# Architectural Lessons: Multi-modal Tool Responses with Gemini Live API

## The Goal
The `visual_pizza_agent` was built to demonstrate an advanced multi-modal agentic flow: taking voice orders via the Gemini Live API, synthesizing the order, and calling an image generation tool (Imagen 3) to show the user a realistic picture of their final pizza.

## Image Generation: "The Right Path" with Imagen 3
Generating images inside an ADK tool is straightforward when using the standard `google.genai` SDK. The ADK integrates seamlessly with the underlying GenAI client. 

Here is the correct approach to generating high-quality images using **Imagen 3**:

### 1. Model Selection & Client Setup
When running on Google Cloud (or locally with Vertex AI credentials), ensure you are using the correct model string for Imagen 3 (`imagen-3.0-generate-002`) and initialize the standard GenAI client.

```python
from google.genai import Client

MODEL_IMAGE = "imagen-3.0-generate-002"

async def generate_pizza_image(description: str, tool_context: "ToolContext"):
    # Automatically picks up Vertex AI credentials if configured in the environment
    client = Client() 
    # ...
```

### 2. Prompt Engineering for Tools
Users talking to a conversational agent usually provide brief descriptions (e.g., "I want a picanha pizza"). If you pass this directly to Imagen, the results can be unpredictable (e.g., it might generate a cartoon, a drawing, or an abstract painting). 

The "right path" for a specialized agent is to **wrap the user's description in a strongly typed stylistic prompt** inside the tool logic itself, completely invisible to the user:

```python
    # Enforce realistic photo style behind the scenes
    full_prompt = (
        f"A realistic high-quality photo of a pizza: {description}. "
        f"Professional food photography, appetizing, detailed crust and toppings."
    )
```

### 3. Executing the Generation Request
Use `client.models.generate_images` to request the image. Always wrap this in a `try/except` block, as image generation APIs can occasionally reject prompts based on safety filters.

```python
    try:
        response = client.models.generate_images(
            model=MODEL_IMAGE,
            prompt=full_prompt,
            config={"number_of_images": 1},
        )
        
        if not response.generated_images:
            return {"status": "failed", "detail": "No images were generated."}
            
        # Extract the raw bytes of the generated PNG
        image_bytes = response.generated_images[0].image.image_bytes
        
        # ... (Proceed to save to GCS, as detailed below)
```

### 4. Required Configuration
Because this uses Vertex AI's Imagen 3, ensure the environment where the agent runs (e.g., your Cloud Run service) has the following environment variables configured:
- `GOOGLE_GENAI_USE_VERTEXAI="1"`
- `GOOGLE_CLOUD_PROJECT="your-project-id"`
- `GOOGLE_CLOUD_LOCATION="us-central1"` (Required, as model availability varies by region)

---

## The Problem: Context Window Limits vs. Binary Data
During implementation, the system successfully called the `generate_pizza_image` tool, but the backend WebSocket connection immediately crashed with the following error:
`1007 None. the provided content is above the context window size 32000.; Error raised from operator assemble_generate_request`

### Why did this happen?
When an ADK tool completes, its return value is serialized into a `FunctionResponse` and sent *back to the LLM* so the agent knows the task succeeded and can formulate its next spoken reply. 
The Imagen 3 model generates beautiful, high-resolution PNG images that are ~1.5MB in size. We were initially encoding this entire 1.5MB binary file as a Base64 text string and returning it inside the tool's JSON response. 

Because Base64 strings are just text, this injected roughly 375,000 text tokens directly into the Gemini Live agent's conversation history. The Gemini Live preview model (`gemini-live-2.5-flash-native-audio`), which is highly optimized for ultra-low latency streaming, currently enforces a strict 32,000 token context window. The massive Base64 string instantly blew out this memory limit.

## The Temporary Fix: Aggressive Compression
To quickly resolve the crash while maintaining the same architecture (returning data directly through the agent), we used the `Pillow` library to aggressively resize and compress the image before returning it.

```python
# visual_pizza_agent/backend/app/tools.py (Temporary Fix)
import base64
import io
from PIL import Image

# ... inside generate_pizza_image ...
image_bytes = response.generated_images[0].image.image_bytes

with Image.open(io.BytesIO(image_bytes)) as img:
    # Resize to 256x256 to stay well under the 32k token limit
    img = img.resize((256, 256), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=60)
    compressed_bytes = output.getvalue()

image_base64 = base64.b64encode(compressed_bytes).decode('utf-8')

return {
    "status": "success",
    "image_base64": image_base64,
    "mime_type": "image/jpeg"
}
```
**Drawback:** This limits the frontend to displaying a low-resolution, highly compressed image.

## The Proper Solution: Decoupling Data from Context (GCS)
The golden rule for LLM tool use is: **Do not force heavy binary data through the agent's context window.**

To support high-resolution images (or large documents, videos, etc.), we must decouple the *data transport* from the *LLM context*. The optimal architecture is to have the tool upload the binary payload to an external storage service (like Google Cloud Storage) and return **only the public URL** to the agent.

### Future Implementation Guide (GCS Approach)

**1. Update the Backend Tool (Python):**
The tool uploads the raw 1.5MB bytes to GCS and returns a short string URL. This consumes practically zero tokens.

```python
import uuid
from google.cloud import storage
from google.adk.tools import ToolContext

async def generate_pizza_image(description: str, tool_context: "ToolContext"):
    # ... call Imagen 3 ...
    image_bytes = response.generated_images[0].image.image_bytes
    
    # Initialize GCS client
    storage_client = storage.Client()
    bucket = storage_client.bucket("your-public-pizza-bucket")
    
    # Generate unique filename and upload
    filename = f"pizza_{uuid.uuid4().hex[:8]}.png"
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type="image/png")
    
    # Return ONLY the URL to the LLM
    public_url = blob.public_url
    
    return {
        "status": "success",
        "detail": "High-res pizza image generated.",
        "image_url": public_url
    }
```

**2. Update the Frontend (Next.js/React):**
The frontend parses the `functionResponse` for the URL instead of base64 data, allowing the browser to load the high-res image directly from GCS.

```typescript
// visual_pizza_agent/frontend/src/app/page.tsx (Future State)
if (part.functionResponse && part.functionResponse.name === 'generate_pizza_image') {
    const response = part.functionResponse.response;
    if (response.status === 'success' && response.image_url) {
       setMessages(prev => [...prev, { 
           role: 'agent', 
           imageUrl: response.image_url 
       }]);
    }
}

// Rendering
{m.imageUrl && (
    <img 
        src={m.imageUrl} 
        alt="Generated Pizza"
        style={{ maxWidth: '100%', borderRadius: '8px' }}
    />
)}
```

This pattern ensures maximum scalability, avoids arbitrary LLM context limits, and provides the best possible user experience.

---

## Deployment: Serving Static Frontends on Cloud Run

When deploying a static frontend (like a Next.js `out` export or a simple HTML/JS site) to Google Cloud Run using Nginx, there are two critical "gotchas" to handle:

### 1. The Port Binding Requirement
Cloud Run requires services to listen on the port defined by the `$PORT` environment variable, which defaults to **8080**. Standard Nginx Docker images are configured to listen on port **80**, which will cause the Cloud Run health check to fail and the deployment to rollback.

**The Solution:** Create a custom `nginx.conf` and explicitly set the listen port to 8080.

```nginx
# visual_pizza_agent/frontend/nginx.conf
server {
    listen 8080;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Important for Single Page Apps (React/Next.js):
    # Force all paths to load index.html so the client-side router can take over.
    location / {
        try_files $uri /index.html;
    }
}
```

### 2. The `.gcloudignore` Pitfall
If you use `gcloud run deploy --source .`, the CLI will automatically ignore common configuration files like `nginx.conf` if they are not explicitly whitelisted.

**The Solution:** Ensure your `nginx.conf` is whitelisted in `.gcloudignore` so it is actually uploaded to the build environment.

```text
# visual_pizza_agent/frontend/.gcloudignore
# ... other ignores ...

!nginx.conf
```

### 3. The Dockerfile Configuration
Finally, update your `Dockerfile` to copy this custom configuration into the correct directory.

```dockerfile
# visual_pizza_agent/frontend/Dockerfile
FROM nginx:stable-alpine

# Copy the static build output
COPY ./out /usr/share/nginx/html

# Copy the custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Inform Cloud Run about the port (optional but good practice)
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
```
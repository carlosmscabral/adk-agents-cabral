import base64
import io
from PIL import Image
from google.adk.tools import ToolContext
from google.genai import Client, types

MODEL_IMAGE = "imagen-3.0-generate-002"

async def generate_pizza_image(description: str, tool_context: "ToolContext"):
    """
    Generates a realistic photo of a pizza based on the description provided.
    
    Args:
        description: A detailed description of the pizza to generate.
        tool_context: The context for the tool execution.
    """
    client = Client()
    
    # Enforce realistic photo style
    full_prompt = f"A realistic high-quality photo of a pizza: {description}. Professional food photography, appetizing, detailed crust and toppings."
    
    print(f"Generating image with prompt: {full_prompt}")
    
    try:
        response = client.models.generate_images(
            model=MODEL_IMAGE,
            prompt=full_prompt,
            config={"number_of_images": 1},
        )
        
        if not response.generated_images:
            return {"status": "failed", "detail": "No images were generated."}
        
        image_bytes = response.generated_images[0].image.image_bytes
        
        # Use Pillow to resize and compress the image
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Resize to 256x256 - should be around 15-20KB JPEG
            img = img.resize((256, 256), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            # Save as JPEG with 60% quality
            img.save(output, format="JPEG", quality=60)
            compressed_bytes = output.getvalue()
        
        # We can either save it as an artifact OR return it as base64.
        # For the Live API demo, sending it as part of the tool response is easy for the frontend to catch.
        image_base64 = base64.b64encode(compressed_bytes).decode('utf-8')
        
        print(f"Image generated! Original: {len(image_bytes)} bytes. Compressed: {len(compressed_bytes)} bytes. Base64 length: {len(image_base64)}")
        
        return {
            "status": "success",
            "detail": "Pizza image generated successfully.",
            "image_base64": image_base64,
            "mime_type": "image/jpeg"
        }
    except Exception as e:
        print(f"Error generating image: {e}")
        return {"status": "error", "detail": str(e)}

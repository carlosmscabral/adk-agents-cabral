import os
import asyncio
from google.adk.models import Gemini
from google.genai import types

os.environ["GOOGLE_CLOUD_PROJECT"] = "vibe-cabral"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

async def main():
    try:
        model = Gemini(model="gemini-3-flash-preview")
        res = await model.generate_content_async(messages=[types.Content(role="user", parts=[types.Part.from_text(text="hi")])])
        print("Success without base_url:", res.text)
    except Exception as e:
        print("Failed without base_url:", e)

    try:
        # What if we just use the global base URL?
        # Actually, the base url usually includes the project and location path in Vertex REST APIs, 
        # but google-genai client uses location inside the URL path:
        # https://{location}-aiplatform.googleapis.com/...
        pass
        
asyncio.run(main())

import base64
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
        
        # We can either save it as an artifact OR return it as base64.
        # For the Live API demo, sending it as part of the tool response is easy for the frontend to catch.
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Also save as artifact just in case
        await tool_context.save_artifact(
            "final_pizza.png",
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
        )
        
        return {
            "status": "success",
            "detail": "Pizza image generated successfully.",
            "image_base64": image_base64,
            "mime_type": "image/png"
        }
    except Exception as e:
        print(f"Error generating image: {e}")
        return {"status": "error", "detail": str(e)}

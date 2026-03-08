import asyncio
import os
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from app.agent import root_agent
from google.genai import types as genai_types

async def main():
    print("--- Starting Pizza Agent Local Test ---")
    
    # 1. Initialize ADK Session Service
    session_service = InMemorySessionService()
    session_id = "test_pizza_session"
    user_id = "test_chef"
    
    # In some ADK versions, you might need to create the session first
    # but InMemorySessionService usually handles it or auto_create_session=True in Runner.
    
    # 2. Create the Runner
    runner = Runner(
        agent=root_agent, 
        app_name="pizza_agent_demo", 
        session_service=session_service,
        auto_create_session=True
    )
    
    query = "Mamma mia! What is the most popular pizzeria in Naples right now in 2026? I must know for my pizza research!"
    print(f"[*] Sending query: '{query}'")
    
    # 3. Run the Agent (using run_async as it returns an async generator of events)
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=genai_types.Content(
                role="user", 
                parts=[genai_types.Part.from_text(text=query)]
            ),
        ):
            # Inspect event structure
            if hasattr(event, 'get_function_calls') and event.get_function_calls():
                print(f"[Agent] Calling tool: {event.get_function_calls()[0].name}")
            
            # Use event.content if it exists
            if hasattr(event, 'content') and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"\n[Agent]: {part.text}")
                        
    except Exception as e:
        print(f"Error during agent run: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ensure environment variables are set (using mock project/location for local test)
    if "GOOGLE_CLOUD_PROJECT" not in os.environ:
        os.environ["GOOGLE_CLOUD_PROJECT"] = "mock-project"
    if "GOOGLE_CLOUD_LOCATION" not in os.environ:
        os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
    
    asyncio.run(main())
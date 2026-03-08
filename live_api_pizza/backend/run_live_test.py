import asyncio
import os
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from app.agent import root_agent
from google.genai import types as genai_types
from google.adk.agents.live_request_queue import LiveRequestQueue

async def main():
    print("--- Starting Pizza Agent Live Test ---")
    
    session_service = InMemorySessionService()
    session_id = "test_pizza_session"
    user_id = "test_chef"
    
    session = await session_service.create_session(
        app_name="app", user_id=user_id, session_id=session_id
    )
    
    runner = Runner(
        agent=root_agent, 
        app_name="app", 
        session_service=session_service,
        auto_create_session=True
    )
    
    live_request_queue = LiveRequestQueue()
    
    # Send a text message to trigger an audio response
    live_request_queue.send_content(genai_types.Content(
        role="user",
        parts=[genai_types.Part.from_text(text="Mamma mia! Tell me a quick joke about pizza!")]
    ))
    
    # We must close the queue so the generator terminates eventually
    # Or just listen for a bit
    
    try:
        from google.adk.runners import RunConfig
        run_config = RunConfig(
            response_modalities=["AUDIO", "TEXT"]
        )
        import contextlib
        
        @contextlib.asynccontextmanager
        async def Aclosing(thing):
            try:
                yield thing
            finally:
                await thing.aclose()
                
        async with Aclosing(
            runner.run_live(
                session=session,
                live_request_queue=live_request_queue,
                run_config=run_config
            )
        ) as agen:
            async for event in agen:
                print(f"Received event: id={event.id}")
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(f"[Text]: {part.text}")
                        if part.inline_data:
                            print(f"[Audio]: Received {len(part.inline_data.data)} bytes of {part.inline_data.mime_type}")
                if event.is_final_response():
                    print("Final response received. Closing queue.")
                    live_request_queue.close()
                    break
                        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
    os.environ["GOOGLE_CLOUD_PROJECT"] = "vibe-cabral"
    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
    asyncio.run(main())
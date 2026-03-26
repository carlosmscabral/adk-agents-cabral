import asyncio
import os
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from app.agent import root_agent

async def test_da():
    session_service = InMemorySessionService()
    app_name = "app"
    user_id = "test_user"
    session_id = "test_session"
    
    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    runner = Runner(agent=root_agent, app_name=app_name, session_service=session_service)
    
    query = "Ask the agent-legal to show me the error rates of the API calls for today."
    print(f"USER: {query}")
    
    content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
    
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            print(f"AGENT: {event.content.parts[0].text}")

if __name__ == "__main__":
    asyncio.run(test_da())

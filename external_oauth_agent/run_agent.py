import asyncio
import os
import jwt
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from app.agent import root_agent
from google.genai import types as genai_types

# Set a mock AUTH_ID to match the agent's expectation
os.environ["AUTH_ID"] = "my-adk-agent-auth"

# This secret matches the one in our mock API
MOCK_JWT_SECRET = "super-secret-key"

def create_mock_token(email="test@example.com"):
    """Creates a simple mock JWT token."""
    payload = {
        "sub": "1234567890",
        "name": "Test User",
        "email": email,
        "iss": "mock_issuer",
        "iat": 1516239022
    }
    return jwt.encode(payload, MOCK_JWT_SECRET, algorithm="HS256")

async def main():
    print("--- Starting ADK Agent Local Test ---")
    
    # 1. Initialize ADK Session Service
    session_service = InMemorySessionService()
    session_id = "test_session_001"
    user_id = "test_user"
    
    await session_service.create_session(
        app_name="external_oauth_demo", user_id=user_id, session_id=session_id
    )
    
    # 2. Simulate Gemini Enterprise injecting the OAuth token
    # In production, Gemini Enterprise does this automatically before calling the agent.
    mock_token = create_mock_token()
    token_key = f"temp:{os.environ['AUTH_ID']}"
    
    # We retrieve the session to manually inject the state
    session = await session_service.get_session(session_id=session_id)
    session.state[token_key] = mock_token
    await session_service.update_session(session)
    
    print(f"[*] Injected mock token into session state under key: {token_key}")

    # 3. Create the Runner
    runner = Runner(
        agent=root_agent, app_name="external_oauth_demo", session_service=session_service
    )
    
    query = "Please fetch my financial data."
    print(f"[*] Sending query: '{query}'")
    
    # 4. Run the Agent
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=genai_types.Content(
            role="user", 
            parts=[genai_types.Part.from_text(text=query)]
        ),
    ):
        if event.get_function_calls():
            print(f"[Agent] Calling tool: {event.get_function_calls()[0].name}")
        elif event.is_final_response():
            print("
--- Final Agent Response ---")
            print(event.content.parts[0].text)
            print("----------------------------
")

if __name__ == "__main__":
    print("NOTE: Ensure the mock API (app/api.py) is running on port 8000 before executing this script.")
    asyncio.run(main())

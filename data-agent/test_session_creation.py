import os
import asyncio
from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService

async def main():
    service = VertexAiSessionService(
        project="vibe-cabral",
        location="us-central1",
        agent_engine_id="projects/280799742875/locations/us-central1/reasoningEngines/8498794423906205696"
    )
    try:
        session = await service.create_session(
            app_name="app",
            user_id="test-user"
        )
        print("Session created:", session.id)
    except Exception as e:
        print("Failed to create session:", e)

asyncio.run(main())

import asyncio
import logging
import os
import warnings
from contextlib import asynccontextmanager

os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

app = FastAPI(title="Pizza Agent Backend")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_service = InMemorySessionService()
runner = Runner(app_name="pizza_agent", agent=root_agent, session_service=session_service)

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: {user_id}/{session_id}")

    # Ensure model location is correctly handled for preview models
    if "native-audio" in root_agent.model:
        response_modalities = ["AUDIO"]
    else:
        response_modalities = ["TEXT"]

    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=response_modalities,
        input_audio_transcription=types.AudioTranscriptionConfig() if response_modalities == ["AUDIO"] else None,
        output_audio_transcription=types.AudioTranscriptionConfig() if response_modalities == ["AUDIO"] else None,
        session_resumption=types.SessionResumptionConfig(),
    )

    # Initialize session
    session = await session_service.get_session(
        app_name="pizza_agent", user_id=user_id, session_id=session_id
    )
    if not session:
        await session_service.create_session(
            app_name="pizza_agent", user_id=user_id, session_id=session_id
        )

    live_request_queue = LiveRequestQueue()

    async def upstream_task():
        try:
            while True:
                message = await websocket.receive()
                if "bytes" in message:
                    audio_data = message["bytes"]
                    audio_blob = types.Blob(mime_type="audio/pcm;rate=16000", data=audio_data)
                    live_request_queue.send_realtime(audio_blob)
                elif "text" in message:
                    text_data = message["text"]
                    import json
                    try:
                        json_msg = json.loads(text_data)
                        if "type" in json_msg and json_msg["type"] == "text":
                            content = types.Content(parts=[types.Part(text=json_msg["text"])])
                            live_request_queue.send_content(content)
                    except Exception as e:
                        logger.error(f"Error parsing text message: {e}")
        except WebSocketDisconnect:
            pass

    async def downstream_task():
        try:
            async for event in runner.run_live(
                user_id=user_id,
                session_id=session_id,
                live_request_queue=live_request_queue,
                run_config=run_config,
            ):
                event_json = event.model_dump_json(exclude_none=True, by_alias=True)
                await websocket.send_text(event_json)
        except Exception as e:
            logger.error(f"Error in downstream task: {e}")

    try:
        await asyncio.gather(upstream_task(), downstream_task())
    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"Error in websocket loop: {e}")
    finally:
        live_request_queue.close()

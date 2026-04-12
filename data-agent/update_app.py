import os

with open('app/agent_engine_app.py', 'r') as f:
    content = f.read()

content = content.replace(
    'from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService\nfrom google.cloud import logging as google_cloud_logging',
    'from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService\nfrom google.adk.sessions.vertex_ai_session_service import VertexAiSessionService\nfrom google.cloud import logging as google_cloud_logging'
)

content = content.replace(
    'agent_engine = AgentEngineApp(\n    app=adk_app,\n    artifact_service_builder=',
    'agent_engine = AgentEngineApp(\n    app=adk_app,\n    session_service_builder=lambda: VertexAiSessionService(\n        project=os.environ.get("GOOGLE_CLOUD_PROJECT", "vibe-cabral"),\n        location="us-central1",\n        agent_engine_id=os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")\n    ),\n    artifact_service_builder='
)

with open('app/agent_engine_app.py', 'w') as f:
    f.write(content)

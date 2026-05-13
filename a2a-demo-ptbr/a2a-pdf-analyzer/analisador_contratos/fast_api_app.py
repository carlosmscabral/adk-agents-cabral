# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import google.auth
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentExtension
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from fastapi import FastAPI
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from analisador_contratos.agent import app as adk_app

_, project_id = google.auth.default()

# Artifact bucket for ADK
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
artifact_service = (
    GcsArtifactService(bucket_name=logs_bucket_name)
    if logs_bucket_name
    else InMemoryArtifactService()
)

runner = Runner(
    app=adk_app,
    artifact_service=artifact_service,
    session_service=InMemorySessionService(),
)

request_handler = DefaultRequestHandler(
    agent_executor=A2aAgentExecutor(runner=runner),
    task_store=InMemoryTaskStore(),
)

app = FastAPI(title="analisador_contratos")

def setup_a2a(fastapi_app: FastAPI):
    # A URL estável que queremos no card
    app_url = os.getenv('APP_URL', 'https://a2a-pdf-analyzer-280799742875.us-east1.run.app')
    
    agent_card = AgentCard(
        name="analisador_contratos",
        description="Análise jurídica de contratos.",
        protocolVersion="0.3.0",
        version="0.1.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        url=app_url,
        preferredTransport="JSONRPC",
        capabilities=AgentCapabilities(streaming=False),
        skills=[{"description": "Análise de contratos", "id": "analisador_contratos", "name": "model", "tags": ["llm"]}]
    )

    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)
    # Registra o Card e o RPC na RAIZ
    a2a_app.add_routes_to_app(
        fastapi_app,
        agent_card_url=AGENT_CARD_WELL_KNOWN_PATH,
        rpc_url="/",
    )

setup_a2a(app)

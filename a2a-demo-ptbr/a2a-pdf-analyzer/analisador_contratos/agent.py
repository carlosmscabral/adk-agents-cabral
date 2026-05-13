import uuid
import os
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.tools.load_artifacts_tool import LoadArtifactsTool
from google.adk.tools import ToolContext
from google.genai import types

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


root_agent = Agent(
    name="analisador_contratos",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Um agente especializado em analisar contratos e documentos legais em Português-BR.",
    instruction="""Você é um especialista jurídico brasileiro. 
Sua tarefa é analisar contratos fornecidos pelo usuário.
Quando receber uma referência a um arquivo (ex: 'user:contrato_XYZ.pdf'), você DEVE usar a ferramenta 'load_artifacts' para ler o conteúdo antes de responder.
Analise cláusulas, identifique riscos e resuma os pontos principais, sempre em Português-BR.
""",
    tools=[
        LoadArtifactsTool(),
    ],
)

app = App(
    root_agent=root_agent,
    name="analisador_contratos",
)

import uuid
import os
import google.auth
import re
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.tools import ToolContext
from google.adk.a2a.converters.part_converter import convert_genai_part_to_a2a_part
from google.genai import types
from a2a.types import AgentCard

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# URL Estável do Analisador no Cloud Run
ANALYZER_URL = os.environ.get("ANALYZER_AGENT_URL", "https://a2a-pdf-analyzer-YOUR_PROJECT_NUMBER.YOUR_REGION.run.app")

def skip_heavy_parts_converter(part: types.Part) -> list:
    """Remove bytes de PDF do payload A2A para evitar erros de limite."""
    if part.inline_data and "pdf" in (part.inline_data.mime_type or "").lower():
        print(f"DEBUG A2A: Removendo bytes de PDF.")
        return []
    return convert_genai_part_to_a2a_part(part)

def salvar_contrato(tool_context: ToolContext) -> str:
    """Identifica o contrato PDF indexado pelo Gemini Enterprise."""
    print(f"DEBUG: Identificando contrato nos eventos.")
    filename = None
    for event in reversed(tool_context.session.events):
        if event.author == "user":
            for part in event.content.parts:
                if part.text:
                    # Regex para capturar nome do arquivo nas tags do GE App
                    match = re.search(r"start_of_user_uploaded_file:\s*([^\s\n>]+)", part.text)
                    if match:
                        filename = match.group(1).strip()
                        break
            if filename: break
    if not filename:
        filename = "contrato_identificado.pdf"
    return f"Contrato '{filename}' identificado. Iniciando análise com o especialista."

# Metadata FIXA validada via curl
ANALYZER_CARD = AgentCard(**{
  "name": "analisador_contratos",
  "description": "Análise jurídica de contratos.",
  "protocolVersion": "0.3.0",
  "version": "0.1.0",
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain"],
  "url": ANALYZER_URL, # Aponta para a raiz /
  "preferredTransport": "JSONRPC", # OBRIGATÓRIO: Único modo que funcionou no Cloud Run
  "skills": [{"id": "analisador_contratos", "name": "model", "tags": ["llm"], "description": "Análise jurídica de contratos."}],
  "capabilities": {"streaming": False}
})

analisador_contratos = RemoteA2aAgent(
    name="analisador_contratos",
    description="Agente remoto especializado em análise de contratos.",
    agent_card=ANALYZER_CARD,
    genai_part_converter=skip_heavy_parts_converter,
    use_legacy=False,
)

root_agent = Agent(
    name="recepcionista_contratos",
    model=Gemini(model="gemini-flash-latest", retry_options=types.HttpRetryOptions(attempts=3)),
    description="Agente de recepção especializado em contratos.",
    instruction="""Você é um recepcionista brasileiro de um escritório de advocacia.
Sua tarefa:
1. Quando o usuário enviar um arquivo, chame 'salvar_contrato'.
2. Com o nome do arquivo, chame o 'analisador_contratos' para a análise.
3. Responda sempre em Português-BR.""",
    sub_agents=[analisador_contratos],
    tools=[salvar_contrato],
)

app = App(root_agent=root_agent, name="app")

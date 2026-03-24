import os
from google.adk.agents.llm_agent import LlmAgent
from .tools import connector_tool

# Because Vertex AI Agent Engine forcibly overwrites the GOOGLE_CLOUD_LOCATION environment variable 
# to match its compute region (which can cause 404 errors for models only available in the 'global' region),
# we include this override to ensure we hit the global model endpoint as defined in our .env
if "MODEL_LOCATION" in os.environ:
    os.environ["GOOGLE_CLOUD_LOCATION"] = os.environ["MODEL_LOCATION"]

root_agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="jira_assistant",
    instruction="""
    You are a helpful Jira assistant. 
    You have access to a Jira Integration Connector tool. 
    You can use it to list, get, or create issues in Jira for the user.
    When a user asks about Jira issues, always use your tools to fetch real-time information.
    """,
    tools=[connector_tool],
)

from google.adk.apps import App

app = App(root_agent=root_agent, name="app")

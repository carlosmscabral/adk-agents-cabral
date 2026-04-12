# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import google.auth
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from google.adk.tools.data_agent.config import DataAgentToolConfig
from google.adk.tools.data_agent.credentials import DataAgentCredentialsConfig
from google.adk.tools.data_agent.data_agent_toolset import DataAgentToolset

# Load environment variables
load_dotenv()

# Setup Vertex AI and standard project context
# We use ADC and the default project/location provided by Agent Engine (us-central1)
# O override de localização (global) acontece apenas no agent_engine_app.py
# para não quebrar a inicialização das sessões no Gemini Enterprise.
_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Data Agent Configuration
DATA_AGENT_PROJECT_ID = os.environ.get("DATA_AGENT_PROJECT_ID", "cabral-apigee")
DATA_AGENT_ID = os.environ.get("DATA_AGENT_ID", "agent_6a22b27c-5d07-4c7b-86c7-9e66e0538be3")
DATA_AGENT_LOCATION = os.environ.get("DATA_AGENT_LOCATION", "us-central1")

# Use ADC for Data Agent interactions
application_default_credentials, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Mandatory refresh for DataAgentToolset
import google.auth.transport.requests
auth_request = google.auth.transport.requests.Request()
application_default_credentials.refresh(auth_request)

credentials_config = DataAgentCredentialsConfig(
    credentials=application_default_credentials
)

tool_config = DataAgentToolConfig(
    max_query_result_rows=100,
)

# Instantiate Data Agent toolset
da_toolset = DataAgentToolset(
    credentials_config=credentials_config,
    data_agent_tool_config=tool_config,
    tool_filter=[
        "list_accessible_data_agents",
        "get_data_agent_info",
        "ask_data_agent",
    ],
)

# Root Agent Definition
root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are a sophisticated AI assistant capable of performing deep data analysis "
        "using Google Cloud Data Agents.\n\n"
        "## Data Analysis Guidelines\n"
        "When a user asks questions related to API calls, usage patterns, or complex datasets, "
        "use the `ask_data_agent` tool. The targeted data agent is located at:\n"
        f"projects/{DATA_AGENT_PROJECT_ID}/locations/{DATA_AGENT_LOCATION}/dataAgents/{DATA_AGENT_ID}\n\n"
        "Always use the `ask_data_agent` tool if the query involves data that seems related to "
        "API analytics or usage metrics. If you are unsure which agents are available, use `list_accessible_data_agents`."
    ),
    tools=[da_toolset],
)

app = App(
    root_agent=root_agent,
    name="app",
)

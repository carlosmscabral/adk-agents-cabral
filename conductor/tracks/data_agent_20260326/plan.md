# Plan: Cross-Project ADK Data Agent

## Objective
Build a new ADK Agent named `data_agent` that invokes a remote Data Agent (Conversational Analytics BigQuery feature) located in a different Google Cloud project. 
The agent will be developed as a prototype and deployed to **Agent Engine** in the project `vibe-cabral`. The remote Data Agent is in `cabral-apigee`, named `agent-legal` (ID: `agent_6a22b27c-5d07-4c7b-86c7-9e66e0538be3`). Finally, the ADK Agent will be registered with a **Gemini Enterprise app**.

## Key Files & Context
- **Workspace:** `/Users/carloscabral/_demos/adk-agents-cabral/`
- **New Project Directory:** `data_agent/`
- **Configuration File:** `.env` for dynamically loading project configurations.
- **Scaffolding Tool:** ADK Agent Starter Pack (`uvx agent-starter-pack`)

## Considerations & Prerequisites

### 1. Agent Engine Identity & Service Account
When using `agent-starter-pack` (ASP), a custom service account named `app_sa` is typically created in the deployment project (`vibe-cabral`).
- **Runtime Identity:** The agent runs as `app_sa@{DEPLOYMENT_PROJECT_ID}.iam.gserviceaccount.com`.
- **Default Fallback:** If no custom service account is provided, Agent Engine uses the **AI Platform Reasoning Engine Service Agent**: `service-{PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com`.
- **Recommendation:** Use the ASP-created `app_sa` for granular control.

### 2. Cross-Project IAM Setup
The chosen identity (`app_sa` or the Service Agent) must be granted the following roles in the **Data Agent project** (`cabral-apigee`):
- `roles/geminidataanalytics.dataAgentUser`: To chat with the Data Agent.
- `roles/bigquery.dataViewer`: To read the data.
- `roles/bigquery.user`: To run BigQuery jobs.
- `roles/cloudaicompanion.user`: For underlying Gemini features.

### 3. Data Agent Region Discovery
Data Agents currently have limited regionalization support. To find the correct region for the resource path:
1. Use the `list_accessible_data_agents` tool (provided by `DataAgentToolset`) during local development.
2. Observe the resource name format returned: `projects/cabral-apigee/locations/{LOCATION}/dataAgents/agent_6a22b27c...`.
3. Common locations are `us-central1` or `global`.

### 4. Gemini Enterprise Registration
To make the ADK Agent available in the Gemini Enterprise web app:
1. Ensure the **Discovery Engine API** is enabled in `vibe-cabral`.
2. Ensure you have the **Discovery Engine Admin** role.
3. In the Google Cloud Console, go to **Gemini Enterprise** -> Select your **App** -> **Agents** -> **Add agent**.
4. Choose **Custom agent via Agent Engine**.
5. Provide the **Reasoning Engine resource path**: `https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ADK_RESOURCE_ID}`.

## Implementation Steps

### Step 1: Scaffolding the ADK Project
Run the Agent Starter Pack in Prototype mode:
```bash
uvx agent-starter-pack create data_agent \
  --agent adk \
  --deployment-target agent_engine \
  --prototype \
  -y
```

### Step 2: Environment Configuration
Create a `.env` file (and `.env.template`):
```env
DEPLOYMENT_PROJECT_ID=vibe-cabral
DATA_AGENT_PROJECT_ID=cabral-apigee
DATA_AGENT_ID=agent_6a22b27c-5d07-4c7b-86c7-9e66e0538be3
DATA_AGENT_LOCATION=us-central1  # Update after discovery
```

### Step 3: Agent Code Implementation (`data_agent/app/agent.py`)
1. Use `DataAgentToolset` to wrap the Conversational Analytics API.
2. Define the agent instruction to use `ask_data_agent` with the remote agent's resource name.
3. Ensure tools are imported correctly from `google.adk.tools.data_agent`.

### Step 4: Local Verification & Region Discovery
1. Run `make playground` locally.
2. Use the "List agents" query to confirm access and identify the exact region of `agent-legal`.
3. Update `.env` with the correct location.

### Step 5: Agent Engine Deployment
1. Run `uv run -m app.app_utils.deploy`.
2. Capture the `remote_agent_engine_id` from `deployment_metadata.json`.

### Step 6: Gemini Enterprise Registration
1. Follow the registration steps in the Cloud Console.
2. Test the agent within the Gemini Enterprise web app.

## Verification & Testing
1. **Local:** `adk web .` -> Query "Who is the owner of the legal data agent?".
2. **Deployed:** Verify `app_sa` has correct cross-project permissions.
3. **Gemini Enterprise:** Confirm the agent appears in the UI and can answer data-related questions.

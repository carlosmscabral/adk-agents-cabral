# ADK Cross-Project Data Agent: API Analytics Demo

This project demonstrates how to build an ADK Agent that invokes a **remote Data Agent** (Conversational Analytics BigQuery feature) located in a different Google Cloud project.

## 🚀 Architecture Overview

- **Deployment Project (`vibe-cabral`):** Hosts the Vertex AI Agent Engine where this ADK agent runs.
- **Data Project (`cabral-apigee`):** Hosts the BigQuery Data Agent (`agent-legal`) and the underlying analytics data.
- **Identity:** The agent runs using the **Reasoning Engine Service Agent** of the deployment project.
- **Integration:** Uses the `google.adk.tools.data_agent.DataAgentToolset` to bridge natural language queries to BigQuery results.

---

## 🛠 Prerequisites & Setup

### 1. Cross-Project IAM (The #1 Gotcha)
The Reasoning Engine does **not** use your personal credentials. In cross-project scenarios using the `DataAgentToolset` (which uses raw REST), it is **highly recommended to use the standard Reasoning Engine Service Agent** instead of the newer Agent Identity for better compatibility.

**Principal:** `service-{DEPLOYMENT_PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com`

**Roles on Data Project (`cabral-apigee`):**
- `roles/geminidataanalytics.dataAgentStatelessUser`: **Mandatory** for executing queries (the "chat" part).
- `roles/bigquery.metadataViewer`: **Mandatory** for the agent to understand the BQ table schemas.
- `roles/bigquery.jobUser`: **Mandatory** at the project level to run the generated SQL jobs.
- `roles/serviceusage.serviceUsageConsumer`: Required to "consume" APIs in the target project.
- `roles/cloudaicompanion.user`: Recommended for underlying Gemini features.

**Roles on Deployment Project (`vibe-cabral`):**
- `roles/cloudtrace.agent`: Recommended to avoid "Permission Denied" noise in logs when the agent attempts to export spans.

### 2. Enable APIs
Enable these APIs in **both** projects:
- `aiplatform.googleapis.com`
- `geminidataanalytics.googleapis.com` (Conversational Analytics)
- `discoveryengine.googleapis.com` (For Gemini Enterprise registration)

---

## 💡 Technical Implementation Details

### Scoped Credentials & Mandatory Refresh (Critical!)
The `DataAgentToolset` uses the `requests` library for REST calls. In Agent Engine, `google.auth.default()` returns a credentials object where the `.token` attribute is **empty** by default. You MUST refresh it manually to populate the token before the toolset uses it:

```python
# app/agent.py
application_default_credentials, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Mandatory refresh: populated credentials.token is required by DataAgentToolset
import google.auth.transport.requests
auth_request = google.auth.transport.requests.Request()
application_default_credentials.refresh(auth_request)

credentials_config = DataAgentCredentialsConfig(
    credentials=application_default_credentials
)
```

### Data Agent Toolset Configuration
The `DataAgentToolset` is instantiated and passed directly to the `Agent`. 

```python
da_toolset = DataAgentToolset(
    credentials_config=credentials_config,
    data_agent_tool_config=DataAgentToolConfig(max_query_result_rows=100),
    tool_filter=["list_accessible_data_agents", "get_data_agent_info", "ask_data_agent"]
)
```

---

## ⚠️ Gotchas & Lessons Learned

### 1. The "REST vs Client Library" Auth Gap
Standard Google Cloud Python clients handle token refreshing automatically. However, tools that use raw REST (like ADK's `DataAgentToolset`) require the token to be explicitly present in the credentials object. Without the manual `refresh()`, you will get 401/403 errors even if IAM is correct.

### 2. Agent Identity vs. Service Agent
While `AGENT_IDENTITY` is a great security feature, some backend APIs (including Conversational Analytics cross-project calls via REST) may still be more stable when using the project's standard Service Agent. If you face persistent 401s with `principal://`, try falling back to the `service-{PROJECT}@gcp-sa-aiplatform-re` identity.

### 3. Model Location vs. API Location
- **Model:** `gemini-3-flash-preview` often requires the `global` location in Agent Engine to resolve correctly.
- **Data Agent:** Discovery can happen in `global`, but the actual execution usually targets regional data agents.
- **Solution:** Set `os.environ["GOOGLE_CLOUD_LOCATION"] = "global"` for the model, but provide specific regional paths for the data agents in your instructions.

### 4. Dependencies
The `DataAgentToolset` requires `google-adk>=1.23.0`.
- Bumping `google-adk` often requires bumping `google-cloud-aiplatform` (e.g., `1.132.0`) to avoid version conflicts in the `uv` lockfile.

---

## 🛠 Development Commands

- **Install:** `make install` (uses `uv`)
- **Local Test:** `uv run test_data_agent.py` (Verify auth and tool calling before deploying)
- **Playground:** `make playground` (Interactive UI)
- **Deploy:** `make deploy` (Pushes to Vertex AI Agent Engine)
- **Register:** `make register-gemini-enterprise` (Links the Agent Engine instance to Gemini Enterprise)

---

## 📝 Gemini Enterprise Registration
To register manually or via CLI, you need the **Reasoning Engine resource path**:
`https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ID}`

Example CLI command:
```bash
agents-cli register-gemini-enterprise \
  --gemini-enterprise-app-id "projects/{PROJECT}/locations/global/collections/default_collection/engines/{APP_ID}" \
  --display-name "API Data Agent"
```

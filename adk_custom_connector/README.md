# Jira Custom Connector Agent

A sample Google ADK Python agent that demonstrates how to seamlessly integrate with Jira using the `ApplicationIntegrationToolset` (Google Integration Connectors).

## Overview

This demo creates an agent capable of interacting with Jira (e.g., listing, reading, and creating issues) by securely leveraging a pre-configured Google Integration Connector connection.

- **Connection**: `jira-carlosmscabral`
- **Location**: `us-central1`
- **Project**: `vibe-cabral`

## Setup

1. Copy `.env.template` to `.env`. The template already contains the required variable names for telemetry and model location.
   ```bash
   cp .env.template .env
   ```

2. Sync dependencies using `uv`:
   ```bash
   uv sync
   ```

## Running Locally

Ensure you have Google Cloud Default Credentials configured:
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project vibe-cabral
```

Run the agent in CLI mode:
```bash
uv run run_agent.py
```
Or interact via the ADK web UI:
```bash
uv run adk web
```

## Deployment

This project uses the scaffolding provided by `agent-starter-pack`. To deploy this agent to Vertex AI Agent Engine with full OpenTelemetry tracing enabled:

```bash
make deploy
```

### Required IAM Roles
When deployed to Agent Engine, the application runs under the default Reasoning Engine service account (`service-{PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com`). 

To successfully initialize the `ApplicationIntegrationToolset` and execute actions against the Jira connection, ensure this service account has the following roles:
- `roles/connectors.viewer` (To read the connection metadata/schema during startup)
- `roles/connectors.invoker` (To execute actions/operations on the connector)
- `roles/integrations.integrationEditor` (To fetch the connection details)

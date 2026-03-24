# Implementation Plan: Jira Custom Connector Agent

## Context
This plan covers the end-to-end setup and implementation of the `adk_custom_connector` demo agent, complying with the repository's ADK product guidelines.

## Steps

### Phase 1: Project Scaffolding
- [ ] **Create Directory Structure:** Create the `adk_custom_connector/` directory at the project root with the following subdirectories and files:
  - `app/__init__.py`
  - `app/agent.py`
  - `app/tools.py`
  - `run_agent.py`
  - `pyproject.toml`
  - `requirements.txt`
  - `.env.template`
  - `Dockerfile` (Optional/standard demo containerization)
  - `README.md`

### Phase 2: Configuration & Dependencies
- [ ] **Setup `pyproject.toml`**: Initialize with `uv` configuration, ensuring `[tool.uv] package = false` and including necessary ADK dependencies (`google-adk`).
- [ ] **Setup `requirements.txt`**: Add core OpenTelemetry dependencies required for Vertex AI Agent Engine deployments:
  - `opentelemetry-api`
  - `opentelemetry-sdk`
  - `opentelemetry-exporter-gcp-logging>=1.6.0`
  - `opentelemetry-exporter-gcp-monitoring>=1.7.0`
  - `opentelemetry-exporter-otlp-proto-grpc>=1.26.0`
  - `opentelemetry-instrumentation`
  - `opentelemetry-instrumentation-google-genai>=0.4b0`
  - `opentelemetry-instrumentation-vertexai>=2.0b0`
- [ ] **Setup `.env.template`**: Add placeholders for OTEL and Model config:
  - `MODEL_LOCATION=global`
  - `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`
  - `OTEL_SERVICE_NAME="adk_custom_connector"`
  - `OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true`
  - `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`
  - `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=true`

### Phase 3: Agent Implementation
- [ ] **Implement `app/tools.py`**:
  - Import `ApplicationIntegrationToolset`.
  - Instantiate `connector_tool` configured for Jira:
    - `project="vibe-cabral"`
    - `location="us-central1"`
    - `connection="jira-carlosmscabral"`
    - `entity_operations={"Issue": []}` (or similar, based on mock needs).
    - `tool_name_prefix="jira_"`
    - Add educational docstrings.
- [ ] **Implement `app/agent.py`**:
  - Add the mandatory `MODEL_LOCATION` to `GOOGLE_CLOUD_LOCATION` environment variable override at the top.
  - Define `LlmAgent` using a standard model (`gemini-3.1-flash-preview`).
  - Attach the `connector_tool` to the agent.
  - Expose `root_agent`.
- [ ] **Implement `run_agent.py`**:
  - Setup simple execution via CLI using standard ADK patterns or directly calling `agent.run()`.
- [ ] **Implement `app/__init__.py`**:
  - Expose the agent.

### Phase 4: Validation & Review
- [ ] **Test Dependencies**: Run `uv sync` to ensure dependencies resolve.
- [ ] **Execution Test**: Verify the agent starts without errors (using mock credentials or `adk web`).
- [ ] **Documentation**: Finalize the local `README.md` with instructions on how to use `adk run` and deploy to Agent Engine using the `--trace_to_cloud` flag.

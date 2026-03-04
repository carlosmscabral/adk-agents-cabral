# Product Guidelines

These guidelines ensure all Google ADK Python demo agents within this repository remain consistent, educational, and deployment-ready.

## 1. Code Style & Documentation (Educational Focus)
- **Highly Descriptive:** Code must prioritize educational value over brevity. Use extensive inline comments to explain complex ADK concepts (e.g., event loops, context injection, state management).
- **Docstrings:** All functions, classes, and tools must have comprehensive docstrings explaining their purpose, arguments, and expected return types, specifically catering to developers learning the SDK.

## 2. Project Structure
- **Modular (Separated):** Each demo agent will reside in its own isolated folder.
- **Standard Layout:** Enforce a clean separation of concerns within each folder (e.g., `agent.py` for orchestration, `tools.py` for tool definitions, `__init__.py` for packaging).
- **Environment Variables:** Because actual `.env` files are ignored by git (to protect secrets), **every project must include an `.env.template` file**. This template must contain all required environment variable keys (with placeholder values) and must be committed to the repository to serve as a structural reference for users.
- **Strict Service Isolation:** If a demo includes supplementary services alongside the ADK agent (e.g., a mock REST API or a frontend UI), they must be strictly isolated. Each service must have its own dedicated subdirectory, dependency manifest (e.g., `requirements.txt`), and deployment configuration (e.g., `Dockerfile`). Never mix agent SDK dependencies with supplementary service dependencies to prevent bloated or insecure container images.

## 3. Error Handling & Resilience
- **Fail-fast (Debuggable):** Demos should not silently swallow errors. Allow exceptions (like tool failures or API errors) to surface immediately so developers can inspect tracebacks and understand failure modes.

## 4. Output UX & Deployment Readiness
- **Omni-Surface Compatibility:** Every agent must be designed to run seamlessly across all ADK surfaces.
- **Web UI & CLI:** Code must support execution via standard console output, rich CLI (e.g., `adk run`), and the interactive web interface (`adk web`).
- **Cloud Deployment:** Agents must be structurally compatible for immediate deployment to both Google Vertex AI Agent Engine and Google Cloud Run using the `adk deploy` CLI commands.
- **Agent Engine Model Location Override:** Because Vertex AI Agent Engine forcibly overwrites the `GOOGLE_CLOUD_LOCATION` environment variable to match its compute region (causing 404 errors for models only available in `global`), **all `agent.py` files must include the following override at the very top of the file:**
  ```python
  import os
  if "MODEL_LOCATION" in os.environ:
      os.environ["GOOGLE_CLOUD_LOCATION"] = os.environ["MODEL_LOCATION"]
  ```
  Additionally, all `.env.template` files must include `MODEL_LOCATION=global`.
- **Explicit Agent Naming:** When documenting or scripting deployments to Vertex AI Agent Engine (`adk deploy agent_engine`), you **must always include the `--display_name` flag** with a descriptive name specific to the demo (e.g., `--display_name "My Specific Demo Agent"`). Do not allow deployments to default to generic names like "app".
- **Telemetry & Observability:** All Agent Engine deployments must enable OpenTelemetry by default to capture full prompt and response payloads in Google Cloud Trace/Logging. To achieve this, you must follow this strict, proven configuration:
  1. **Deployment Command:** Append the `--trace_to_cloud` and explicitly pass `--env_file=.env` to the `adk deploy agent_engine` command.
  2. **Environment Variables:** The `.env.template` must explicitly define the complete suite of OTEL variables:
     ```env
     GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
     OTEL_SERVICE_NAME="<agent_name>"
     OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
     OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
     ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=true
     ```
  3. **Dependencies:** The deployment `requirements.txt` MUST explicitly include the core OTEL API, the GCP exporters, and the specific instrumentations for GenAI and Vertex AI. Do not rely on the base ADK package to install these:
     - `opentelemetry-api`
     - `opentelemetry-sdk`
     - `opentelemetry-exporter-gcp-logging>=1.6.0`
     - `opentelemetry-exporter-gcp-monitoring>=1.7.0`
     - `opentelemetry-exporter-otlp-proto-grpc>=1.26.0`
     - `opentelemetry-instrumentation`
     - `opentelemetry-instrumentation-google-genai>=0.4b0`
     - `opentelemetry-instrumentation-vertexai>=2.0b0`

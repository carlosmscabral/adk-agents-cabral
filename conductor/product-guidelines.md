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
- **Explicit Agent Naming:** When documenting or scripting deployments to Vertex AI Agent Engine (`adk deploy agent_engine`), you **must always include the `--display_name` flag** with a descriptive name specific to the demo (e.g., `--display_name "My Specific Demo Agent"`). Do not allow deployments to default to generic names like "app".
- **Telemetry & Observability:** All Agent Engine deployments must enable OpenTelemetry by default. This is done by appending the `--otel_to_cloud` flag to the `adk deploy agent_engine` command (which automatically sets `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` in the runtime). Additionally, the `.env` template should explicitly include `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` to ensure full prompt/response logging is captured in Cloud Logging.

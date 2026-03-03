# Product Guidelines

These guidelines ensure all Google ADK Python demo agents within this repository remain consistent, educational, and deployment-ready.

## 1. Code Style & Documentation (Educational Focus)
- **Highly Descriptive:** Code must prioritize educational value over brevity. Use extensive inline comments to explain complex ADK concepts (e.g., event loops, context injection, state management).
- **Docstrings:** All functions, classes, and tools must have comprehensive docstrings explaining their purpose, arguments, and expected return types, specifically catering to developers learning the SDK.

## 2. Project Structure
- **Modular (Separated):** Each demo agent will reside in its own isolated folder.
- **Standard Layout:** Enforce a clean separation of concerns within each folder (e.g., `agent.py` for orchestration, `tools.py` for tool definitions, `__init__.py` for packaging, and an `.env` template).
- **Strict Service Isolation:** If a demo includes supplementary services alongside the ADK agent (e.g., a mock REST API or a frontend UI), they must be strictly isolated. Each service must have its own dedicated subdirectory, dependency manifest (e.g., `requirements.txt`), and deployment configuration (e.g., `Dockerfile`). Never mix agent SDK dependencies with supplementary service dependencies to prevent bloated or insecure container images.

## 3. Error Handling & Resilience
- **Fail-fast (Debuggable):** Demos should not silently swallow errors. Allow exceptions (like tool failures or API errors) to surface immediately so developers can inspect tracebacks and understand failure modes.

## 4. Output UX & Deployment Readiness
- **Omni-Surface Compatibility:** Every agent must be designed to run seamlessly across all ADK surfaces.
- **Web UI & CLI:** Code must support execution via standard console output, rich CLI (e.g., `adk run`), and the interactive web interface (`adk web`).
- **Cloud Deployment:** Agents must be structurally compatible for immediate deployment to both Google Vertex AI Agent Engine and Google Cloud Run using the `adk deploy` CLI commands.

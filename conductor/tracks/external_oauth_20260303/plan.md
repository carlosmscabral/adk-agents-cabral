# Implementation Plan: Implement External OAuth/OIDC Tool Authentication Flow

## Phase 1: API Setup & Mocking
- [ ] Task: Create a new directory for the demo project (e.g., `external_oauth_agent`).
- [ ] Task: Scaffold the FastAPI application (`app/api.py`) with a simple GET endpoint that simulates data retrieval.
- [ ] Task: Implement JWT validation logic in the FastAPI endpoint (simulating Keycloak/OIDC validation of `Authorization: Bearer <token>`).
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Agent Implementation & Core ADK Usage
- [ ] Task: Scaffold the ADK project structure (`agent.py`, `tools.py`, `__init__.py`) alongside the API.
- [ ] Task: Implement the target tool function in `tools.py` using `tool_context.state.get(f"temp:{os.getenv('AUTH_ID')}")` to pass credentials to the FastAPI app.
- [ ] Task: Implement the central `LlmAgent` in `agent.py` to use the tool.
- [ ] Task: Write a `run_agent.py` test script that manually seeds the `session_service` state with a mock token to programmatically test the agent's logic.
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Deployment & Documentation
- [ ] Task: Provide a `Dockerfile` to deploy the FastAPI application to Google Cloud Run.
- [ ] Task: Ensure the agent structure adheres to the format required for deployment to Vertex AI Agent Engine.
- [ ] Task: Write a highly detailed `README.md` that guides a developer through the process of registering the agent, configuring the OAuth client in GCP, and setting up the Gemini Enterprise connection.
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

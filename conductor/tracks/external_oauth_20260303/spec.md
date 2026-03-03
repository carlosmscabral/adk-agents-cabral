# Specification: Implement External OAuth/OIDC Tool Authentication Flow

## Objective
Create a demonstration project showcasing how an ADK (Agent Development Kit) Python agent can securely consume externally generated OAuth/OIDC access tokens (e.g., from Gemini Enterprise / AgentSpace) to call a protected downstream API.

## Core Components
1. **Target API (Cloud Run + FastAPI):**
   - A simple REST API built with FastAPI.
   - It will feature a protected endpoint that validates an incoming JWT/OIDC token (using a Keycloak or generic signature check mechanism).
   - Designed to be easily deployed to Google Cloud Run.

2. **The ADK Agent (Agent Engine):**
   - Built using the `google.adk.agents.Agent` class.
   - Contains a custom tool function that reaches out to the FastAPI Cloud Run endpoint.
   - Uses `tool_context.state.get(f"temp:{os.getenv('AUTH_ID')}")` to extract the access token passed down by Gemini Enterprise.
   - Configured and structured for deployment to Vertex AI Agent Engine.

## Interaction Flow
1. The user interacts with the agent via Gemini Enterprise.
2. The agent attempts to use the protected tool.
3. Gemini Enterprise triggers an OAuth consent flow (if a token is not already active).
4. Gemini Enterprise receives the OAuth access token and passes it to the ADK agent's state.
5. The ADK tool reads the token from `tool_context.state`, builds the headers (`Authorization: Bearer <token>`), and requests the Cloud Run API.
6. The Cloud Run API validates the token and returns the data.
7. The agent summarizes the data back to the user.

## Educational Documentation
The agent folder must include a highly descriptive `README.md` containing the exact steps provided in the requirements (e.g., "Configure OAuth Client in Google Cloud", "Create an Authorization Resource in Gemini Enterprise", etc.) to educate developers on establishing this setup.

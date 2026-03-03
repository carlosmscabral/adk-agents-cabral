# External OAuth/OIDC Tool Authentication Flow Demo

This project demonstrates how to build a Google ADK Python agent that securely consumes externally generated OAuth/OIDC access tokens. Specifically, it shows how to integrate an agent running in **Vertex AI Agent Engine** with **Gemini Enterprise (AgentSpace)** acting as the OAuth intermediary, authenticating against a **Keycloak** Identity Provider.

This setup allows Gemini Enterprise to handle the user-facing OAuth consent flow with Keycloak, while passing the resulting access token securely to your agent's backend tools. The tools can then use the token to access protected APIs (like the mock Cloud Run API provided in this demo, which validates the token against Keycloak's public keys).

## Architecture

1.  **Target API (`api_server/`)**: A FastAPI REST service designed for Google Cloud Run. It exposes a `/api/v1/protected-data` endpoint requiring a valid Bearer token. It dynamically fetches Keycloak's JSON Web Key Set (JWKS) to mathematically verify the token's signature.
2.  **ADK Agent (`app/`)**: The core agent logic designed for Vertex AI Agent Engine. It uses a tool that retrieves the OAuth token injected into the session state by Gemini Enterprise.

---

## Prerequisites & Setup

### 1. Configure Keycloak Client
You must configure an OAuth client within your Keycloak Realm that Gemini Enterprise will use to facilitate the authentication.

1. In your Keycloak Administration Console, navigate to **Clients**.
2. Click **Create client**.
3. Set the Client ID (e.g., `gemini-enterprise-client`).
4. Ensure **Standard Flow** (Authorization Code Flow) is enabled.
5. Add the following to the **"Valid redirect URIs"** list (This is the critical step for Gemini Enterprise):
   ```
   https://vertexaisearch.cloud.google.com/oauth-redirect
   ```
6. Ensure **Client Authentication** is ON if you want a confidential client, and note down the **Client ID** and **Client Secret** (from the Credentials tab).
7. Note your Realm's OpenID Configuration URL (e.g., `http://34.111.38.17.nip.io/realms/cabral/.well-known/openid-configuration`).

### 2. Create an Authorization Resource in Gemini Enterprise
Gemini Enterprise requires an Authorization resource to securely store the client credentials, rather than hardcoding them in the agent.

*Note: This step is typically done via the Vertex AI Discovery Engine API.*

You need to create a configuration linking:
- `AUTH_ID`: A unique identifier (e.g., `my-adk-agent-auth`). This is critical as it maps the token to the ADK session state.
- `OAUTH_CLIENT_ID`: From step 1.
- `OAUTH_CLIENT_SECRET`: From step 1.
- `OAUTH_AUTH_URI`: The authorization endpoint from Keycloak's openid-configuration (e.g., `http://34.111.38.17.nip.io/realms/cabral/protocol/openid-connect/auth&redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html&response_type=code&access_type=offline&prompt=consent`).
- `OAUTH_TOKEN_URI`: The token endpoint from Keycloak's openid-configuration (e.g., `http://34.111.38.17.nip.io/realms/cabral/protocol/openid-connect/token`).

### 3. Deploy the Target API (Cloud Run)
To test the flow, you need the protected API running.

```bash
cd external_oauth_agent
# The API defaults to the provided Keycloak URL, but you can override it:
# export OIDC_WELL_KNOWN_URL="http://your-keycloak/.../.well-known/openid-configuration"

gcloud run deploy mock-protected-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="OIDC_WELL_KNOWN_URL=http://34.111.38.17.nip.io/realms/cabral/.well-known/openid-configuration"
```
*Note the returned URL and update `API_URL` in `app/tools.py` if necessary.*

### 4. Deploy the ADK Agent (Vertex AI Agent Engine)
Deploy the agent code using the ADK CLI. Ensure your `app/` directory is packaged correctly.

```bash
cd external_oauth_agent
# Set the environment variable so the agent knows which key to look for
export AUTH_ID="my-adk-agent-auth" 
# Set the URL of your deployed Cloud Run API (from Step 3)
export API_URL="https://mock-protected-api-xyz.a.run.app/api/v1/protected-data"

adk deploy agent_engine \
  --project your-google-cloud-project-id \
  --region us-central1 \
  --env_vars AUTH_ID=${AUTH_ID},API_URL=${API_URL} \
  app
```
*Note: The agent code in `app/tools.py` dynamically reads `API_URL` from the environment. Ensure this is set correctly to point to your protected endpoint.*

### 5. Register Your ADK Agent in Gemini Enterprise
Link your deployed Agent Engine resource with the Authorization resource you created in step 2.

When defining the agent payload for Gemini Enterprise, ensure you include the `authorizationConfig`:
```json
{
  "name": "projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/engines/{ENGINE_ID}/agents/{AGENT_ID}",
  "displayName": "Financial Data Agent",
  "agentEngineResource": "projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}",
  "authorizationConfig": {
    "authorizationId": "{AUTH_ID}"
  },
  // ... other configs
}
```

---

## How It Works (The Code)

When a user triggers an action requiring the API, Gemini Enterprise initiates the OAuth flow with Keycloak. Upon success, it passes the token to the ADK Agent.

In `app/tools.py`, the tool extracts this dynamically injected token from the `tool_context.state`:

```python
auth_id = os.getenv("AUTH_ID", "my-adk-agent-auth")

# The string format must strictly be temp:<AUTH_ID>
token_key = f"temp:{auth_id}"

# The token is dynamically injected here by the Gemini Enterprise framework
access_token = tool_context.state.get(token_key)
```

The API (`api_server/main.py`) then validates this token by:
1. Fetching the `jwks_uri` from Keycloak's `.well-known/openid-configuration`.
2. Extracting the `kid` (Key ID) from the incoming token's header.
3. Finding the matching public key in the JWKS.
4. Using that public key to cryptographically verify the token's signature.

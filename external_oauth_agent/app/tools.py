import os
import requests
from typing import Dict, Any
from google.adk.tools import ToolContext

# URL for the mock API running locally (or in Cloud Run)
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/protected-data")

def fetch_protected_financial_data(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Fetches the user's protected financial data from the external API.
    Requires a valid OAuth/OIDC token to be present in the session state.

    Returns:
        dict: The response from the API, or an error dictionary.
    """
    auth_id = os.getenv("AUTH_ID", "my-adk-agent-auth")
    
    # Retrieve the access token from tool_context.state, placed there by Gemini Enterprise
    token_key = f"temp:{auth_id}"
    access_token = tool_context.state.get(token_key)

    if not access_token:
        return {
            "status": "error",
            "message": "OAuth token not available in state. User consent may be needed or Gemini Enterprise integration is not configured."
        }

    # Build the authorization header using the retrieved token
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
             return {"status": "error", "message": "Token rejected by API. Unauthorized."}
        return {"status": "error", "message": f"HTTP Error: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Connection Error: {str(e)}"}

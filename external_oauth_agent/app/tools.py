import os
import requests
import logging
from typing import Dict, Any
from google.adk.tools import ToolContext

# Configure logger for troubleshooting
logger = logging.getLogger(__name__)

# URL for the mock API running locally (or in Cloud Run)
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/protected-data")

def fetch_protected_financial_data(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Fetches the user's protected financial data from the external API.
    Requires a valid OAuth/OIDC token to be present in the session state.

    Returns:
        dict: The response from the API, or an error dictionary.
    """
    logger.info("DEBUG: [fetch_protected_financial_data] Function started.")

    # [TROUBLESHOOTING] Dump full state content safely using .to_dict()
    try:
        state_dict = tool_context.state.to_dict()
        logger.info(f"DEBUG: [TROUBLESHOOTING] tool_context.state type: {type(tool_context.state)}")
        logger.info(f"DEBUG: [TROUBLESHOOTING] tool_context.state keys: {list(state_dict.keys())}")
        logger.info(f"DEBUG: [TROUBLESHOOTING] tool_context.state full content: {state_dict}")
    except Exception as e:
        logger.error(f"DEBUG: [TROUBLESHOOTING] Failed to parse state dictionary: {e}")

    auth_id = os.getenv("AUTH_ID", "my-adk-agent-auth")
    logger.info(f"DEBUG: Resolved AUTH_ID from environment: '{auth_id}'")
    
    # Retrieve the access token from tool_context.state, placed there by Gemini Enterprise
    token_key = f"temp:{auth_id}"
    logger.info(f"DEBUG: Attempting to retrieve token from state using key: '{token_key}'")
    
    access_token = tool_context.state.get(token_key)

    if access_token:
        logger.info(f"DEBUG: Access token successfully found in state! Prefix: {str(access_token)[:15]}...")
    else:
        logger.warning(f"DEBUG: Access token NOT FOUND for key '{token_key}'. Returning error to LLM.")
        return {
            "status": "error",
            "message": "OAuth token not available in state. User consent may be needed or Gemini Enterprise integration is not configured."
        }

    # Build the authorization header using the retrieved token
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    logger.info(f"DEBUG: Preparing GET request to target API URL: {API_URL}")

    try:
        logger.info("DEBUG: Sending request to API...")
        response = requests.get(API_URL, headers=headers)
        logger.info(f"DEBUG: API request completed. Status Code: {response.status_code}")
        
        response.raise_for_status() # Raise an exception for bad status codes
        
        data = response.json()
        logger.info("DEBUG: Successfully parsed JSON response from API. Returning data.")
        return data
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"DEBUG: HTTPError caught during API request: {str(e)}")
        if response.status_code == 401:
             logger.error("DEBUG: Received 401 from API. The token might be invalid or expired.")
             return {"status": "error", "message": "Token rejected by API. Unauthorized."}
        return {"status": "error", "message": f"HTTP Error: {str(e)}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"DEBUG: RequestException caught: {str(e)}")
        return {"status": "error", "message": f"Connection Error: {str(e)}"}
    except Exception as e:
        logger.error(f"DEBUG: Unexpected general exception caught: {str(e)}")
        return {"status": "error", "message": f"Unexpected Error: {str(e)}"}

import os
import requests
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Protected API (Keycloak)", description="An API validating tokens against Keycloak")

# The OIDC Discovery URL provided by the user
OIDC_WELL_KNOWN_URL = os.getenv(
    "OIDC_WELL_KNOWN_URL", 
    "http://34.111.38.17.nip.io/realms/cabral/.well-known/openid-configuration"
)

# Fetch the JWKS URI from the discovery document
try:
    oidc_config = requests.get(OIDC_WELL_KNOWN_URL).json()
    JWKS_URI = oidc_config["jwks_uri"]
    # Initialize the JWK client to fetch and cache public keys
    jwks_client = PyJWKClient(JWKS_URI)
except Exception as e:
    print(f"Warning: Could not initialize JWKS client from {OIDC_WELL_KNOWN_URL}. Error: {e}")
    jwks_client = None

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Validates the incoming JWT token against Keycloak's public keys.
    """
    if not jwks_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OIDC configuration failed. Cannot validate tokens.",
        )

    token = credentials.credentials
    try:
        # Fetch the signing key corresponding to the token's kid header
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and verify the token
        # Note: In a production environment, you should also verify 'audience' (aud)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False} # Set to True and provide 'audience' in production
        )
        return payload
    except jwt.PyJWKClientError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unable to fetch signing key: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.DecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token format: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.ExpiredSignatureError:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class ProtectedDataResponse(BaseModel):
    message: str
    user_info: Dict[str, Any]
    data: Dict[str, str]

@app.get("/api/v1/protected-data", response_model=ProtectedDataResponse)
async def get_protected_data(token_payload: Dict[str, Any] = Depends(verify_token)):
    """
    A protected endpoint requiring a valid Keycloak Bearer token.
    """
    email = token_payload.get("email", token_payload.get("preferred_username", "unknown_user"))
    
    return ProtectedDataResponse(
        message="Successfully accessed protected endpoint using Keycloak token!",
        user_info={
            "email_or_username": email, 
            "roles": token_payload.get("realm_access", {}).get("roles", []),
            "issuer": token_payload.get("iss")
        },
        data={
            "account_balance": "$1,250.00",
            "last_transaction": "Coffee Shop - $4.50",
            "status": "Active"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

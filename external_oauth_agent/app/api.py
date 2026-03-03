from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Mock Protected API", description="A simple API to validate ADK OAuth integration")

# Using a hardcoded mock secret for demo purposes.
# In a real scenario, this would be a public key from Keycloak/OIDC provider.
MOCK_JWT_SECRET = "super-secret-key"
ALGORITHM = "HS256"

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Validates the incoming JWT token. 
    Simulates the validation of an OIDC token from Gemini Enterprise.
    """
    token = credentials.credentials
    try:
        # We allow an unverified decode in this mock if the user just passes ANY token
        # But to be somewhat realistic, let's try to decode it with our mock secret.
        # If it's a real Google token, this will fail unless we decode without verification.
        # For demo simplicity, we'll try to decode without signature verification if it's not our mock token.
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        return unverified_payload
    except jwt.DecodeError:
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
    A protected endpoint that requires a valid Bearer token.
    Returns some simulated secure data.
    """
    # Extract some info from the payload if it exists
    email = token_payload.get("email", "unknown_user@example.com")
    
    return ProtectedDataResponse(
        message="Successfully accessed protected endpoint!",
        user_info={"email": email, "auth_provider": token_payload.get("iss", "mock_issuer")},
        data={
            "account_balance": "$1,250.00",
            "last_transaction": "Coffee Shop - $4.50",
            "status": "Active"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

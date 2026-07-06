import json

import jwt
import jwt.algorithms
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class AppleAuthRequest(BaseModel):
    idToken: str


class AppleUser(BaseModel):
    email: str


class AppleAuthResponse(BaseModel):
    user: AppleUser


APPLE_PUBLIC_KEY_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"


def get_apple_public_key(kid: str):
    response = requests.get(APPLE_PUBLIC_KEY_URL)
    keys = response.json()["keys"]
    for key in keys:
        if key["kid"] == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
    raise HTTPException(status_code=400, detail="Invalid key ID")


@router.post("/auth/apple", response_model=AppleAuthResponse)
async def authenticate_with_apple(request: AppleAuthRequest):
    try:
        # Decode the token header to get the key ID (kid)
        header = jwt.get_unverified_header(request.idToken)
        kid = header["kid"]

        # Get the public key
        public_key = get_apple_public_key(kid)

        # Verify and decode the token
        decoded_token = jwt.decode(
            request.idToken,
            public_key,
            algorithms=["RS256"],
            audience="YOUR_CLIENT_ID",  # Replace with your Apple Client ID
            issuer=APPLE_ISSUER,
        )

        # Extract email from the decoded token
        email = decoded_token.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="Email not found in the token")

        # Here you would typically check if the user exists in your database
        # and create a new user if they don't exist

        return AppleAuthResponse(user=AppleUser(email=email))

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

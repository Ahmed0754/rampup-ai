import logging
import os

import jwt
from fastapi import Header, HTTPException

from app.services.supabase import get_supabase

logger = logging.getLogger("rampup.auth")


def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ").strip()

    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
    if jwt_secret:
        # Supabase signs session tokens with this project secret (HS256), so
        # the signature and expiry can be checked locally instead of making a
        # network round-trip to Supabase Auth on every single request.
        try:
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="authenticated")
            return payload["sub"]
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    # No local signing secret configured - fall back to asking Supabase Auth
    # directly, or (if Supabase isn't configured at all, e.g. local dev)
    # trust the bearer token itself as the user id.
    client = get_supabase()
    if client is None:
        return token

    try:
        response = client.auth.get_user(token)
        return response.user.id
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

import logging

from fastapi import Header, HTTPException

from app.services.supabase import get_supabase

logger = logging.getLogger("rampup.auth")


def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    client = get_supabase()
    if client is None:
        # Supabase not configured (e.g. local dev) - trust the token as the user id.
        return token

    try:
        response = client.auth.get_user(token)
        return response.user.id
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

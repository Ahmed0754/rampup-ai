import time

import jwt
import pytest
from fastapi import HTTPException

from app.deps import get_current_user_id

SECRET = "test-jwt-secret-that-is-long-enough-for-hs256"


def _token(sub="user-123", aud="authenticated", exp_delta=3600, secret=SECRET):
    now = int(time.time())
    payload = {"sub": sub, "aud": aud, "iat": now, "exp": now + exp_delta}
    return jwt.encode(payload, secret, algorithm="HS256")


def test_verifies_locally_with_jwt_secret(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    token = _token(sub="user-abc")
    assert get_current_user_id(authorization=f"Bearer {token}") == "user-abc"


def test_rejects_bad_signature(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    token = _token(secret="a-completely-different-secret-value-here")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


def test_rejects_expired_token(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    token = _token(exp_delta=-3600)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


def test_rejects_wrong_audience(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    token = _token(aud="something-else")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


def test_missing_header_returns_401():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(authorization=None)
    assert exc_info.value.status_code == 401


def test_falls_back_to_trusting_token_when_unconfigured(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    # conftest already strips SUPABASE_URL/SUPABASE_SERVICE_KEY, so
    # get_supabase() is None here too and the raw token is trusted.
    assert get_current_user_id(authorization="Bearer some-raw-token") == "some-raw-token"

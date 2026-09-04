import os

import pytest
from fastapi.testclient import TestClient

from app.main import app  # noqa: E402
from app.services import supabase as supabase_service  # noqa: E402

# Importing app.main runs load_dotenv(), which may populate real Supabase creds
# from a local .env. Strip them so tests exercise the "not configured" path where
# the bearer token is trusted as the user id, and drop any cached client.
os.environ.pop("SUPABASE_URL", None)
os.environ.pop("SUPABASE_SERVICE_KEY", None)
supabase_service._client = None

AUTH_HEADERS = {"Authorization": "Bearer test-user-id"}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return AUTH_HEADERS


@pytest.fixture(autouse=True)
def gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

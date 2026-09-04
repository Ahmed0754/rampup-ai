import os

import pytest
from fastapi.testclient import TestClient

os.environ.pop("SUPABASE_URL", None)
os.environ.pop("SUPABASE_SERVICE_KEY", None)

from app.main import app  # noqa: E402

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

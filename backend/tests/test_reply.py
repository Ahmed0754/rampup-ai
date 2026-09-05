import json
from unittest.mock import MagicMock, patch

from app.models import MAX_INPUT_CHARS
from app.services.ai import AIServiceError


def _chunks(text, n=3):
    size = max(1, len(text) // n)
    return [text[i : i + size] for i in range(0, len(text), size)]


def _mock_service(reply_text="Sounds good, I'll take care of it."):
    mock = MagicMock()
    mock.generate_reply_stream.return_value = iter(_chunks(reply_text))
    return mock


def _error_service(message="AI service unavailable"):
    def failing_gen():
        raise AIServiceError(message)
        yield  # pragma: no cover - unreachable, keeps this a generator

    mock = MagicMock()
    mock.generate_reply_stream.return_value = failing_gen()
    return mock


def _parse_ndjson(response):
    return [json.loads(line) for line in response.text.strip().splitlines() if line.strip()]


def _done(response):
    return next(e for e in _parse_ndjson(response) if e["type"] == "done")


def test_reply_casual_tone(client, auth_headers):
    with patch("app.routers.reply.AIService", return_value=_mock_service("yeah for sure, on it!")):
        response = client.post(
            "/api/reply", json={"text": "can you fix this today?", "tone": "casual"}, headers=auth_headers
        )
    assert response.status_code == 200
    done = _done(response)
    assert done["tone"] == "casual"
    assert done["reply"] == "yeah for sure, on it!"
    assert done["saved"] is False  # no Supabase configured in tests


def test_reply_professional_tone(client, auth_headers):
    with patch("app.routers.reply.AIService", return_value=_mock_service("I will have this done today.")):
        response = client.post(
            "/api/reply", json={"text": "can you fix this today?", "tone": "professional"}, headers=auth_headers
        )
    assert response.status_code == 200
    assert _done(response)["tone"] == "professional"


def test_reply_manager_safe_tone(client, auth_headers):
    with patch("app.routers.reply.AIService", return_value=_mock_service("Taking ownership of this now.")):
        response = client.post(
            "/api/reply", json={"text": "can you fix this today?", "tone": "manager-safe"}, headers=auth_headers
        )
    assert response.status_code == 200
    assert _done(response)["tone"] == "manager-safe"


def test_reply_confused_but_trying_tone(client, auth_headers):
    with patch(
        "app.routers.reply.AIService",
        return_value=_mock_service("I'm not 100% sure yet, but looking into it."),
    ):
        response = client.post(
            "/api/reply",
            json={"text": "can you fix this today?", "tone": "confused-but-trying"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert _done(response)["tone"] == "confused-but-trying"


def test_reply_missing_text_field_returns_422(client, auth_headers):
    response = client.post("/api/reply", json={"tone": "casual"}, headers=auth_headers)
    assert response.status_code == 422


def test_reply_missing_tone_field_returns_422(client, auth_headers):
    response = client.post("/api/reply", json={"text": "hello there"}, headers=auth_headers)
    assert response.status_code == 422


def test_reply_invalid_tone_returns_422(client, auth_headers):
    response = client.post("/api/reply", json={"text": "hello there", "tone": "sarcastic"}, headers=auth_headers)
    assert response.status_code == 422


def test_reply_empty_text_returns_422(client, auth_headers):
    response = client.post("/api/reply", json={"text": "   ", "tone": "casual"}, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["detail"] == "Please paste some text first"


def test_reply_over_length_limit_returns_422(client, auth_headers):
    response = client.post(
        "/api/reply",
        json={"text": "x" * (MAX_INPUT_CHARS + 1), "tone": "casual"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_reply_ai_error_returns_502(client, auth_headers):
    with patch("app.routers.reply.AIService", return_value=_error_service()):
        response = client.post("/api/reply", json={"text": "hello there", "tone": "casual"}, headers=auth_headers)
    assert response.status_code == 502


def test_reply_missing_api_key_returns_500(client, auth_headers, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/reply", json={"text": "hello there", "tone": "casual"}, headers=auth_headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "API key not configured"

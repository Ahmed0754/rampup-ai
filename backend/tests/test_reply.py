from unittest.mock import MagicMock, patch

from app.services.ai import AIServiceError


def _mock_service(reply_text="Sounds good, I'll take care of it."):
    mock = MagicMock()
    mock.generate_reply.return_value = reply_text
    return mock


def test_reply_casual_tone(client, auth_headers):
    with patch("app.routers.reply.AIService", return_value=_mock_service("yeah for sure, on it!")):
        response = client.post(
            "/api/reply", json={"text": "can you fix this today?", "tone": "casual"}, headers=auth_headers
        )
    assert response.status_code == 200
    body = response.json()
    assert body["tone"] == "casual"
    assert body["reply"] == "yeah for sure, on it!"


def test_reply_professional_tone(client, auth_headers):
    with patch("app.routers.reply.AIService", return_value=_mock_service("I will have this done today.")):
        response = client.post(
            "/api/reply", json={"text": "can you fix this today?", "tone": "professional"}, headers=auth_headers
        )
    assert response.status_code == 200
    assert response.json()["tone"] == "professional"


def test_reply_manager_safe_tone(client, auth_headers):
    with patch("app.routers.reply.AIService", return_value=_mock_service("Taking ownership of this now.")):
        response = client.post(
            "/api/reply", json={"text": "can you fix this today?", "tone": "manager-safe"}, headers=auth_headers
        )
    assert response.status_code == 200
    assert response.json()["tone"] == "manager-safe"


def test_reply_confused_but_trying_tone(client, auth_headers):
    with patch("app.routers.reply.AIService", return_value=_mock_service("I'm not 100% sure yet, but looking into it.")):
        response = client.post(
            "/api/reply",
            json={"text": "can you fix this today?", "tone": "confused-but-trying"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert response.json()["tone"] == "confused-but-trying"


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


def test_reply_ai_error_returns_502(client, auth_headers):
    mock = MagicMock()
    mock.generate_reply.side_effect = AIServiceError("AI service unavailable")
    with patch("app.routers.reply.AIService", return_value=mock):
        response = client.post("/api/reply", json={"text": "hello there", "tone": "casual"}, headers=auth_headers)
    assert response.status_code == 502


def test_reply_missing_api_key_returns_500(client, auth_headers, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/reply", json={"text": "hello there", "tone": "casual"}, headers=auth_headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "API key not configured"

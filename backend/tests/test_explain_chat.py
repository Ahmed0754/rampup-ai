import json
from unittest.mock import MagicMock, patch

from app.models import MAX_INPUT_CHARS
from app.services.ai import AIServiceError

PASTE = {"id": "paste-1", "raw_text": "Traceback: KeyError", "explanation": "A key was missing.", "input_type": "error"}


def _chunks(text, n=3):
    size = max(1, len(text) // n)
    return [text[i : i + size] for i in range(0, len(text), size)]


def _mock_service(reply_text="It means the dictionary didn't have that key."):
    mock = MagicMock()
    mock.chat_stream.return_value = iter(_chunks(reply_text))
    return mock


def _error_service(message="AI service unavailable"):
    def failing_gen():
        raise AIServiceError(message)
        yield  # pragma: no cover - unreachable, keeps this a generator

    mock = MagicMock()
    mock.chat_stream.return_value = failing_gen()
    return mock


def _parse_ndjson(response):
    return [json.loads(line) for line in response.text.strip().splitlines() if line.strip()]


def _done(response):
    return next(e for e in _parse_ndjson(response) if e["type"] == "done")


def test_explain_chat_returns_streamed_reply(client, auth_headers):
    with (
        patch("app.routers.explain.get_paste", return_value=PASTE),
        patch("app.routers.explain.get_explain_chat_messages", return_value=[]),
        patch("app.routers.explain.save_explain_chat_message", return_value="msg-1"),
        patch("app.routers.explain.AIService", return_value=_mock_service()),
    ):
        response = client.post(
            "/api/explain/chat",
            json={"paste_id": "paste-1", "message": "what does that mean?"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    done = _done(response)
    assert done["reply"] == "It means the dictionary didn't have that key."
    assert done["saved"] is True


def test_explain_chat_saves_question_even_before_reply_finishes(client, auth_headers):
    with (
        patch("app.routers.explain.get_paste", return_value=PASTE),
        patch("app.routers.explain.get_explain_chat_messages", return_value=[]),
        patch("app.routers.explain.save_explain_chat_message", return_value="msg-1") as mock_save,
        patch("app.routers.explain.AIService", return_value=_mock_service()),
    ):
        client.post(
            "/api/explain/chat",
            json={"paste_id": "paste-1", "message": "what does that mean?"},
            headers=auth_headers,
        )
    roles_saved = [call.kwargs["role"] for call in mock_save.call_args_list]
    assert roles_saved == ["user", "assistant"]


def test_explain_chat_trims_history_to_last_ten(client, auth_headers):
    long_history = [{"role": "user", "content": f"q{i}"} for i in range(15)]
    mock_service = _mock_service()
    with (
        patch("app.routers.explain.get_paste", return_value=PASTE),
        patch("app.routers.explain.get_explain_chat_messages", return_value=long_history),
        patch("app.routers.explain.save_explain_chat_message", return_value="msg-1"),
        patch("app.routers.explain.AIService", return_value=mock_service),
    ):
        client.post(
            "/api/explain/chat",
            json={"paste_id": "paste-1", "message": "another question"},
            headers=auth_headers,
        )
    passed_history = mock_service.chat_stream.call_args.args[2]
    assert len(passed_history) == 10
    assert passed_history[0]["content"] == "q5"  # the last 10 of 15


def test_explain_chat_paste_not_found_returns_404(client, auth_headers):
    with patch("app.routers.explain.get_paste", return_value=None):
        response = client.post(
            "/api/explain/chat",
            json={"paste_id": "does-not-exist", "message": "huh?"},
            headers=auth_headers,
        )
    assert response.status_code == 404


def test_explain_chat_empty_message_returns_422(client, auth_headers):
    response = client.post(
        "/api/explain/chat", json={"paste_id": "paste-1", "message": "   "}, headers=auth_headers
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Please enter a question"


def test_explain_chat_over_length_limit_returns_422(client, auth_headers):
    response = client.post(
        "/api/explain/chat",
        json={"paste_id": "paste-1", "message": "x" * (MAX_INPUT_CHARS + 1)},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_explain_chat_requires_auth_header(client):
    response = client.post("/api/explain/chat", json={"paste_id": "paste-1", "message": "hi"})
    assert response.status_code == 401


def test_explain_chat_missing_api_key_returns_500(client, auth_headers, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with (
        patch("app.routers.explain.get_paste", return_value=PASTE),
        patch("app.routers.explain.get_explain_chat_messages", return_value=[]),
    ):
        response = client.post(
            "/api/explain/chat", json={"paste_id": "paste-1", "message": "hi"}, headers=auth_headers
        )
    assert response.status_code == 500
    assert response.json()["detail"] == "API key not configured"


def test_explain_chat_ai_error_returns_502(client, auth_headers):
    with (
        patch("app.routers.explain.get_paste", return_value=PASTE),
        patch("app.routers.explain.get_explain_chat_messages", return_value=[]),
        patch("app.routers.explain.save_explain_chat_message", return_value="msg-1"),
        patch("app.routers.explain.AIService", return_value=_error_service()),
    ):
        response = client.post(
            "/api/explain/chat", json={"paste_id": "paste-1", "message": "hi"}, headers=auth_headers
        )
    assert response.status_code == 502

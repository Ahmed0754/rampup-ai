import json
from unittest.mock import MagicMock, patch

from app.models import MAX_INPUT_CHARS
from app.services.ai import AIServiceError

STREAM_TEXT = (
    "EXPLANATION: Your build failed because a dependency is missing.\n"
    "WHAT_THEY_MEAN: The system needs you to install the missing package.\n"
    "WHAT_TO_DO_NEXT: Run npm install to fetch the missing dependency.\n"
    "ACTION_ITEMS:\n"
    "- Run npm install\n"
    "- Re-run the build\n"
    "- Check package.json\n"
)

EXPLAIN_RESULT = {
    "explanation": "Your build failed because a dependency is missing.",
    "what_they_mean": "The system needs you to install the missing package.",
    "what_to_do_next": "Run npm install to fetch the missing dependency.",
    "action_items": ["Run npm install", "Re-run the build", "Check package.json"],
}


def _chunks(text, n=4):
    """Split text into n pieces to exercise multi-chunk streaming."""
    size = max(1, len(text) // n)
    return [text[i : i + size] for i in range(0, len(text), size)]


def _mock_service(stream_text=STREAM_TEXT):
    mock = MagicMock()
    mock.explain_stream.return_value = iter(_chunks(stream_text))
    return mock


def _error_service(message="AI service unavailable"):
    def failing_gen():
        raise AIServiceError(message)
        yield  # pragma: no cover - unreachable, keeps this a generator

    mock = MagicMock()
    mock.explain_stream.return_value = failing_gen()
    return mock


def _parse_ndjson(response):
    return [json.loads(line) for line in response.text.strip().splitlines() if line.strip()]


def test_explain_endpoint_returns_expected_fields(client, auth_headers):
    with patch("app.routers.explain.AIService", return_value=_mock_service()):
        response = client.post("/api/explain", json={"text": "Traceback: ModuleNotFoundError"}, headers=auth_headers)

    assert response.status_code == 200
    events = _parse_ndjson(response)
    assert any(e["type"] == "chunk" for e in events)
    done = next(e for e in events if e["type"] == "done")
    assert done["input_type"] == "error"
    assert done["explanation"] == EXPLAIN_RESULT["explanation"]
    assert done["what_they_mean"] == EXPLAIN_RESULT["what_they_mean"]
    assert done["what_to_do_next"] == EXPLAIN_RESULT["what_to_do_next"]
    assert done["action_items"] == EXPLAIN_RESULT["action_items"]


def test_explain_saves_paste_to_supabase(client, auth_headers):
    with (
        patch("app.routers.explain.AIService", return_value=_mock_service()),
        patch("app.routers.explain.save_paste", return_value="paste-123") as mock_save,
    ):
        response = client.post("/api/explain", json={"text": "Traceback: ModuleNotFoundError"}, headers=auth_headers)

    assert response.status_code == 200
    done = next(e for e in _parse_ndjson(response) if e["type"] == "done")
    assert done["paste_id"] == "paste-123"
    assert done["saved"] is True
    mock_save.assert_called_once()
    _, kwargs = mock_save.call_args
    assert kwargs["user_id"] == "test-user-id"
    assert kwargs["input_type"] == "error"


def test_explain_empty_text_returns_422(client, auth_headers):
    response = client.post("/api/explain", json={"text": "   "}, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["detail"] == "Please paste some text first"


def test_explain_over_length_limit_returns_422(client, auth_headers):
    response = client.post(
        "/api/explain", json={"text": "x" * (MAX_INPUT_CHARS + 1)}, headers=auth_headers
    )
    assert response.status_code == 422


def test_explain_missing_api_key_returns_500(client, auth_headers, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/explain", json={"text": "some real text"}, headers=auth_headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "API key not configured"


def test_explain_ai_error_returns_502(client, auth_headers):
    with patch("app.routers.explain.AIService", return_value=_error_service()):
        response = client.post("/api/explain", json={"text": "some real text"}, headers=auth_headers)

    assert response.status_code == 502
    assert response.json()["detail"] == "AI service unavailable"


def test_explain_classifies_email_input_type(client, auth_headers):
    with patch("app.routers.explain.AIService", return_value=_mock_service()):
        response = client.post(
            "/api/explain",
            json={"text": "Dear team,\n\nPlease review the attached doc."},
            headers=auth_headers,
        )

    assert response.status_code == 200
    done = next(e for e in _parse_ndjson(response) if e["type"] == "done")
    assert done["input_type"] == "email"


def test_explain_requires_auth_header(client):
    response = client.post("/api/explain", json={"text": "some text"})
    assert response.status_code == 401


def test_explain_falls_back_when_model_ignores_format(client, auth_headers):
    with patch("app.routers.explain.AIService", return_value=_mock_service("just a plain sentence, no markers")):
        response = client.post("/api/explain", json={"text": "hi"}, headers=auth_headers)

    assert response.status_code == 200
    done = next(e for e in _parse_ndjson(response) if e["type"] == "done")
    assert done["explanation"] == "just a plain sentence, no markers"
    assert done["action_items"] == []

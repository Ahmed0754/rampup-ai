from unittest.mock import MagicMock, patch

from app.services.claude import ClaudeServiceError

EXPLAIN_RESULT = {
    "explanation": "Your build failed because a dependency is missing.",
    "what_they_mean": "The system needs you to install the missing package.",
    "what_to_do_next": "Run npm install to fetch the missing dependency.",
    "action_items": ["Run npm install", "Re-run the build", "Check package.json"],
}


def _mock_service(**overrides):
    mock = MagicMock()
    mock.explain.return_value = {**EXPLAIN_RESULT, **overrides}
    return mock


def test_explain_endpoint_returns_expected_fields(client, auth_headers):
    with patch("app.routers.explain.ClaudeService", return_value=_mock_service()):
        response = client.post("/api/explain", json={"text": "Traceback: ModuleNotFoundError"}, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["input_type"] == "error"
    assert body["explanation"] == EXPLAIN_RESULT["explanation"]
    assert body["what_they_mean"] == EXPLAIN_RESULT["what_they_mean"]
    assert body["what_to_do_next"] == EXPLAIN_RESULT["what_to_do_next"]
    assert body["action_items"] == EXPLAIN_RESULT["action_items"]


def test_explain_saves_paste_to_supabase(client, auth_headers):
    with (
        patch("app.routers.explain.ClaudeService", return_value=_mock_service()),
        patch("app.routers.explain.save_paste", return_value="paste-123") as mock_save,
    ):
        response = client.post("/api/explain", json={"text": "Traceback: ModuleNotFoundError"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["paste_id"] == "paste-123"
    mock_save.assert_called_once()
    _, kwargs = mock_save.call_args
    assert kwargs["user_id"] == "test-user-id"
    assert kwargs["input_type"] == "error"


def test_explain_empty_text_returns_422(client, auth_headers):
    response = client.post("/api/explain", json={"text": "   "}, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["detail"] == "Please paste some text first"


def test_explain_missing_api_key_returns_500(client, auth_headers, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/api/explain", json={"text": "some real text"}, headers=auth_headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "API key not configured"


def test_explain_claude_error_returns_502(client, auth_headers):
    mock = MagicMock()
    mock.explain.side_effect = ClaudeServiceError("AI service unavailable")
    with patch("app.routers.explain.ClaudeService", return_value=mock):
        response = client.post("/api/explain", json={"text": "some real text"}, headers=auth_headers)

    assert response.status_code == 502
    assert response.json()["detail"] == "AI service unavailable"


def test_explain_classifies_email_input_type(client, auth_headers):
    with patch("app.routers.explain.ClaudeService", return_value=_mock_service()):
        response = client.post(
            "/api/explain",
            json={"text": "Dear team,\n\nPlease review the attached doc."},
            headers=auth_headers,
        )

    assert response.status_code == 200
    assert response.json()["input_type"] == "email"


def test_explain_requires_auth_header(client):
    response = client.post("/api/explain", json={"text": "some text"})
    assert response.status_code == 401

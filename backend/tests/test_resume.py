import json
from unittest.mock import MagicMock, patch

from app.models import MAX_INPUT_CHARS
from app.services.ai import AIServiceError

BULLETS = [
    "Built a data pipeline that reduced processing time by 40%",
    "Shipped 12 pull requests across 3 microservices",
    "Mentored 2 new interns on the onboarding process",
]
STREAM_TEXT = "\n".join(f"- {b}" for b in BULLETS)


def _chunks(text, n=3):
    size = max(1, len(text) // n)
    return [text[i : i + size] for i in range(0, len(text), size)]


def _mock_service(stream_text=STREAM_TEXT):
    mock = MagicMock()
    mock.generate_resume_bullets_stream.return_value = iter(_chunks(stream_text))
    return mock


def _error_service(message="AI service unavailable"):
    def failing_gen():
        raise AIServiceError(message)
        yield  # pragma: no cover - unreachable, keeps this a generator

    mock = MagicMock()
    mock.generate_resume_bullets_stream.return_value = failing_gen()
    return mock


def _parse_ndjson(response):
    return [json.loads(line) for line in response.text.strip().splitlines() if line.strip()]


def _done(response):
    return next(e for e in _parse_ndjson(response) if e["type"] == "done")


def test_resume_bullets_endpoint_returns_bullets(client, auth_headers):
    with patch("app.routers.resume.AIService", return_value=_mock_service()):
        response = client.post(
            "/api/resume-bullets",
            json={"description": "worked on the data pipeline project"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert _done(response)["bullets"] == BULLETS


def test_resume_bullets_format_is_list_of_strings(client, auth_headers):
    with patch("app.routers.resume.AIService", return_value=_mock_service()):
        response = client.post(
            "/api/resume-bullets",
            json={"description": "worked on the data pipeline project"},
            headers=auth_headers,
        )
    bullets = _done(response)["bullets"]
    assert isinstance(bullets, list)
    assert 1 <= len(bullets) <= 5
    assert all(isinstance(b, str) and len(b) > 0 for b in bullets)


def test_resume_bullets_requires_auth_header(client):
    response = client.post("/api/resume-bullets", json={"description": "worked on the data pipeline project"})
    assert response.status_code == 401


def test_resume_bullets_empty_description_returns_422(client, auth_headers):
    response = client.post("/api/resume-bullets", json={"description": "   "}, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["detail"] == "Please paste some text first"


def test_resume_bullets_over_length_limit_returns_422(client, auth_headers):
    response = client.post(
        "/api/resume-bullets",
        json={"description": "x" * (MAX_INPUT_CHARS + 1)},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_resume_bullets_missing_api_key_returns_500(client, auth_headers, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post(
        "/api/resume-bullets",
        json={"description": "worked on the data pipeline project"},
        headers=auth_headers,
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "API key not configured"


def test_resume_bullets_ai_error_returns_502(client, auth_headers):
    with patch("app.routers.resume.AIService", return_value=_error_service()):
        response = client.post(
            "/api/resume-bullets",
            json={"description": "worked on the data pipeline project"},
            headers=auth_headers,
        )
    assert response.status_code == 502
    assert response.json()["detail"] == "AI service unavailable"

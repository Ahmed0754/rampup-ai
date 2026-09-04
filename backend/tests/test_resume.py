from unittest.mock import MagicMock, patch

from app.services.ai import AIServiceError

BULLETS = [
    "Built a data pipeline that reduced processing time by 40%",
    "Shipped 12 pull requests across 3 microservices",
    "Mentored 2 new interns on the onboarding process",
]


def _mock_service(bullets=None):
    mock = MagicMock()
    mock.generate_resume_bullets.return_value = bullets if bullets is not None else BULLETS
    return mock


def test_resume_bullets_endpoint_returns_bullets(client):
    with patch("app.routers.resume.AIService", return_value=_mock_service()):
        response = client.post("/api/resume-bullets", json={"description": "worked on the data pipeline project"})
    assert response.status_code == 200
    assert response.json()["bullets"] == BULLETS


def test_resume_bullets_format_is_list_of_strings(client):
    with patch("app.routers.resume.AIService", return_value=_mock_service()):
        response = client.post("/api/resume-bullets", json={"description": "worked on the data pipeline project"})
    bullets = response.json()["bullets"]
    assert isinstance(bullets, list)
    assert 1 <= len(bullets) <= 5
    assert all(isinstance(b, str) and len(b) > 0 for b in bullets)


def test_resume_bullets_empty_description_returns_422(client):
    response = client.post("/api/resume-bullets", json={"description": "   "})
    assert response.status_code == 422
    assert response.json()["detail"] == "Please paste some text first"


def test_resume_bullets_missing_api_key_returns_500(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/resume-bullets", json={"description": "worked on the data pipeline project"})
    assert response.status_code == 500
    assert response.json()["detail"] == "API key not configured"


def test_resume_bullets_ai_error_returns_502(client):
    mock = MagicMock()
    mock.generate_resume_bullets.side_effect = AIServiceError("AI service unavailable")
    with patch("app.routers.resume.AIService", return_value=mock):
        response = client.post("/api/resume-bullets", json={"description": "worked on the data pipeline project"})
    assert response.status_code == 502
    assert response.json()["detail"] == "AI service unavailable"

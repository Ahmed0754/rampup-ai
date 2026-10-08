from unittest.mock import MagicMock, patch

from app.services.ai import AIServiceError

ENTRIES = [
    {"week_start": "2026-06-01", "entry_type": "learned", "entry_text": "How our deploy pipeline works"},
    {"week_start": "2026-06-01", "entry_type": "win", "entry_text": "Shipped my first PR"},
    {"week_start": "2026-06-08", "entry_type": "blocker", "entry_text": "Flaky integration tests"},
]

RECAP = {
    "headline": "Grew from first PR to owning a feature.",
    "highlights": ["Shipped the export feature"],
    "skills_learned": ["CI/CD"],
    "challenges_overcome": ["Stabilised flaky tests"],
    "resume_bullets": ["Built X"],
    "talking_points": ["Ready for more ownership"],
}


def _mock_service(result=RECAP):
    mock = MagicMock()
    mock.generate_internship_recap.return_value = result
    return mock


def test_recap_returns_recap_and_coverage(client, auth_headers):
    service = _mock_service()
    with (
        patch("app.routers.progress.get_all_progress_entries", return_value=ENTRIES),
        patch("app.routers.progress.AIService", return_value=service),
    ):
        response = client.post("/api/progress/recap", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["recap"] == RECAP
    assert body["first_week"] == "2026-06-01"
    assert body["last_week"] == "2026-06-08"
    assert body["weeks_covered"] == 2
    assert body["entry_count"] == 3
    sent = service.generate_internship_recap.call_args.args[0]
    assert sent[0] == {"week_start": "2026-06-01", "type": "learned", "text": "How our deploy pipeline works"}


def test_recap_queries_only_the_current_user(client, auth_headers):
    with (
        patch("app.routers.progress.get_all_progress_entries", return_value=ENTRIES) as mock_get,
        patch("app.routers.progress.AIService", return_value=_mock_service()),
    ):
        client.post("/api/progress/recap", headers=auth_headers)

    mock_get.assert_called_once_with(user_id="test-user-id")


def test_recap_422_when_nothing_logged(client, auth_headers):
    with patch("app.routers.progress.get_all_progress_entries", return_value=[]):
        response = client.post("/api/progress/recap", headers=auth_headers)
    assert response.status_code == 422


def test_recap_drops_oldest_entries_past_the_budget(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.routers.progress.RECAP_MAX_CHARS", 50)
    entries = [
        {"week_start": "2026-06-01", "entry_type": "win", "entry_text": "a" * 40},
        {"week_start": "2026-06-08", "entry_type": "win", "entry_text": "b" * 30},
        {"week_start": "2026-06-15", "entry_type": "win", "entry_text": "c" * 15},
    ]
    service = _mock_service()
    with (
        patch("app.routers.progress.get_all_progress_entries", return_value=entries),
        patch("app.routers.progress.AIService", return_value=service),
    ):
        body = client.post("/api/progress/recap", headers=auth_headers).json()

    sent = service.generate_internship_recap.call_args.args[0]
    assert [e["text"][0] for e in sent] == ["b", "c"]
    assert body["first_week"] == "2026-06-08"
    assert body["entry_count"] == 2


def test_recap_keeps_a_single_oversized_entry(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.routers.progress.RECAP_MAX_CHARS", 10)
    entries = [{"week_start": "2026-06-01", "entry_type": "win", "entry_text": "x" * 100}]
    service = _mock_service()
    with (
        patch("app.routers.progress.get_all_progress_entries", return_value=entries),
        patch("app.routers.progress.AIService", return_value=service),
    ):
        response = client.post("/api/progress/recap", headers=auth_headers)

    assert response.status_code == 200
    assert len(service.generate_internship_recap.call_args.args[0]) == 1


def test_recap_maps_ai_errors_to_502(client, auth_headers):
    service = MagicMock()
    service.generate_internship_recap.side_effect = AIServiceError("AI service unavailable")
    with (
        patch("app.routers.progress.get_all_progress_entries", return_value=ENTRIES),
        patch("app.routers.progress.AIService", return_value=service),
    ):
        response = client.post("/api/progress/recap", headers=auth_headers)
    assert response.status_code == 502


def test_recap_requires_auth(client):
    assert client.post("/api/progress/recap").status_code == 401

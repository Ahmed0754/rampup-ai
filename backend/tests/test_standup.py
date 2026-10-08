from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.services.ai import AIServiceError

R = "app.routers.standup"

ENTRIES = [
    {"entry_type": "task_completed", "entry_text": "Fixed the flaky webhook test", "created_at": "x"},
    {"entry_type": "blocker", "entry_text": "Waiting on staging DB access", "created_at": "x"},
]
PASTES = [{"raw_text": "can you pick up PLAT-482? " + "x" * 1000, "explanation": "e",
           "action_items": ["Read PLAT-482"], "created_at": "x"}]
RESULT = {"yesterday": ["Fixed the flaky webhook test"], "today": ["Pick up PLAT-482"],
          "blockers": ["Waiting on staging DB access"]}


def _since(hours_ago=20):
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def _service(result=RESULT):
    mock = MagicMock()
    mock.generate_standup.return_value = result
    return mock


def test_standup_returns_sections_and_counts(client, auth_headers):
    service = _service()
    with (
        patch(f"{R}.get_progress_entries_since", return_value=ENTRIES),
        patch(f"{R}.get_pastes_since", return_value=PASTES),
        patch(f"{R}.AIService", return_value=service),
    ):
        response = client.post("/api/standup", json={"since": _since(), "notes": "  pairing with Priya  "},
                               headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {**RESULT, "entry_count": 2, "paste_count": 1}
    entries, pastes, notes = service.generate_standup.call_args.args
    assert entries[0] == {"type": "task_completed", "text": "Fixed the flaky webhook test"}
    assert len(pastes[0]["text"]) == 400
    assert pastes[0]["action_items"] == ["Read PLAT-482"]
    assert notes == "pairing with Priya"


def test_standup_queries_from_the_given_time_for_the_current_user(client, auth_headers):
    since = "2026-10-07T00:00:00-04:00"
    fake_now = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
    with (
        patch(f"{R}.datetime") as mock_dt,
        patch(f"{R}.get_progress_entries_since", return_value=ENTRIES) as mock_entries,
        patch(f"{R}.get_pastes_since", return_value=[]) as mock_pastes,
        patch(f"{R}.AIService", return_value=_service()),
    ):
        mock_dt.now.return_value = fake_now
        client.post("/api/standup", json={"since": since}, headers=auth_headers)

    mock_entries.assert_called_once_with("test-user-id", "2026-10-07T00:00:00-04:00")
    mock_pastes.assert_called_once_with("test-user-id", "2026-10-07T00:00:00-04:00")


def test_standup_caps_lookback_at_seven_days(client, auth_headers):
    with (
        patch(f"{R}.get_progress_entries_since", return_value=ENTRIES) as mock_entries,
        patch(f"{R}.get_pastes_since", return_value=[]),
        patch(f"{R}.AIService", return_value=_service()),
    ):
        client.post("/api/standup", json={"since": _since(hours_ago=24 * 30)}, headers=auth_headers)

    used = datetime.fromisoformat(mock_entries.call_args.args[1])
    assert timedelta(days=6, hours=23) < datetime.now(timezone.utc) - used <= timedelta(days=7, minutes=1)


def test_standup_with_only_notes_still_works(client, auth_headers):
    with (
        patch(f"{R}.get_progress_entries_since", return_value=[]),
        patch(f"{R}.get_pastes_since", return_value=[]),
        patch(f"{R}.AIService", return_value=_service()),
    ):
        response = client.post("/api/standup", json={"since": _since(), "notes": "Starting the export ticket"},
                               headers=auth_headers)
    assert response.status_code == 200


def test_standup_422_when_nothing_to_report(client, auth_headers):
    with (
        patch(f"{R}.get_progress_entries_since", return_value=[]),
        patch(f"{R}.get_pastes_since", return_value=[]),
        patch(f"{R}.AIService") as mock_service,
    ):
        response = client.post("/api/standup", json={"since": _since(), "notes": "   "}, headers=auth_headers)
    assert response.status_code == 422
    mock_service.assert_not_called()


def test_standup_rejects_naive_and_future_since(client, auth_headers):
    naive = client.post("/api/standup", json={"since": "2026-10-07T00:00:00"}, headers=auth_headers)
    future = client.post("/api/standup", json={"since": _since(hours_ago=-5)}, headers=auth_headers)
    assert naive.status_code == 422
    assert future.status_code == 422


def test_standup_maps_ai_errors_to_502(client, auth_headers):
    service = MagicMock()
    service.generate_standup.side_effect = AIServiceError("AI service unavailable")
    with (
        patch(f"{R}.get_progress_entries_since", return_value=ENTRIES),
        patch(f"{R}.get_pastes_since", return_value=[]),
        patch(f"{R}.AIService", return_value=service),
    ):
        response = client.post("/api/standup", json={"since": _since()}, headers=auth_headers)
    assert response.status_code == 502


def test_standup_requires_auth(client):
    assert client.post("/api/standup", json={"since": _since()}).status_code == 401

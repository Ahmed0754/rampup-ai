from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.nudge import (
    NudgeConfigError,
    build_email_html,
    current_week_start,
    has_logged_this_week,
    list_all_users,
    run,
    send_email,
)


def test_current_week_start_is_the_preceding_or_same_monday():
    # Wednesday 2026-09-09 -> Monday 2026-09-07
    assert current_week_start(date(2026, 9, 9)) == "2026-09-07"
    # A Monday should map to itself
    assert current_week_start(date(2026, 9, 7)) == "2026-09-07"


def _user(id_, email):
    return SimpleNamespace(id=id_, email=email)


def test_list_all_users_pages_until_a_short_page():
    client = MagicMock()
    page1 = [_user(str(i), f"u{i}@example.com") for i in range(200)]
    page2 = [_user("200", "u200@example.com")]
    client.auth.admin.list_users.side_effect = [page1, page2]

    users = list_all_users(client)

    assert len(users) == 201
    assert client.auth.admin.list_users.call_count == 2


def test_list_all_users_stops_immediately_on_empty_first_page():
    client = MagicMock()
    client.auth.admin.list_users.return_value = []
    assert list_all_users(client) == []


def test_has_logged_this_week_true_and_false():
    client = MagicMock()
    query = client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value
    query.execute.return_value = SimpleNamespace(count=3)
    assert has_logged_this_week(client, "user-1", "2026-09-07") is True

    query.execute.return_value = SimpleNamespace(count=0)
    assert has_logged_this_week(client, "user-1", "2026-09-07") is False


def test_build_email_html_includes_link_only_when_app_url_set():
    assert "href" not in build_email_html("")
    assert 'href="https://example.com/progress"' in build_email_html("https://example.com")


def test_send_email_posts_to_resend_and_raises_on_error(monkeypatch):
    mock_post = MagicMock()
    mock_post.return_value.raise_for_status.side_effect = None
    monkeypatch.setattr("app.services.nudge.httpx.post", mock_post)

    send_email("key-123", "a@example.com", "Subject", "<p>hi</p>")

    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer key-123"
    assert kwargs["json"]["to"] == ["a@example.com"]


def test_run_raises_when_supabase_not_configured(monkeypatch):
    monkeypatch.setattr("app.services.nudge.get_supabase", lambda: None)
    with pytest.raises(NudgeConfigError):
        run()


def test_run_raises_when_resend_key_missing(monkeypatch):
    monkeypatch.setattr("app.services.nudge.get_supabase", lambda: MagicMock())
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    with pytest.raises(NudgeConfigError):
        run()


def test_run_sends_only_to_users_without_entries_this_week(monkeypatch):
    monkeypatch.setattr("app.services.nudge.get_supabase", lambda: MagicMock())
    monkeypatch.setenv("RESEND_API_KEY", "key-123")

    already_logged = _user("u1", "logged@example.com")
    needs_nudge = _user("u2", "quiet@example.com")
    no_email = _user("u3", None)

    with (
        patch("app.services.nudge.list_all_users", return_value=[already_logged, needs_nudge, no_email]),
        patch("app.services.nudge.has_logged_this_week", side_effect=lambda c, uid, ws: uid == "u1"),
        patch("app.services.nudge.send_email") as mock_send,
    ):
        summary = run()

    mock_send.assert_called_once()
    assert mock_send.call_args.args[1] == "quiet@example.com"
    assert summary["sent"] == ["quiet@example.com"]
    assert summary["skipped"] == ["logged@example.com"]
    assert summary["failed"] == []


def test_run_records_failures_without_raising(monkeypatch):
    monkeypatch.setattr("app.services.nudge.get_supabase", lambda: MagicMock())
    monkeypatch.setenv("RESEND_API_KEY", "key-123")
    needs_nudge = _user("u1", "quiet@example.com")

    with (
        patch("app.services.nudge.list_all_users", return_value=[needs_nudge]),
        patch("app.services.nudge.has_logged_this_week", return_value=False),
        patch("app.services.nudge.send_email", side_effect=RuntimeError("boom")),
    ):
        summary = run()

    assert summary["failed"] == ["quiet@example.com"]
    assert summary["sent"] == []

import logging
import os
from datetime import date, timedelta

import httpx

from app.services.supabase import get_supabase

logger = logging.getLogger("rampup.nudge")

RESEND_API_URL = "https://api.resend.com/emails"
DEFAULT_FROM = "RampUp AI <onboarding@resend.dev>"
LIST_USERS_PAGE_SIZE = 200


class NudgeConfigError(Exception):
    pass


def current_week_start(today: date | None = None) -> str:
    """Monday of the current week, matching the frontend's getCurrentWeekStart()."""
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat()


def list_all_users(client) -> list:
    """Page through every Supabase Auth user."""
    users = []
    page = 1
    while True:
        batch = client.auth.admin.list_users(page=page, per_page=LIST_USERS_PAGE_SIZE)
        if not batch:
            break
        users.extend(batch)
        if len(batch) < LIST_USERS_PAGE_SIZE:
            break
        page += 1
    return users


def has_logged_this_week(client, user_id: str, week_start: str) -> bool:
    result = (
        client.table("progress_entries")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("week_start", week_start)
        .limit(1)
        .execute()
    )
    return (result.count or 0) > 0


def build_email_html(app_url: str) -> str:
    cta = f'<p><a href="{app_url}/progress">Log this week\'s progress &rarr;</a></p>' if app_url else ""
    return (
        "<p>Hey — quick nudge from RampUp AI.</p>"
        "<p>You haven't logged anything for this week yet. Take two minutes to jot down a win, "
        "something you learned, or a blocker — future you (and your resume) will thank you.</p>"
        f"{cta}"
    )


def send_email(api_key: str, to: str, subject: str, html: str, from_email: str = DEFAULT_FROM) -> None:
    response = httpx.post(
        RESEND_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"from": from_email, "to": [to], "subject": subject, "html": html},
        timeout=15,
    )
    response.raise_for_status()


def run() -> dict:
    """Email everyone who hasn't logged progress this week yet. Returns a summary."""
    client = get_supabase()
    if client is None:
        raise NudgeConfigError("Supabase is not configured (SUPABASE_URL / SUPABASE_SERVICE_KEY)")

    resend_key = os.environ.get("RESEND_API_KEY")
    if not resend_key:
        raise NudgeConfigError("RESEND_API_KEY is not configured")

    from_email = os.environ.get("REMINDER_FROM_EMAIL") or DEFAULT_FROM
    app_url = (os.environ.get("FRONTEND_URL") or "").rstrip("/")
    week_start = current_week_start()
    html = build_email_html(app_url)

    sent, skipped, failed = [], [], []
    for user in list_all_users(client):
        if not user.email:
            continue
        if has_logged_this_week(client, user.id, week_start):
            skipped.append(user.email)
            continue
        try:
            send_email(resend_key, user.email, "Don't forget to log this week's progress", html, from_email)
            sent.append(user.email)
        except Exception:
            logger.exception("Failed to send nudge email to %s", user.email)
            failed.append(user.email)

    return {"week_start": week_start, "sent": sent, "skipped": skipped, "failed": failed}

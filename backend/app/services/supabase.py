import logging
import os

from supabase import Client, create_client

logger = logging.getLogger("rampup.supabase")

_client: Client | None = None


def get_supabase() -> Client | None:
    global _client
    if _client is not None:
        return _client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        logger.warning("Supabase not configured; skipping persistence")
        return None
    _client = create_client(url, key)
    return _client


def save_paste(user_id: str, raw_text: str, input_type: str, explanation: str, action_items: list[str]) -> str | None:
    client = get_supabase()
    if client is None:
        return None
    try:
        result = (
            client.table("pastes")
            .insert(
                {
                    "user_id": user_id,
                    "raw_text": raw_text,
                    "input_type": input_type,
                    "explanation": explanation,
                    "action_items": action_items,
                }
            )
            .execute()
        )
        return result.data[0]["id"] if result.data else None
    except Exception:
        logger.exception("Failed to save paste to Supabase")
        return None


def save_reply(user_id: str, original_text: str, tone: str, reply_text: str, paste_id: str | None) -> str | None:
    client = get_supabase()
    if client is None:
        return None
    try:
        result = (
            client.table("replies")
            .insert(
                {
                    "user_id": user_id,
                    "original_text": original_text,
                    "tone": tone,
                    "reply_text": reply_text,
                    "paste_id": paste_id,
                }
            )
            .execute()
        )
        return result.data[0]["id"] if result.data else None
    except Exception:
        logger.exception("Failed to save reply to Supabase")
        return None


def save_progress_entry(user_id: str, entry_text: str, entry_type: str, week_start: str) -> dict | None:
    client = get_supabase()
    if client is None:
        return None
    try:
        result = (
            client.table("progress_entries")
            .insert(
                {
                    "user_id": user_id,
                    "entry_text": entry_text,
                    "entry_type": entry_type,
                    "week_start": week_start,
                }
            )
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception:
        logger.exception("Failed to save progress entry to Supabase")
        return None


def get_progress_entries(user_id: str, week_start: str) -> list[dict]:
    client = get_supabase()
    if client is None:
        return []
    try:
        result = (
            client.table("progress_entries")
            .select("*")
            .eq("user_id", user_id)
            .eq("week_start", week_start)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []
    except Exception:
        logger.exception("Failed to fetch progress entries from Supabase")
        return []


def save_weekly_summary(user_id: str, week_start: str, summary: dict) -> str | None:
    client = get_supabase()
    if client is None:
        return None
    try:
        result = (
            client.table("weekly_summaries")
            .insert(
                {
                    "user_id": user_id,
                    "week_start": week_start,
                    "what_i_worked_on": summary.get("what_i_worked_on"),
                    "what_i_learned": summary.get("what_i_learned"),
                    "blockers": summary.get("blockers"),
                    "resume_bullets": summary.get("resume_bullets"),
                    "talking_points": summary.get("talking_points"),
                }
            )
            .execute()
        )
        return result.data[0]["id"] if result.data else None
    except Exception:
        logger.exception("Failed to save weekly summary to Supabase")
        return None

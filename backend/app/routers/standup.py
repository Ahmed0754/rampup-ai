from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user_id
from app.models import StandupRequest, StandupResponse
from app.services.ai import AIService, AIServiceError
from app.services.supabase import get_pastes_since, get_progress_entries_since

router = APIRouter()

# Standup covers "since your last workday" - never more than this, even after a long break.
MAX_LOOKBACK = timedelta(days=7)
# Pasted messages can be long logs; only the gist is needed for a standup line.
PASTE_PREVIEW_CHARS = 400


@router.post("/standup", response_model=StandupResponse)
def generate_standup(payload: StandupRequest, user_id: str = Depends(get_current_user_id)):
    if payload.since.tzinfo is None:
        raise HTTPException(status_code=422, detail="since must include a timezone offset")
    now = datetime.now(timezone.utc)
    if payload.since > now:
        raise HTTPException(status_code=422, detail="since can't be in the future")
    since = max(payload.since, now - MAX_LOOKBACK).isoformat()

    notes = (payload.notes or "").strip()
    entries = [{"type": e["entry_type"], "text": e["entry_text"]} for e in get_progress_entries_since(user_id, since)]
    pastes = [
        {"text": p["raw_text"][:PASTE_PREVIEW_CHARS], "action_items": p.get("action_items") or []}
        for p in get_pastes_since(user_id, since)
    ]

    if not entries and not pastes and not notes:
        raise HTTPException(
            status_code=422,
            detail="Nothing logged since your last workday - add a note about what you're working on",
        )

    try:
        service = AIService()
        result = service.generate_standup(entries, pastes, notes)
    except AIServiceError as exc:
        message = str(exc)
        status_code = 500 if message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    return StandupResponse(**result, entry_count=len(entries), paste_count=len(pastes))

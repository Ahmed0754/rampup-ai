from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user_id
from app.models import (
    ProgressEntryCreate,
    ProgressEntryResponse,
    ProgressListResponse,
    WeeklySummary,
    WeeklySummaryRequest,
    WeeklySummaryResponse,
)
from app.services.ai import AIService, AIServiceError
from app.services.supabase import (
    get_progress_entries,
    save_progress_entry,
    save_weekly_summary,
)

router = APIRouter()

VALID_ENTRY_TYPES = {"win", "learned", "blocker", "task_completed"}


@router.post("/progress", response_model=ProgressEntryResponse)
def create_progress_entry(payload: ProgressEntryCreate, user_id: str = Depends(get_current_user_id)):
    entry_text = payload.entry_text.strip()
    if not entry_text:
        raise HTTPException(status_code=422, detail="Please paste some text first")

    saved = save_progress_entry(
        user_id=user_id,
        entry_text=entry_text,
        entry_type=payload.entry_type,
        week_start=payload.week_start,
    )

    if saved is None:
        raise HTTPException(status_code=502, detail="Could not save progress entry")

    return ProgressEntryResponse(id=saved["id"], created_at=saved["created_at"])


@router.get("/progress", response_model=ProgressListResponse)
def list_progress_entries(week_start: str, user_id: str = Depends(get_current_user_id)):
    entries = get_progress_entries(user_id=user_id, week_start=week_start)
    return ProgressListResponse(entries=entries)


@router.post("/progress/summary", response_model=WeeklySummaryResponse)
def generate_weekly_summary(payload: WeeklySummaryRequest, user_id: str = Depends(get_current_user_id)):
    entries = get_progress_entries(user_id=user_id, week_start=payload.week_start)
    if not entries:
        raise HTTPException(status_code=422, detail="No progress entries found for this week")

    try:
        service = AIService()
        result = service.generate_weekly_summary(entries)
    except AIServiceError as exc:
        message = str(exc)
        status_code = 500 if message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    summary = WeeklySummary(
        what_i_worked_on=result.get("what_i_worked_on", ""),
        what_i_learned=result.get("what_i_learned", ""),
        blockers=result.get("blockers", "None this week"),
        resume_bullets=result.get("resume_bullets", []),
        talking_points=result.get("talking_points", ""),
    )

    save_weekly_summary(user_id=user_id, week_start=payload.week_start, summary=summary.model_dump())

    return WeeklySummaryResponse(summary=summary)

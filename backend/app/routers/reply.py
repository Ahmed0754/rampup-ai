from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user_id
from app.models import ReplyRequest, ReplyResponse
from app.services.ai import AIService, AIServiceError
from app.services.supabase import save_reply

router = APIRouter()

VALID_TONES = {"casual", "professional", "manager-safe", "confused-but-trying"}


@router.post("/reply", response_model=ReplyResponse)
def generate_reply(payload: ReplyRequest, user_id: str = Depends(get_current_user_id)):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Please paste some text first")

    if payload.tone not in VALID_TONES:
        raise HTTPException(status_code=422, detail=f"Invalid tone. Must be one of: {', '.join(sorted(VALID_TONES))}")

    try:
        service = AIService()
        reply_text = service.generate_reply(text, payload.tone)
    except AIServiceError as exc:
        message = str(exc)
        status_code = 500 if message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    save_reply(
        user_id=user_id,
        original_text=text,
        tone=payload.tone,
        reply_text=reply_text,
        paste_id=payload.paste_id,
    )

    return ReplyResponse(reply=reply_text, tone=payload.tone)

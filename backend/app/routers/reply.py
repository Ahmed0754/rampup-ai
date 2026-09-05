from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user_id
from app.models import ReplyRequest
from app.services.ai import AIService, AIServiceError
from app.services.supabase import save_reply
from app.streaming import stream_ndjson

router = APIRouter()

VALID_TONES = {"casual", "professional", "manager-safe", "confused-but-trying"}


@router.post("/reply")
def generate_reply(payload: ReplyRequest, user_id: str = Depends(get_current_user_id)):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Please paste some text first")

    if payload.tone not in VALID_TONES:
        raise HTTPException(status_code=422, detail=f"Invalid tone. Must be one of: {', '.join(sorted(VALID_TONES))}")

    try:
        service = AIService()
    except AIServiceError as exc:
        message = str(exc)
        status_code = 500 if message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    def finalize(full_text: str) -> dict:
        reply_text = full_text.strip()
        reply_id = save_reply(
            user_id=user_id,
            original_text=text,
            tone=payload.tone,
            reply_text=reply_text,
            paste_id=payload.paste_id,
        )
        return {"reply": reply_text, "tone": payload.tone, "saved": reply_id is not None}

    return stream_ndjson(service.generate_reply_stream(text, payload.tone), finalize)

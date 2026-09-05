from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user_id
from app.models import ResumeBulletsRequest
from app.services.ai import AIService, AIServiceError, parse_bullet_lines
from app.services.supabase import save_resume_bullets
from app.streaming import stream_ndjson

router = APIRouter()


@router.post("/resume-bullets")
def generate_resume_bullets(payload: ResumeBulletsRequest, user_id: str = Depends(get_current_user_id)):
    description = payload.description.strip()
    if not description:
        raise HTTPException(status_code=422, detail="Please paste some text first")

    try:
        service = AIService()
    except AIServiceError as exc:
        message = str(exc)
        status_code = 500 if message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    def finalize(full_text: str) -> dict:
        bullets = parse_bullet_lines(full_text)
        record_id = save_resume_bullets(user_id=user_id, description=description, bullets=bullets)
        return {"bullets": bullets, "saved": record_id is not None}

    return stream_ndjson(service.generate_resume_bullets_stream(description), finalize)

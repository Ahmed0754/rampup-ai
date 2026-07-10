from fastapi import APIRouter, HTTPException

from app.models import ResumeBulletsRequest, ResumeBulletsResponse
from app.services.claude import ClaudeService, ClaudeServiceError

router = APIRouter()


@router.post("/resume-bullets", response_model=ResumeBulletsResponse)
def generate_resume_bullets(payload: ResumeBulletsRequest):
    description = payload.description.strip()
    if not description:
        raise HTTPException(status_code=422, detail="Please paste some text first")

    try:
        service = ClaudeService()
        bullets = service.generate_resume_bullets(description)
    except ClaudeServiceError as exc:
        message = str(exc)
        status_code = 500 if message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    return ResumeBulletsResponse(bullets=bullets)

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user_id
from app.models import ExplainRequest, ExplainResponse
from app.services.ai import AIService, AIServiceError
from app.services.classifier import classify_input
from app.services.supabase import save_paste

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
def explain(payload: ExplainRequest, user_id: str = Depends(get_current_user_id)):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Please paste some text first")

    input_type = classify_input(text)

    try:
        service = AIService()
        result = service.explain(text, input_type)
    except AIServiceError as exc:
        message = str(exc)
        status_code = 500 if message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    paste_id = save_paste(
        user_id=user_id,
        raw_text=text,
        input_type=input_type,
        explanation=result.get("explanation", ""),
        action_items=result.get("action_items", []),
    )

    return ExplainResponse(
        input_type=input_type,
        explanation=result.get("explanation", ""),
        what_they_mean=result.get("what_they_mean", ""),
        what_to_do_next=result.get("what_to_do_next", ""),
        action_items=result.get("action_items", []),
        paste_id=paste_id,
        saved=paste_id is not None,
    )

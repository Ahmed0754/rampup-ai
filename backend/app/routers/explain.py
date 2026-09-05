from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user_id
from app.models import ExplainRequest
from app.services.ai import AIService, AIServiceError, parse_explain_sections
from app.services.classifier import classify_input
from app.services.supabase import save_paste
from app.streaming import stream_ndjson

router = APIRouter()


@router.post("/explain")
def explain(payload: ExplainRequest, user_id: str = Depends(get_current_user_id)):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Please paste some text first")

    input_type = classify_input(text)

    try:
        service = AIService()
    except AIServiceError as exc:
        message = str(exc)
        status_code = 500 if message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    def finalize(full_text: str) -> dict:
        result = parse_explain_sections(full_text)
        paste_id = save_paste(
            user_id=user_id,
            raw_text=text,
            input_type=input_type,
            explanation=result["explanation"],
            action_items=result["action_items"],
        )
        return {
            "input_type": input_type,
            **result,
            "paste_id": paste_id,
            "saved": paste_id is not None,
        }

    return stream_ndjson(service.explain_stream(text, input_type), finalize)

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user_id
from app.models import ExplainChatRequest, ExplainRequest
from app.services.ai import AIService, AIServiceError, parse_explain_sections
from app.services.classifier import classify_input
from app.services.supabase import (
    get_explain_chat_messages,
    get_paste,
    save_explain_chat_message,
    save_paste,
)
from app.streaming import stream_ndjson

router = APIRouter()

# How many prior chat turns to feed back as context. Keeps the prompt (and
# cost) bounded on a long-running follow-up conversation.
MAX_CHAT_HISTORY = 10


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


@router.post("/explain/chat")
def explain_chat(payload: ExplainChatRequest, user_id: str = Depends(get_current_user_id)):
    question = payload.message.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Please enter a question")

    paste = get_paste(payload.paste_id, user_id)
    if paste is None:
        raise HTTPException(status_code=404, detail="Original explanation not found")

    history = get_explain_chat_messages(payload.paste_id, user_id)[-MAX_CHAT_HISTORY:]

    try:
        service = AIService()
    except AIServiceError as exc:
        error_message = str(exc)
        status_code = 500 if error_message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=error_message) from exc

    # Save the question immediately so it's preserved even if generation fails.
    save_explain_chat_message(user_id=user_id, paste_id=payload.paste_id, role="user", content=question)

    def finalize(full_text: str) -> dict:
        reply = full_text.strip()
        reply_id = save_explain_chat_message(
            user_id=user_id, paste_id=payload.paste_id, role="assistant", content=reply
        )
        return {"reply": reply, "saved": reply_id is not None}

    return stream_ndjson(
        service.chat_stream(paste["raw_text"], paste.get("explanation") or "", history, question),
        finalize,
    )

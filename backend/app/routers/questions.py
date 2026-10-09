from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response

from app.deps import get_current_user_id
from app.models import (
    MentorQuestion,
    MentorQuestionListResponse,
    MentorQuestionsCreate,
    MentorQuestionSuggestRequest,
    MentorQuestionSuggestResponse,
    MentorQuestionUpdate,
)
from app.services.ai import AIService, AIServiceError
from app.services.supabase import (
    delete_mentor_question,
    get_explain_chat_messages,
    get_mentor_questions,
    get_paste,
    save_mentor_questions,
    update_mentor_question,
)

router = APIRouter()

# Same bound as the Explain follow-up chat: enough context, bounded prompt.
MAX_CHAT_HISTORY = 10


@router.get("/questions", response_model=MentorQuestionListResponse)
def list_questions(user_id: str = Depends(get_current_user_id)):
    questions = get_mentor_questions(user_id)
    if questions is None:
        raise HTTPException(status_code=502, detail="Could not load your questions")
    return MentorQuestionListResponse(questions=questions)


@router.post("/questions", response_model=MentorQuestionListResponse)
def add_questions(payload: MentorQuestionsCreate, user_id: str = Depends(get_current_user_id)):
    owned_pastes: dict[str, bool] = {}
    to_save = []
    for item in payload.questions:
        question = item.question.strip()
        if not question:
            raise HTTPException(status_code=422, detail="Questions can't be blank")

        paste_id = item.paste_id
        if paste_id is not None:
            if paste_id not in owned_pastes:
                owned_pastes[paste_id] = get_paste(paste_id, user_id) is not None
            if not owned_pastes[paste_id]:
                paste_id = None

        context = (item.context or "").strip() or None
        to_save.append({"question": question, "context": context, "paste_id": paste_id})

    saved = save_mentor_questions(user_id, to_save)
    if saved is None:
        raise HTTPException(status_code=502, detail="Could not save your questions")
    return MentorQuestionListResponse(questions=saved)


@router.patch("/questions/{question_id}", response_model=MentorQuestion)
def edit_question(question_id: str, payload: MentorQuestionUpdate, user_id: str = Depends(get_current_user_id)):
    changes: dict = {}
    if payload.question is not None:
        if not payload.question.strip():
            raise HTTPException(status_code=422, detail="Questions can't be blank")
        changes["question"] = payload.question.strip()
    if payload.answer is not None:
        changes["answer"] = payload.answer.strip() or None
    if payload.answered is True:
        changes["answered_at"] = datetime.now(timezone.utc).isoformat()
    elif payload.answered is False:
        changes["answered_at"] = None
        changes["answer"] = None
    if not changes:
        raise HTTPException(status_code=422, detail="Nothing to update")

    updated = update_mentor_question(user_id, question_id, changes)
    if updated is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return updated


@router.delete("/questions/{question_id}", status_code=204)
def remove_question(question_id: str, user_id: str = Depends(get_current_user_id)):
    if not delete_mentor_question(user_id, question_id):
        raise HTTPException(status_code=404, detail="Question not found")
    return Response(status_code=204)


@router.post("/questions/suggest", response_model=MentorQuestionSuggestResponse)
def suggest_questions(payload: MentorQuestionSuggestRequest, user_id: str = Depends(get_current_user_id)):
    paste = get_paste(payload.paste_id, user_id)
    if paste is None:
        raise HTTPException(status_code=404, detail="Original explanation not found")

    chat = get_explain_chat_messages(payload.paste_id, user_id)[-MAX_CHAT_HISTORY:]
    # Suggestions aren't saved, so if the list fails to load we just can't steer
    # away from questions the user already has.
    open_questions = [q["question"] for q in (get_mentor_questions(user_id) or []) if not q.get("answered_at")]

    try:
        service = AIService()
        suggestions = service.suggest_mentor_questions(
            paste["raw_text"], paste.get("explanation") or "", chat, open_questions
        )
    except AIServiceError as exc:
        message = str(exc)
        status_code = 500 if message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    return MentorQuestionSuggestResponse(suggestions=suggestions)

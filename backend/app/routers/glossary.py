from fastapi import APIRouter, Depends, HTTPException, Response

from app.deps import get_current_user_id
from app.models import (
    GlossaryListResponse,
    GlossarySaveResponse,
    GlossarySuggestRequest,
    GlossarySuggestResponse,
    GlossaryTerm,
    GlossaryTermsCreate,
    GlossaryTermUpdate,
)
from app.services.ai import AIService, AIServiceError
from app.services.supabase import (
    delete_glossary_term,
    get_glossary_terms,
    get_paste,
    save_glossary_terms,
    update_glossary_term,
)

router = APIRouter()


def _known_terms(user_id: str) -> list[dict]:
    terms = get_glossary_terms(user_id)
    if terms is None:
        raise HTTPException(status_code=502, detail="Could not load your glossary")
    return terms


@router.get("/glossary", response_model=GlossaryListResponse)
def list_glossary(user_id: str = Depends(get_current_user_id)):
    return GlossaryListResponse(terms=_known_terms(user_id))


@router.post("/glossary", response_model=GlossarySaveResponse)
def add_glossary_terms(payload: GlossaryTermsCreate, user_id: str = Depends(get_current_user_id)):
    seen = {t["term"].lower() for t in _known_terms(user_id)}
    owned_pastes: dict[str, bool] = {}
    to_save, skipped = [], []

    for item in payload.terms:
        term, definition = item.term.strip(), item.definition.strip()
        if not term or not definition:
            raise HTTPException(status_code=422, detail="Every term needs a name and a definition")
        if term.lower() in seen:
            skipped.append(term)
            continue
        seen.add(term.lower())

        paste_id = item.paste_id
        if paste_id is not None:
            if paste_id not in owned_pastes:
                owned_pastes[paste_id] = get_paste(paste_id, user_id) is not None
            if not owned_pastes[paste_id]:
                paste_id = None

        context = (item.context or "").strip() or None
        to_save.append({"term": term, "definition": definition, "context": context, "paste_id": paste_id})

    if not to_save:
        return GlossarySaveResponse(saved=[], skipped=skipped)

    saved = save_glossary_terms(user_id, to_save)
    if saved is None:
        raise HTTPException(status_code=502, detail="Could not save to your glossary")
    return GlossarySaveResponse(saved=saved, skipped=skipped)


@router.patch("/glossary/{term_id}", response_model=GlossaryTerm)
def edit_glossary_term(term_id: str, payload: GlossaryTermUpdate, user_id: str = Depends(get_current_user_id)):
    changes = {key: value.strip() for key, value in payload.model_dump(exclude_none=True).items()}
    if not changes or not all(changes.values()):
        raise HTTPException(status_code=422, detail="Nothing to update")

    if "term" in changes:
        clash = any(
            t["id"] != term_id and t["term"].lower() == changes["term"].lower() for t in _known_terms(user_id)
        )
        if clash:
            raise HTTPException(status_code=409, detail=f'"{changes["term"]}" is already in your glossary')

    updated = update_glossary_term(user_id, term_id, changes)
    if updated is None:
        raise HTTPException(status_code=404, detail="Term not found")
    return updated


@router.delete("/glossary/{term_id}", status_code=204)
def remove_glossary_term(term_id: str, user_id: str = Depends(get_current_user_id)):
    if not delete_glossary_term(user_id, term_id):
        raise HTTPException(status_code=404, detail="Term not found")
    return Response(status_code=204)


@router.post("/glossary/suggest", response_model=GlossarySuggestResponse)
def suggest_glossary_terms(payload: GlossarySuggestRequest, user_id: str = Depends(get_current_user_id)):
    paste = get_paste(payload.paste_id, user_id)
    if paste is None:
        raise HTTPException(status_code=404, detail="Original explanation not found")

    # Suggestions aren't saved, so a glossary that fails to load just means
    # we can't pre-filter; saving still dedupes against the real glossary.
    known = [t["term"] for t in (get_glossary_terms(user_id) or [])]

    try:
        service = AIService()
        suggestions = service.suggest_glossary_terms(paste["raw_text"], paste.get("explanation") or "", known)
    except AIServiceError as exc:
        message = str(exc)
        status_code = 500 if message == "API key not configured" else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    seen = {term.lower() for term in known}
    fresh = []
    for suggestion in suggestions:
        if suggestion["term"].lower() not in seen:
            seen.add(suggestion["term"].lower())
            fresh.append(suggestion)
    return GlossarySuggestResponse(suggestions=fresh)

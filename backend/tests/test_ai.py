import json

import pytest

from app.services.ai import AIService, AIServiceError, _as_list, _as_text, _parse_json


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    svc = AIService.__new__(AIService)  # skip __init__ / real client
    return svc


def _stub(svc, payload):
    svc._complete = lambda prompt, json_output=False: json.dumps(payload)


def test_as_text_handles_list_and_scalars():
    assert _as_text(["a", "b"]) == "a\nb"
    assert _as_text("x") == "x"
    assert _as_text(None) == ""
    assert _as_text(3) == "3"


def test_as_list_handles_scalars_and_none():
    assert _as_list(["a", "b"]) == ["a", "b"]
    assert _as_list("a") == ["a"]
    assert _as_list(None) == []
    assert _as_list([1, 2]) == ["1", "2"]


def test_parse_json_rejects_non_object():
    with pytest.raises(AIServiceError):
        _parse_json("[1, 2, 3]")
    with pytest.raises(AIServiceError):
        _parse_json("not json")


def test_parse_json_strips_code_fence():
    assert _parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_weekly_summary_coerces_list_fields_to_strings(service):
    # Gemini often returns bullet-point fields as arrays.
    _stub(
        service,
        {
            "what_i_worked_on": ["shipped export", "fixed tests"],
            "what_i_learned": "RLS",
            "blockers": [],
            "resume_bullets": ["Built X", "Shipped Y"],
            "talking_points": ["point one", "point two"],
        },
    )
    result = service.generate_weekly_summary([{"type": "win", "text": "did a thing"}])
    assert result["what_i_worked_on"] == "shipped export\nfixed tests"
    assert result["blockers"] == "None this week"
    assert result["talking_points"] == "point one\npoint two"
    assert result["resume_bullets"] == ["Built X", "Shipped Y"]


def test_explain_coerces_fields(service):
    _stub(
        service,
        {
            "explanation": ["line one", "line two"],
            "what_they_mean": "they want a fix",
            "what_to_do_next": "run the migration",
            "action_items": "just one string",
        },
    )
    result = service.explain("some error", "error")
    assert result["explanation"] == "line one\nline two"
    assert result["action_items"] == ["just one string"]


def test_resume_bullets_coerces_to_list(service):
    _stub(service, {"bullets": "a single bullet"})
    assert service.generate_resume_bullets("notes") == ["a single bullet"]

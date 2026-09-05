import json

import pytest

from app.services.ai import (
    AIService,
    AIServiceError,
    _as_list,
    _as_text,
    _parse_json,
    parse_bullet_lines,
    parse_explain_sections,
)


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    svc = AIService.__new__(AIService)  # skip __init__ / real client
    return svc


def _stub_complete(svc, payload):
    svc._complete = lambda prompt, json_output=False: json.dumps(payload)


def _stub_stream(svc, chunks):
    svc._stream = lambda prompt: iter(chunks)


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
    _stub_complete(
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


def test_parse_explain_sections_happy_path():
    text = (
        "EXPLANATION: your build failed.\n"
        "WHAT_THEY_MEAN: they want it fixed.\n"
        "WHAT_TO_DO_NEXT: run the migration.\n"
        "ACTION_ITEMS:\n"
        "- do thing one\n"
        "- do thing two\n"
    )
    result = parse_explain_sections(text)
    assert result["explanation"] == "your build failed."
    assert result["what_they_mean"] == "they want it fixed."
    assert result["what_to_do_next"] == "run the migration."
    assert result["action_items"] == ["do thing one", "do thing two"]


def test_parse_explain_sections_handles_wrapped_lines():
    text = (
        "EXPLANATION: this is a long\nexplanation split across lines.\n"
        "WHAT_THEY_MEAN: single line.\n"
        "WHAT_TO_DO_NEXT: single line.\n"
        "ACTION_ITEMS:\n- one item\n"
    )
    result = parse_explain_sections(text)
    assert result["explanation"] == "this is a long explanation split across lines."


def test_parse_explain_sections_falls_back_to_raw_text_when_no_markers():
    result = parse_explain_sections("just a plain sentence with no structure at all")
    assert result["explanation"] == "just a plain sentence with no structure at all"
    assert result["action_items"] == []


def test_parse_bullet_lines_strips_prefixes():
    assert parse_bullet_lines("- one\n* two\n• three\n") == ["one", "two", "three"]


def test_parse_bullet_lines_falls_back_to_whole_text():
    assert parse_bullet_lines("just one long bullet, no dash prefix") == ["just one long bullet, no dash prefix"]


def test_parse_bullet_lines_empty_input():
    assert parse_bullet_lines("") == []


def test_explain_stream_yields_prompted_text(service):
    _stub_stream(service, ["EXPLANATION: hi ", "there"])
    assert list(service.explain_stream("some error", "error")) == ["EXPLANATION: hi ", "there"]


def test_generate_reply_stream_yields_chunks(service):
    _stub_stream(service, ["yeah ", "for sure"])
    assert list(service.generate_reply_stream("ok?", "casual")) == ["yeah ", "for sure"]


def test_generate_resume_bullets_stream_yields_chunks(service):
    _stub_stream(service, ["- built X\n", "- shipped Y\n"])
    assert list(service.generate_resume_bullets_stream("notes")) == ["- built X\n", "- shipped Y\n"]

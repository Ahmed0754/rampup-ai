import json
from unittest.mock import MagicMock

import pytest
from google.genai.errors import APIError

from app.services.ai import (
    AIService,
    AIServiceError,
    _as_list,
    _as_text,
    _groq_complete,
    _groq_stream,
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


def test_standup_normalises_fields(service):
    _stub_complete(service, {"yesterday": "Fixed a test", "today": ["Pick up PLAT-482"]})
    result = service.generate_standup([{"type": "win", "text": "Fixed a test"}], [], "")
    assert result == {"yesterday": ["Fixed a test"], "today": ["Pick up PLAT-482"], "blockers": []}


def test_suggest_mentor_questions_drops_malformed_items(service):
    _stub_complete(
        service,
        {"questions": [
            {"question": "Who owns the payments service?", "context": "ticket mentions it"},
            {"question": "  "},
            "nope",
            {"question": "Is there a staging checklist?"},
        ]},
    )
    result = service.suggest_mentor_questions("text", "explanation", [], [])
    assert result == [
        {"question": "Who owns the payments service?", "context": "ticket mentions it"},
        {"question": "Is there a staging checklist?", "context": None},
    ]


def test_suggest_glossary_terms_drops_malformed_items(service):
    _stub_complete(
        service,
        {
            "terms": [
                {"term": "Feature flag", "definition": "A switch", "context": "behind a flag"},
                {"term": "", "definition": "no name"},
                {"term": "No definition"},
                "not an object",
                {"term": " RLS ", "definition": ["Row level", "security"]},
            ]
        },
    )
    result = service.suggest_glossary_terms("text", "explanation", [])
    assert result == [
        {"term": "Feature flag", "definition": "A switch", "context": "behind a flag"},
        {"term": "RLS", "definition": "Row level\nsecurity", "context": None},
    ]


def test_suggest_glossary_terms_handles_missing_terms_key(service):
    _stub_complete(service, {"something": "else"})
    assert service.suggest_glossary_terms("text", "explanation", ["CI"]) == []


def test_internship_recap_normalises_fields(service):
    _stub_complete(
        service,
        {
            "headline": ["Grew a lot.", "Shipped a feature."],
            "highlights": "Shipped export",
            "skills_learned": ["SQL", "RLS"],
            "resume_bullets": ["Built X"],
            "talking_points": ["Ready for more"],
        },
    )
    result = service.generate_internship_recap([{"week_start": "2026-06-01", "type": "win", "text": "did a thing"}])
    assert result["headline"] == "Grew a lot.\nShipped a feature."
    assert result["highlights"] == ["Shipped export"]
    assert result["skills_learned"] == ["SQL", "RLS"]
    assert result["challenges_overcome"] == []
    assert result["talking_points"] == ["Ready for more"]


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


def _capture_stream_prompt(svc):
    prompts = []

    def fake_stream(prompt):
        prompts.append(prompt)
        return iter(["ok"])

    svc._stream = fake_stream
    return prompts


def test_explain_stream_uses_code_prompt_for_code(service):
    prompts = _capture_stream_prompt(service)
    list(service.explain_stream("def f(): pass", "code"))
    assert "They pasted this code:" in prompts[0]
    assert "where it's most likely to break" in prompts[0]


def test_explain_stream_uses_error_prompt_for_errors(service):
    prompts = _capture_stream_prompt(service)
    list(service.explain_stream("KeyError: 'id'", "error"))
    assert "They pasted this error output:" in prompts[0]
    assert "most likely root cause" in prompts[0]


def test_explain_stream_uses_general_prompt_for_messages(service):
    prompts = _capture_stream_prompt(service)
    list(service.explain_stream("can you review my PR?", "slack"))
    assert "pasted the following slack" in prompts[0]
    assert "They pasted this code" not in prompts[0]


def test_generate_reply_stream_yields_chunks(service):
    _stub_stream(service, ["yeah ", "for sure"])
    assert list(service.generate_reply_stream("ok?", "casual")) == ["yeah ", "for sure"]


def test_generate_resume_bullets_stream_yields_chunks(service):
    _stub_stream(service, ["- built X\n", "- shipped Y\n"])
    assert list(service.generate_resume_bullets_stream("notes")) == ["- built X\n", "- shipped Y\n"]


class _FakeSseResponse:
    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        pass

    def iter_lines(self):
        return iter(self._lines)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_groq_stream_parses_sse_chunks(monkeypatch):
    lines = [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}',
        "",  # keepalive / blank lines should be skipped
        'data: {"choices":[{"delta":{"content":" world"}}]}',
        "data: [DONE]",
    ]
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setattr("app.services.ai.httpx.stream", lambda *a, **k: _FakeSseResponse(lines))
    assert list(_groq_stream("hi")) == ["Hello", " world"]


def test_groq_complete_returns_message_content(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "hi there"}}]}
    monkeypatch.setattr("app.services.ai.httpx.post", lambda *a, **k: mock_response)
    assert _groq_complete("hi", json_output=False) == "hi there"


def test_stream_falls_back_to_groq_on_non_retryable_gemini_error(monkeypatch, service):
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    service.client = MagicMock()
    service.client.models.generate_content_stream.side_effect = APIError(500, {"error": {"message": "boom"}})
    monkeypatch.setattr("app.services.ai._groq_stream", lambda prompt: iter(["fallback ", "reply"]))

    assert list(service._stream("prompt")) == ["fallback ", "reply"]


def test_stream_raises_when_groq_not_configured(monkeypatch, service):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    service.client = MagicMock()
    service.client.models.generate_content_stream.side_effect = APIError(500, {"error": {"message": "boom"}})

    with pytest.raises(AIServiceError):
        list(service._stream("prompt"))


def test_stream_does_not_fall_back_once_real_output_has_started(monkeypatch, service):
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    service.client = MagicMock()

    def flaky_stream(*args, **kwargs):
        yield MagicMock(text="partial ")
        raise APIError(500, {"error": {"message": "boom"}})

    service.client.models.generate_content_stream.side_effect = lambda *a, **k: flaky_stream()
    fallback_called = MagicMock(side_effect=iter([]))
    monkeypatch.setattr("app.services.ai._groq_stream", fallback_called)

    with pytest.raises(AIServiceError):
        list(service._stream("prompt"))
    fallback_called.assert_not_called()


def test_complete_falls_back_to_groq_on_non_retryable_gemini_error(monkeypatch, service):
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    service.client = MagicMock()
    service.client.models.generate_content.side_effect = APIError(500, {"error": {"message": "boom"}})
    monkeypatch.setattr("app.services.ai._groq_complete", lambda prompt, json_output: "fallback text")

    assert service._complete("prompt") == "fallback text"


def test_complete_raises_when_groq_not_configured(monkeypatch, service):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    service.client = MagicMock()
    service.client.models.generate_content.side_effect = APIError(500, {"error": {"message": "boom"}})

    with pytest.raises(AIServiceError):
        service._complete("prompt")

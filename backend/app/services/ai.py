import json
import os
import time
from typing import Iterator

from google import genai
from google.genai import types
from google.genai.errors import APIError

MODEL = "gemini-flash-lite-latest"
MAX_TOKENS = 2048
RETRY_STATUSES = {429, 503}
MAX_RETRIES = 3

TONE_INSTRUCTIONS = {
    "casual": "friendly, uses contractions, sounds like a peer",
    "professional": "clear and respectful, no slang",
    "manager-safe": "concise, confident, shows ownership",
    "confused-but-trying": "honest about needing more info but shows effort",
}


class AIServiceError(Exception):
    pass


class AIService:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise AIServiceError("API key not configured")
        self.client = genai.Client(api_key=api_key)

    def _complete(self, prompt: str, json_output: bool = False) -> str:
        """Single-shot, non-streaming completion. Used where the full response
        is needed at once (weekly summary is generated rarely, so streaming it
        isn't worth the complexity)."""
        config = types.GenerateContentConfig(
            max_output_tokens=MAX_TOKENS,
            response_mime_type="application/json" if json_output else "text/plain",
        )
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=config,
                )
                text = response.text
                if not text:
                    raise AIServiceError("AI service unavailable")
                return text
            except APIError as exc:
                retryable = exc.code in RETRY_STATUSES and attempt < MAX_RETRIES - 1
                if not retryable:
                    raise AIServiceError("AI service unavailable") from exc
                time.sleep(2**attempt)
        raise AIServiceError("AI service unavailable")

    def _stream(self, prompt: str) -> Iterator[str]:
        """Yield text chunks as the model generates them. Retries (with
        backoff) only apply before the first chunk has been sent out - once
        the caller has started forwarding real output there's no way to
        retry without duplicating text, so a failure past that point just
        propagates."""
        config = types.GenerateContentConfig(max_output_tokens=MAX_TOKENS)
        attempt = 0
        while True:
            yielded_any = False
            try:
                for chunk in self.client.models.generate_content_stream(
                    model=MODEL, contents=prompt, config=config
                ):
                    if chunk.text:
                        yielded_any = True
                        yield chunk.text
                return
            except APIError as exc:
                retryable = not yielded_any and exc.code in RETRY_STATUSES and attempt < MAX_RETRIES - 1
                if not retryable:
                    raise AIServiceError("AI service unavailable") from exc
                attempt += 1
                time.sleep(2**attempt)

    def explain_stream(self, text: str, input_type: str) -> Iterator[str]:
        prompt = f"""You are a senior engineer helping a confused intern understand something at work.
The intern pasted the following {input_type}:

{text}

Respond in exactly this plain-text format (no markdown, no JSON):
EXPLANATION: <2-3 sentence plain English explanation, no jargon>
WHAT_THEY_MEAN: <1 sentence: what the person/system is actually asking for>
WHAT_TO_DO_NEXT: <1 sentence: the single most important next action>
ACTION_ITEMS:
- <specific actionable task>
- <specific actionable task>

Include 2-4 action items. Be direct, friendly, and assume the intern is smart but unfamiliar
with the codebase."""
        yield from self._stream(prompt)

    def generate_reply_stream(self, text: str, tone: str) -> Iterator[str]:
        tone_desc = TONE_INSTRUCTIONS.get(tone, tone)
        prompt = f"""You are helping an intern write a reply to the following message:

{text}

Write the reply in this tone: {tone} ({tone_desc}).
Respond with only the reply text, no preamble or explanation."""
        yield from self._stream(prompt)

    def chat_stream(self, original_text: str, explanation: str, history: list[dict], message: str) -> Iterator[str]:
        convo = "\n".join(
            f"{'Intern' if turn.get('role') == 'user' else 'You'}: {turn.get('content', '')}" for turn in history
        )
        convo_block = f"\nConversation so far:\n{convo}\n" if convo else ""
        prompt = f"""You are a senior engineer. Earlier, an intern pasted something at work and you explained it
to them. They now have a follow-up question.

What the intern originally pasted:
{original_text}

Your explanation:
{explanation}
{convo_block}
The intern now asks: {message}

Reply directly to their question in 1-4 sentences, plain English, no jargon, no preamble like
"Great question". If it isn't related to the original message, still answer it, briefly."""
        yield from self._stream(prompt)

    def generate_resume_bullets_stream(self, description: str) -> Iterator[str]:
        prompt = f"""You are helping an intern turn rough notes about their work into strong resume bullet points.

Notes:
{description}

Respond with 3-5 strong resume bullet points using action verbs and metrics where possible.
One bullet per line, each starting with "- ". No preamble, no extra commentary."""
        yield from self._stream(prompt)

    def generate_weekly_summary(self, entries: list[dict]) -> dict:
        prompt = f"""You are helping an intern write their weekly status update.
Given these progress entries: {entries}

Respond in JSON with:
- "what_i_worked_on": 2-3 sentence summary
- "what_i_learned": 2-3 sentence summary
- "blockers": blockers or "None this week"
- "resume_bullets": array of 3-5 strong resume bullet points with action verbs and metrics
- "talking_points": 3-4 bullet points for a midpoint/final internship review"""
        data = _parse_json(self._complete(prompt, json_output=True))
        return {
            "what_i_worked_on": _as_text(data.get("what_i_worked_on")),
            "what_i_learned": _as_text(data.get("what_i_learned")),
            "blockers": _as_text(data.get("blockers")) or "None this week",
            "resume_bullets": _as_list(data.get("resume_bullets")),
            "talking_points": _as_text(data.get("talking_points")),
        }


SECTION_MARKERS = {
    "EXPLANATION:": "explanation",
    "WHAT_THEY_MEAN:": "what_they_mean",
    "WHAT_TO_DO_NEXT:": "what_to_do_next",
}


def parse_explain_sections(text: str) -> dict:
    """Parse the plain-text EXPLANATION/WHAT_THEY_MEAN/... format streamed by
    explain_stream. Tolerant of the model drifting slightly from the format:
    if no markers are found at all, the whole response is used as the
    explanation rather than returning an empty card."""
    fields = {"explanation": "", "what_they_mean": "", "what_to_do_next": "", "action_items": []}
    current: str | None = None
    action_items: list[str] = []
    any_marker_found = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        upper = line.upper()

        matched_field = next((field for marker, field in SECTION_MARKERS.items() if upper.startswith(marker)), None)
        if matched_field:
            any_marker_found = True
            current = matched_field
            fields[current] = line.split(":", 1)[1].strip()
            continue
        if upper.startswith("ACTION_ITEMS"):
            any_marker_found = True
            current = "action_items"
            continue

        if current == "action_items":
            action_items.append(line.lstrip("-*•").strip())
        elif current in ("explanation", "what_they_mean", "what_to_do_next"):
            fields[current] = f"{fields[current]} {line}".strip()

    fields["action_items"] = [item for item in action_items if item]

    if not any_marker_found:
        fields["explanation"] = text.strip()

    return fields


def parse_bullet_lines(text: str) -> list[str]:
    """Parse a plain "- bullet" per line response. Falls back to the whole
    response as a single bullet if nothing looks like a bulleted line."""
    items = [line.strip().lstrip("-*•").strip() for line in text.splitlines()]
    items = [item for item in items if item]
    if items:
        return items
    stripped = text.strip()
    return [stripped] if stripped else []


def _as_text(value: object) -> str:
    """Model JSON fields that should be prose sometimes come back as a list of
    strings (or a number). Normalise everything to a single string."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    return str(value)


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value in (None, ""):
        return []
    return [str(value)]


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIServiceError("AI service unavailable") from exc
    if not isinstance(parsed, dict):
        raise AIServiceError("AI service unavailable")
    return parsed

import json
import os
import time

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

    def explain(self, text: str, input_type: str) -> dict:
        prompt = f"""You are a senior engineer helping a confused intern understand something at work.
The intern pasted the following {input_type}:

{text}

Respond in JSON with these exact keys:
- "explanation": plain English explanation (2-3 sentences, no jargon)
- "what_they_mean": what the person/system is actually asking for (1 sentence)
- "what_to_do_next": the single most important next action (1 sentence)
- "action_items": array of 2-4 specific actionable tasks as strings

Be direct, friendly, and assume the intern is smart but unfamiliar with the codebase."""
        data = _parse_json(self._complete(prompt, json_output=True))
        return {
            "explanation": _as_text(data.get("explanation")),
            "what_they_mean": _as_text(data.get("what_they_mean")),
            "what_to_do_next": _as_text(data.get("what_to_do_next")),
            "action_items": _as_list(data.get("action_items")),
        }

    def generate_reply(self, text: str, tone: str) -> str:
        tone_desc = TONE_INSTRUCTIONS.get(tone, tone)
        prompt = f"""You are helping an intern write a reply to the following message:

{text}

Write the reply in this tone: {tone} ({tone_desc}).
Respond with only the reply text, no preamble or explanation."""
        return self._complete(prompt).strip()

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

    def generate_resume_bullets(self, description: str) -> list[str]:
        prompt = f"""You are helping an intern turn rough notes about their work into strong resume bullet points.

Notes:
{description}

Respond in JSON with a single key "bullets": an array of 3-5 strong resume bullet points using action verbs and metrics where possible."""
        parsed = _parse_json(self._complete(prompt, json_output=True))
        return _as_list(parsed.get("bullets"))


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

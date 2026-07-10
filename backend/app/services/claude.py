import json
import os

from anthropic import Anthropic

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1500

TONE_INSTRUCTIONS = {
    "casual": "friendly, uses contractions, sounds like a peer",
    "professional": "clear and respectful, no slang",
    "manager-safe": "concise, confident, shows ownership",
    "confused-but-trying": "honest about needing more info but shows effort",
}


class ClaudeServiceError(Exception):
    pass


class ClaudeService:
    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ClaudeServiceError("API key not configured")
        self.client = Anthropic(api_key=api_key)

    def _complete(self, prompt: str) -> str:
        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as exc:
            raise ClaudeServiceError("AI service unavailable") from exc

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
        raw = self._complete(prompt)
        return _parse_json(raw)

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
        raw = self._complete(prompt)
        return _parse_json(raw)

    def generate_resume_bullets(self, description: str) -> list[str]:
        prompt = f"""You are helping an intern turn rough notes about their work into strong resume bullet points.

Notes:
{description}

Respond in JSON with a single key "bullets": an array of 3-5 strong resume bullet points using action verbs and metrics where possible."""
        raw = self._complete(prompt)
        parsed = _parse_json(raw)
        return parsed.get("bullets", [])


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ClaudeServiceError("AI service unavailable") from exc

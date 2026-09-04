from typing import Optional

from pydantic import BaseModel, Field

# Rough upper bound on a single pasted message / note. Keeps prompts (and cost)
# sane and rejects accidental multi-megabyte log dumps before they reach the model.
MAX_INPUT_CHARS = 15_000


class ExplainRequest(BaseModel):
    text: str = Field(max_length=MAX_INPUT_CHARS)


class ExplainResponse(BaseModel):
    input_type: str
    explanation: str
    what_they_mean: str
    what_to_do_next: str
    action_items: list[str]
    paste_id: Optional[str] = None
    saved: bool = False


class ReplyRequest(BaseModel):
    text: str = Field(max_length=MAX_INPUT_CHARS)
    tone: str
    paste_id: Optional[str] = None


class ReplyResponse(BaseModel):
    reply: str
    tone: str
    saved: bool = False


class ProgressEntryCreate(BaseModel):
    entry_text: str = Field(max_length=MAX_INPUT_CHARS)
    entry_type: str
    week_start: str


class ProgressEntryResponse(BaseModel):
    id: str
    created_at: str


class ProgressEntry(BaseModel):
    id: str
    entry_text: str
    entry_type: str
    week_start: str
    created_at: str


class ProgressListResponse(BaseModel):
    entries: list[ProgressEntry]


class WeeklySummaryRequest(BaseModel):
    week_start: str


class WeeklySummary(BaseModel):
    what_i_worked_on: str
    what_i_learned: str
    blockers: str
    resume_bullets: list[str]
    talking_points: str


class WeeklySummaryResponse(BaseModel):
    summary: WeeklySummary
    saved: bool = False


class ResumeBulletsRequest(BaseModel):
    description: str = Field(max_length=MAX_INPUT_CHARS)


class ResumeBulletsResponse(BaseModel):
    bullets: list[str]
    saved: bool = False

from datetime import datetime
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


class ExplainChatRequest(BaseModel):
    paste_id: str
    message: str = Field(max_length=MAX_INPUT_CHARS)


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


class InternshipRecap(BaseModel):
    headline: str
    highlights: list[str]
    skills_learned: list[str]
    challenges_overcome: list[str]
    resume_bullets: list[str]
    talking_points: list[str]


class InternshipRecapResponse(BaseModel):
    recap: InternshipRecap
    first_week: str
    last_week: str
    weeks_covered: int
    entry_count: int


class GlossaryTermCreate(BaseModel):
    term: str = Field(min_length=1, max_length=200)
    definition: str = Field(min_length=1, max_length=2_000)
    context: Optional[str] = Field(default=None, max_length=500)
    paste_id: Optional[str] = None


class GlossaryTermsCreate(BaseModel):
    terms: list[GlossaryTermCreate] = Field(min_length=1, max_length=50)


class GlossaryTermUpdate(BaseModel):
    term: Optional[str] = Field(default=None, min_length=1, max_length=200)
    definition: Optional[str] = Field(default=None, min_length=1, max_length=2_000)


class GlossaryTerm(BaseModel):
    id: str
    term: str
    definition: str
    context: Optional[str] = None
    paste_id: Optional[str] = None
    created_at: str


class GlossaryListResponse(BaseModel):
    terms: list[GlossaryTerm]


class GlossarySaveResponse(BaseModel):
    saved: list[GlossaryTerm]
    skipped: list[str]


class GlossarySuggestRequest(BaseModel):
    paste_id: str


class GlossarySuggestion(BaseModel):
    term: str
    definition: str
    context: Optional[str] = None


class GlossarySuggestResponse(BaseModel):
    suggestions: list[GlossarySuggestion]


class StandupRequest(BaseModel):
    # Start of the user's previous workday in their local time, as an ISO timestamp
    # with offset. The frontend computes it so "yesterday" means the user's yesterday.
    since: datetime
    notes: Optional[str] = Field(default=None, max_length=2_000)


class StandupResponse(BaseModel):
    yesterday: list[str]
    today: list[str]
    blockers: list[str]
    entry_count: int
    paste_count: int


class MentorQuestionCreate(BaseModel):
    question: str = Field(min_length=1, max_length=1_000)
    context: Optional[str] = Field(default=None, max_length=500)
    paste_id: Optional[str] = None


class MentorQuestionsCreate(BaseModel):
    questions: list[MentorQuestionCreate] = Field(min_length=1, max_length=20)


class MentorQuestionUpdate(BaseModel):
    question: Optional[str] = Field(default=None, min_length=1, max_length=1_000)
    # true marks it answered (with an optional answer note), false reopens it.
    answered: Optional[bool] = None
    answer: Optional[str] = Field(default=None, max_length=2_000)


class MentorQuestion(BaseModel):
    id: str
    question: str
    context: Optional[str] = None
    paste_id: Optional[str] = None
    answer: Optional[str] = None
    answered_at: Optional[str] = None
    created_at: str


class MentorQuestionListResponse(BaseModel):
    questions: list[MentorQuestion]


class MentorQuestionSuggestRequest(BaseModel):
    paste_id: str


class MentorQuestionSuggestion(BaseModel):
    question: str
    context: Optional[str] = None


class MentorQuestionSuggestResponse(BaseModel):
    suggestions: list[MentorQuestionSuggestion]

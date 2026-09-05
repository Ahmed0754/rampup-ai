import re

# Plain substring checks used to misfire on capitalized words that happen to
# contain a keyword - e.g. "PR" matched inside "PRIORITY" or "SPRINT", and
# "ticket"/"meeting" were case-sensitive so "Ticket ENG-123" or "Meeting notes"
# never matched. Matching on whole words (case-insensitively) fixes both.
_WORD_PATTERNS = {
    "error": [r"\btraceback\b", r"\berror:"],
    "email": [r"\bdear\b", r"\bsubject:"],
    "jira": [r"\btickets?\b", r"\bstory points\b"],
    "pr": [r"\bpr\b", r"\bpull requests?\b"],
    "meeting_note": [r"\bmeetings?\b", r"\bstand-?ups?\b"],
}


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def classify_input(text: str) -> str:
    if _matches_any(text, _WORD_PATTERNS["error"]) or "$ " in text:
        return "error"
    if "@" in text and _has_short_paragraphs(text):
        return "slack"
    if _matches_any(text, _WORD_PATTERNS["email"]):
        return "email"
    if _matches_any(text, _WORD_PATTERNS["jira"]):
        return "jira"
    if _matches_any(text, _WORD_PATTERNS["pr"]):
        return "pr"
    if _matches_any(text, _WORD_PATTERNS["meeting_note"]):
        return "meeting_note"
    return "other"


def _has_short_paragraphs(text: str) -> bool:
    paragraphs = [p for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return False
    return all(len(p.split()) <= 40 for p in paragraphs)

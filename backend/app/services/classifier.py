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

# Unambiguous signs of a stack trace. Checked before code detection, since a
# trace is full of code-looking lines.
_STACK_TRACE_PATTERNS = [
    re.compile(r'^\s*File ".+", line \d+', re.MULTILINE),  # Python
    re.compile(r"^\s+at \S+ \(?.+:\d+(:\d+)?\)?$", re.MULTILINE),  # JS / Java
    re.compile(r"^(goroutine \d+|panic:)", re.MULTILINE),  # Go
]

# Exception names like TypeError / NullPointerException. "\berror:" misses
# these because "Error" sits mid-word. Case-sensitive on purpose, and checked
# after code detection so `except ValueError:` in a snippet still reads as code.
_EXCEPTION_NAME = re.compile(r"\b[A-Z][A-Za-z]*(?:Error|Exception)\b")

_CODE_LINE_PATTERNS = [
    re.compile(
        r"^\s*(?:def|class|import|from \S+ import|function|const|let|var|return|public|private|protected|"
        r"static|package|func|fn|async def|#include|if\s*\(|for\s*\(|while\s*\(|else\b|elif\b|try\b|except\b)"
    ),
    re.compile(r"[{};]\s*$|\):\s*$|=>"),
    re.compile(r"^\s*(?:SELECT|INSERT INTO|UPDATE|DELETE FROM|CREATE TABLE|ALTER TABLE)\b"),
    re.compile(r"&&|\|\||!==?|===?|::|->"),
    re.compile(r"^\s*(?:if|for|while|with|elif|else)\b.*:\s*$"),  # Python block headers
    re.compile(r"^\s*[\w.]+\(.*\)\s*$"),  # bare call statement: codes.append(code)
    re.compile(r"^\s*[\w.\[\]]+\s*[-+*/]?=\s*\S"),  # assignment: order.total = ...
]
# A pasted snippet needs at least this many code-looking lines, making up at
# least this share of the non-empty lines, so a chat message that mentions a
# function name or ends a sentence with ";" isn't mistaken for code.
_MIN_CODE_LINES = 2
_MIN_CODE_RATIO = 0.4


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def classify_input(text: str) -> str:
    if (
        _matches_any(text, [r"\btraceback\b"])
        or any(p.search(text) for p in _STACK_TRACE_PATTERNS)
        or "$ " in text
    ):
        return "error"
    if _looks_like_code(text):
        return "code"
    if _matches_any(text, _WORD_PATTERNS["error"]) or _EXCEPTION_NAME.search(text):
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


def _looks_like_code(text: str) -> bool:
    if "```" in text:
        return True
    lines = [line for line in text.split("\n") if line.strip()]
    code_lines = sum(1 for line in lines if any(p.search(line) for p in _CODE_LINE_PATTERNS))
    return code_lines >= _MIN_CODE_LINES and code_lines / len(lines) >= _MIN_CODE_RATIO


def _has_short_paragraphs(text: str) -> bool:
    paragraphs = [p for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return False
    return all(len(p.split()) <= 40 for p in paragraphs)

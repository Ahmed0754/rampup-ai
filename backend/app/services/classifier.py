def classify_input(text: str) -> str:
    if "Traceback" in text or "Error:" in text or "$ " in text:
        return "error"
    if "@" in text and _has_short_paragraphs(text):
        return "slack"
    if "Dear" in text or "Subject:" in text:
        return "email"
    if "ticket" in text or "story points" in text:
        return "jira"
    if "PR" in text or "pull request" in text:
        return "pr"
    if "meeting" in text or "standup" in text:
        return "meeting_note"
    return "other"


def _has_short_paragraphs(text: str) -> bool:
    paragraphs = [p for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return False
    return all(len(p.split()) <= 40 for p in paragraphs)

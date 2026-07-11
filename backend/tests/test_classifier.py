from app.services.classifier import classify_input


def test_classify_traceback_as_error():
    text = "Traceback (most recent call last):\n  File 'x.py', line 1"
    assert classify_input(text) == "error"


def test_classify_error_colon_as_error():
    assert classify_input("Error: connection refused") == "error"


def test_classify_shell_prompt_as_error():
    assert classify_input("$ npm run build\nfailed with exit code 1") == "error"


def test_classify_slack_message():
    text = "hey @sarah can you review my PR when you get a chance?\nno rush!"
    assert classify_input(text) == "slack"


def test_classify_slack_short_paragraphs():
    text = "@mike quick question about the deploy\nis staging still down?"
    assert classify_input(text) == "slack"


def test_classify_email_with_dear():
    text = "Dear team,\n\nI wanted to follow up on our last conversation."
    assert classify_input(text) == "email"


def test_classify_email_with_subject():
    text = "Subject: Weekly sync notes\n\nHi all, sharing notes from today."
    assert classify_input(text) == "email"


def test_classify_jira_ticket():
    assert classify_input("Please pick up ticket ENG-123 for the sprint") == "jira"


def test_classify_jira_story_points():
    assert classify_input("This task is estimated at 5 story points") == "jira"


def test_classify_pr():
    assert classify_input("Can you review my PR #482?") == "pr"


def test_classify_pull_request():
    assert classify_input("Opened a pull request for the auth fix") == "pr"


def test_classify_meeting():
    assert classify_input("Notes from the meeting we had today") == "meeting_note"


def test_classify_standup():
    assert classify_input("standup notes: blocked on API access") == "meeting_note"


def test_classify_default_other():
    assert classify_input("just some random unrelated text") == "other"


def test_classify_empty_string_is_other():
    assert classify_input("") == "other"


def test_classify_error_takes_precedence_over_slack():
    text = "Traceback (most recent call last):\n@user this broke in prod"
    assert classify_input(text) == "error"

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


def test_classify_priority_is_not_misread_as_pr():
    # "PR" used to match as a bare substring, so ALL-CAPS "PRIORITY" false-
    # positived as a pull request.
    assert classify_input("This is SUPER PRIORITY, please fix ASAP") == "other"


def test_classify_sprint_is_not_misread_as_pr():
    assert classify_input("Let's wrap up this SPRINT by Friday, we're on track") == "other"


def test_classify_ticket_is_case_insensitive():
    assert classify_input("Ticket ENG-500 needs a fix before release") == "jira"


def test_classify_meetings_plural():
    assert classify_input("Notes from yesterday's meetings") == "meeting_note"


def test_classify_python_snippet_as_code():
    text = "def total(items):\n    result = 0\n    for item in items:\n        result += item.price\n    return result"
    assert classify_input(text) == "code"


def test_classify_js_snippet_as_code():
    text = "const user = await getUser(id);\nif (!user) {\n  return null;\n}\nsetUser(user);"
    assert classify_input(text) == "code"


def test_classify_sql_as_code():
    text = "SELECT id, email\nFROM users\nWHERE created_at > now() - interval '7 days';\n"
    assert classify_input(text) == "code"


def test_classify_fenced_block_as_code():
    assert classify_input("what does this do?\n```\nx = [i for i in y]\n```") == "code"


def test_python_snippet_with_except_clause_is_code_not_error():
    text = "try:\n    value = int(raw)\nexcept ValueError:\n    value = 0\nreturn value"
    assert classify_input(text) == "code"


def test_classify_camelcase_exception_names_as_error():
    assert classify_input("TypeError: Cannot read properties of undefined (reading 'map')") == "error"
    assert classify_input("java.lang.NullPointerException thrown in OrderService") == "error"


def test_classify_python_stack_frame_as_error():
    text = 'File "app/main.py", line 12, in <module>\n    run()\nKeyError: \'user_id\''
    assert classify_input(text) == "error"


def test_classify_js_stack_trace_as_error_not_code():
    text = (
        "Uncaught (in promise) undefined is not a function\n"
        "    at handleClick (Button.tsx:42:13)\n"
        "    at onClick (App.tsx:10:5)"
    )
    assert classify_input(text) == "error"


def test_classify_go_panic_as_error():
    assert classify_input("panic: runtime error: index out of range [3] with length 3") == "error"


def test_message_mentioning_a_function_is_not_code():
    text = "@sam I think getUser() is returning null sometimes\ncan you take a look when you're free?"
    assert classify_input(text) == "slack"


def test_prose_with_a_single_semicolon_line_is_not_code():
    text = "Dear team;\n\nThanks for a great quarter. Let's keep the momentum going into next year."
    assert classify_input(text) == "email"


def test_lowercase_select_in_prose_is_not_sql():
    text = "Please select the right template\nfrom the dropdown before the meeting."
    assert classify_input(text) == "meeting_note"


def test_classify_python_with_block_headers_and_statements_as_code():
    # Regression: only the def and return lines used to count as code here,
    # so this landed under "other" and got the chat-message prompt.
    text = (
        "def apply_discount(order, codes=[]):\n"
        "    for code in order.promo_codes:\n"
        "        codes.append(code)\n"
        '    if "WELCOME10" in codes:\n'
        "        order.total = order.total * 0.9\n"
        "    return order"
    )
    assert classify_input(text) == "code"


def test_chat_message_with_a_colon_line_is_not_code():
    text = "@priya if you get a chance today:\ncould you look at the deploy failure from this morning? thanks!"
    assert classify_input(text) == "slack"

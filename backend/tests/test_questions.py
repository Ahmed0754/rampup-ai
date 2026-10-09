from unittest.mock import MagicMock, patch

from app.services.ai import AIServiceError

R = "app.routers.questions"

OPEN = {"id": "q1", "question": "Who owns the payments service?", "context": None, "paste_id": None,
        "answer": None, "answered_at": None, "created_at": "2026-10-08T00:00:00Z"}
ANSWERED = {**OPEN, "id": "q2", "question": "When is code freeze?", "answer": "Fridays",
            "answered_at": "2026-10-08T12:00:00Z"}


def _saved(rows):
    return [{**r, "id": f"new-{i}", "answer": None, "answered_at": None, "created_at": "2026-10-09T00:00:00Z"}
            for i, r in enumerate(rows)]


def test_list_questions(client, auth_headers):
    with patch(f"{R}.get_mentor_questions", return_value=[OPEN, ANSWERED]) as mock_get:
        response = client.get("/api/questions", headers=auth_headers)
    assert response.status_code == 200
    assert [q["id"] for q in response.json()["questions"]] == ["q1", "q2"]
    mock_get.assert_called_once_with("test-user-id")


def test_list_502_when_load_fails(client, auth_headers):
    with patch(f"{R}.get_mentor_questions", return_value=None):
        assert client.get("/api/questions", headers=auth_headers).status_code == 502


def test_add_strips_and_drops_unowned_paste_ids(client, auth_headers):
    payload = {"questions": [
        {"question": "  Who reviews infra PRs?  ", "context": "  from a Slack thread ", "paste_id": "p-mine"},
        {"question": "Is there a style guide?", "paste_id": "p-theirs"},
    ]}
    with (
        patch(f"{R}.get_paste", side_effect=lambda pid, uid: {"id": pid} if pid == "p-mine" else None),
        patch(f"{R}.save_mentor_questions", side_effect=lambda uid, rows: _saved(rows)) as mock_save,
    ):
        response = client.post("/api/questions", json=payload, headers=auth_headers)

    assert response.status_code == 200
    assert mock_save.call_args.args[1] == [
        {"question": "Who reviews infra PRs?", "context": "from a Slack thread", "paste_id": "p-mine"},
        {"question": "Is there a style guide?", "context": None, "paste_id": None},
    ]


def test_add_rejects_blank_and_handles_save_failure(client, auth_headers):
    blank = client.post("/api/questions", json={"questions": [{"question": "   "}]}, headers=auth_headers)
    assert blank.status_code == 422
    with patch(f"{R}.save_mentor_questions", return_value=None):
        failed = client.post("/api/questions", json={"questions": [{"question": "Q?"}]}, headers=auth_headers)
    assert failed.status_code == 502


def test_mark_answered_sets_timestamp_and_answer(client, auth_headers):
    with patch(f"{R}.update_mentor_question", return_value=ANSWERED) as mock_update:
        response = client.patch("/api/questions/q1", json={"answered": True, "answer": " Fridays "},
                                headers=auth_headers)
    assert response.status_code == 200
    uid, qid, changes = mock_update.call_args.args
    assert (uid, qid) == ("test-user-id", "q1")
    assert changes["answer"] == "Fridays"
    assert changes["answered_at"].endswith("+00:00")


def test_reopen_clears_answer(client, auth_headers):
    with patch(f"{R}.update_mentor_question", return_value=OPEN) as mock_update:
        client.patch("/api/questions/q2", json={"answered": False}, headers=auth_headers)
    assert mock_update.call_args.args[2] == {"answered_at": None, "answer": None}


def test_edit_question_text(client, auth_headers):
    with patch(f"{R}.update_mentor_question", return_value=OPEN) as mock_update:
        client.patch("/api/questions/q1", json={"question": " Who owns billing? "}, headers=auth_headers)
    assert mock_update.call_args.args[2] == {"question": "Who owns billing?"}


def test_edit_422_and_404(client, auth_headers):
    assert client.patch("/api/questions/q1", json={}, headers=auth_headers).status_code == 422
    assert client.patch("/api/questions/q1", json={"question": "  "}, headers=auth_headers).status_code == 422
    with patch(f"{R}.update_mentor_question", return_value=None):
        response = client.patch("/api/questions/nope", json={"answered": True}, headers=auth_headers)
    assert response.status_code == 404


def test_delete(client, auth_headers):
    with patch(f"{R}.delete_mentor_question", return_value=True) as mock_delete:
        assert client.delete("/api/questions/q1", headers=auth_headers).status_code == 204
    mock_delete.assert_called_once_with("test-user-id", "q1")
    with patch(f"{R}.delete_mentor_question", return_value=False):
        assert client.delete("/api/questions/nope", headers=auth_headers).status_code == 404


def test_suggest_passes_chat_and_only_open_questions(client, auth_headers):
    service = MagicMock()
    service.suggest_mentor_questions.return_value = [{"question": "Which env should I test in?", "context": "c"}]
    paste = {"raw_text": "deploy to staging", "explanation": "e"}
    chat = [{"role": "user", "content": f"m{i}"} for i in range(15)]
    with (
        patch(f"{R}.get_paste", return_value=paste),
        patch(f"{R}.get_explain_chat_messages", return_value=chat),
        patch(f"{R}.get_mentor_questions", return_value=[OPEN, ANSWERED]),
        patch(f"{R}.AIService", return_value=service),
    ):
        response = client.post("/api/questions/suggest", json={"paste_id": "p1"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["suggestions"][0]["question"] == "Which env should I test in?"
    text, explanation, sent_chat, open_questions = service.suggest_mentor_questions.call_args.args
    assert (text, explanation) == ("deploy to staging", "e")
    assert len(sent_chat) == 10 and sent_chat[-1]["content"] == "m14"
    assert open_questions == ["Who owns the payments service?"]


def test_suggest_404_and_502(client, auth_headers):
    with patch(f"{R}.get_paste", return_value=None):
        assert client.post("/api/questions/suggest", json={"paste_id": "x"}, headers=auth_headers).status_code == 404

    service = MagicMock()
    service.suggest_mentor_questions.side_effect = AIServiceError("AI service unavailable")
    with (
        patch(f"{R}.get_paste", return_value={"raw_text": "x", "explanation": ""}),
        patch(f"{R}.get_explain_chat_messages", return_value=[]),
        patch(f"{R}.get_mentor_questions", return_value=[]),
        patch(f"{R}.AIService", return_value=service),
    ):
        assert client.post("/api/questions/suggest", json={"paste_id": "p"}, headers=auth_headers).status_code == 502


def test_questions_require_auth(client):
    assert client.get("/api/questions").status_code == 401
    assert client.post("/api/questions/suggest", json={"paste_id": "p"}).status_code == 401

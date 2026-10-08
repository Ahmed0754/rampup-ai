from unittest.mock import MagicMock, patch

from app.services.ai import AIServiceError

R = "app.routers.glossary"

EXISTING = [
    {"id": "t1", "term": "CI", "definition": "Runs tests on every push", "context": None, "paste_id": None,
     "created_at": "2026-10-01T00:00:00Z"},
]


def _saved(terms):
    return [{**t, "id": f"new-{i}", "created_at": "2026-10-08T00:00:00Z"} for i, t in enumerate(terms)]


def test_list_returns_terms(client, auth_headers):
    with patch(f"{R}.get_glossary_terms", return_value=EXISTING) as mock_get:
        response = client.get("/api/glossary", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["terms"][0]["term"] == "CI"
    mock_get.assert_called_once_with("test-user-id")


def test_list_502_when_glossary_cannot_load(client, auth_headers):
    with patch(f"{R}.get_glossary_terms", return_value=None):
        assert client.get("/api/glossary", headers=auth_headers).status_code == 502


def test_add_skips_existing_and_in_batch_duplicates_case_insensitively(client, auth_headers):
    payload = {"terms": [
        {"term": "  ci ", "definition": "dup of existing"},
        {"term": "Idempotent", "definition": "Safe to run twice", "context": "  make it idempotent "},
        {"term": "idempotent", "definition": "dup within batch"},
    ]}
    with (
        patch(f"{R}.get_glossary_terms", return_value=EXISTING),
        patch(f"{R}.save_glossary_terms", side_effect=lambda uid, terms: _saved(terms)) as mock_save,
    ):
        response = client.post("/api/glossary", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["skipped"] == ["ci", "idempotent"]
    assert [t["term"] for t in body["saved"]] == ["Idempotent"]
    sent = mock_save.call_args.args[1]
    assert sent == [{"term": "Idempotent", "definition": "Safe to run twice", "context": "make it idempotent",
                     "paste_id": None}]


def test_add_with_nothing_new_does_not_write(client, auth_headers):
    with (
        patch(f"{R}.get_glossary_terms", return_value=EXISTING),
        patch(f"{R}.save_glossary_terms") as mock_save,
    ):
        body = client.post("/api/glossary", json={"terms": [{"term": "CI", "definition": "x"}]},
                           headers=auth_headers).json()
    assert body == {"saved": [], "skipped": ["CI"]}
    mock_save.assert_not_called()


def test_add_drops_paste_ids_the_user_does_not_own(client, auth_headers):
    payload = {"terms": [
        {"term": "Mine", "definition": "d", "paste_id": "p-mine"},
        {"term": "Theirs", "definition": "d", "paste_id": "p-theirs"},
    ]}
    with (
        patch(f"{R}.get_glossary_terms", return_value=[]),
        patch(f"{R}.get_paste", side_effect=lambda pid, uid: {"id": pid} if pid == "p-mine" else None),
        patch(f"{R}.save_glossary_terms", side_effect=lambda uid, terms: _saved(terms)) as mock_save,
    ):
        client.post("/api/glossary", json=payload, headers=auth_headers)
    sent = mock_save.call_args.args[1]
    assert [t["paste_id"] for t in sent] == ["p-mine", None]


def test_add_rejects_blank_term(client, auth_headers):
    with patch(f"{R}.get_glossary_terms", return_value=[]):
        response = client.post("/api/glossary", json={"terms": [{"term": "   ", "definition": "d"}]},
                               headers=auth_headers)
    assert response.status_code == 422


def test_add_502_when_save_fails(client, auth_headers):
    with (
        patch(f"{R}.get_glossary_terms", return_value=[]),
        patch(f"{R}.save_glossary_terms", return_value=None),
    ):
        response = client.post("/api/glossary", json={"terms": [{"term": "X", "definition": "d"}]},
                               headers=auth_headers)
    assert response.status_code == 502


def test_edit_updates_definition(client, auth_headers):
    updated = {**EXISTING[0], "definition": "Continuous integration"}
    with patch(f"{R}.update_glossary_term", return_value=updated) as mock_update:
        response = client.patch("/api/glossary/t1", json={"definition": " Continuous integration "},
                                headers=auth_headers)
    assert response.status_code == 200
    mock_update.assert_called_once_with("test-user-id", "t1", {"definition": "Continuous integration"})


def test_edit_409_when_renaming_onto_another_term(client, auth_headers):
    other = {**EXISTING[0], "id": "t2", "term": "CD"}
    with patch(f"{R}.get_glossary_terms", return_value=EXISTING + [other]):
        response = client.patch("/api/glossary/t2", json={"term": "ci"}, headers=auth_headers)
    assert response.status_code == 409


def test_edit_allows_recasing_the_same_term(client, auth_headers):
    with (
        patch(f"{R}.get_glossary_terms", return_value=EXISTING),
        patch(f"{R}.update_glossary_term", return_value={**EXISTING[0], "term": "ci"}),
    ):
        response = client.patch("/api/glossary/t1", json={"term": "ci"}, headers=auth_headers)
    assert response.status_code == 200


def test_edit_422_when_empty_and_404_when_missing(client, auth_headers):
    assert client.patch("/api/glossary/t1", json={}, headers=auth_headers).status_code == 422
    with patch(f"{R}.update_glossary_term", return_value=None):
        response = client.patch("/api/glossary/nope", json={"definition": "x"}, headers=auth_headers)
    assert response.status_code == 404


def test_delete(client, auth_headers):
    with patch(f"{R}.delete_glossary_term", return_value=True) as mock_delete:
        assert client.delete("/api/glossary/t1", headers=auth_headers).status_code == 204
    mock_delete.assert_called_once_with("test-user-id", "t1")
    with patch(f"{R}.delete_glossary_term", return_value=False):
        assert client.delete("/api/glossary/nope", headers=auth_headers).status_code == 404


def test_suggest_filters_out_known_terms_and_duplicates(client, auth_headers):
    service = MagicMock()
    service.suggest_glossary_terms.return_value = [
        {"term": "ci", "definition": "known", "context": None},
        {"term": "Feature flag", "definition": "A switch", "context": "behind a feature flag"},
        {"term": "feature flag", "definition": "dup", "context": None},
    ]
    paste = {"id": "p1", "raw_text": "ship it behind a feature flag once CI is green", "explanation": "e"}
    with (
        patch(f"{R}.get_paste", return_value=paste),
        patch(f"{R}.get_glossary_terms", return_value=EXISTING),
        patch(f"{R}.AIService", return_value=service),
    ):
        response = client.post("/api/glossary/suggest", json={"paste_id": "p1"}, headers=auth_headers)

    assert response.status_code == 200
    assert [s["term"] for s in response.json()["suggestions"]] == ["Feature flag"]
    assert service.suggest_glossary_terms.call_args.args == (paste["raw_text"], "e", ["CI"])


def test_suggest_404_for_unknown_paste(client, auth_headers):
    with patch(f"{R}.get_paste", return_value=None):
        response = client.post("/api/glossary/suggest", json={"paste_id": "nope"}, headers=auth_headers)
    assert response.status_code == 404


def test_suggest_maps_ai_errors_to_502(client, auth_headers):
    service = MagicMock()
    service.suggest_glossary_terms.side_effect = AIServiceError("AI service unavailable")
    with (
        patch(f"{R}.get_paste", return_value={"raw_text": "x", "explanation": ""}),
        patch(f"{R}.get_glossary_terms", return_value=[]),
        patch(f"{R}.AIService", return_value=service),
    ):
        response = client.post("/api/glossary/suggest", json={"paste_id": "p1"}, headers=auth_headers)
    assert response.status_code == 502


def test_glossary_requires_auth(client):
    assert client.get("/api/glossary").status_code == 401
    assert client.post("/api/glossary/suggest", json={"paste_id": "p"}).status_code == 401

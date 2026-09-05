from app.main import DEFAULT_ORIGINS, _parse_origins


def test_parse_origins_defaults_when_unset():
    assert _parse_origins(None) == DEFAULT_ORIGINS
    assert _parse_origins("") == DEFAULT_ORIGINS


def test_parse_origins_splits_and_trims_csv():
    assert _parse_origins("https://a.example.com, https://b.example.com") == [
        "https://a.example.com",
        "https://b.example.com",
    ]


def test_parse_origins_drops_empty_entries():
    assert _parse_origins("https://a.example.com,,  ,") == ["https://a.example.com"]


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

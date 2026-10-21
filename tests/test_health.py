def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    # /health must report DB reachability, not just "process alive".
    assert body["database"] == "ok"


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "NegotiateAI API"


def test_docs_available(client):
    assert client.get("/docs").status_code == 200

import uuid


def _new_email():
    return f"user_{uuid.uuid4().hex[:8]}@example.com"


def test_register_login_me(client):
    email = _new_email()
    r = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Auth User", "password": "TestPass@123"},
    )
    assert r.status_code == 201, r.text

    r = client.post("/api/auth/login", data={"username": email, "password": "TestPass@123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_duplicate_email_rejected(client):
    email = _new_email()
    payload = {"email": email, "full_name": "Dup", "password": "TestPass@123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 400


def test_login_wrong_password(client):
    email = _new_email()
    client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Wrong", "password": "TestPass@123"},
    )
    r = client.post("/api/auth/login", data={"username": email, "password": "nope"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_malformed_jwt_rejected(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert r.status_code == 401

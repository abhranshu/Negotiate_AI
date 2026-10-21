def test_create_and_get_case(client, auth_headers):
    payload = {
        "dispute_type": "delayed_payment",
        "claim_amount": 250000,
        "overdue_days": 90,
        "description": "Invoice not paid for 90 days",
        "state": "MH",
        "industry": "manufacturing",
    }
    r = client.post("/api/cases", json=payload, headers=auth_headers)
    assert r.status_code == 201, r.text
    case = r.json()
    assert case["claim_amount"] == 250000
    case_id = case["id"]

    r = client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["claim_amount"] == 250000


def test_list_cases(client, auth_headers):
    client.post(
        "/api/cases",
        json={"dispute_type": "non_payment", "claim_amount": 10000},
        headers=auth_headers,
    )
    r = client.get("/api/cases", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_case_requires_auth(client):
    assert client.get("/api/cases").status_code == 401


def test_get_unknown_case_404(client, auth_headers):
    r = client.get("/api/cases/does-not-exist", headers=auth_headers)
    assert r.status_code == 404


def test_unauthorized_case_access(client, auth_headers):
    # Create a case as user A, then try to read it as a different user B.
    r = client.post(
        "/api/cases",
        json={"dispute_type": "delayed_payment", "claim_amount": 5000},
        headers=auth_headers,
    )
    case_id = r.json()["id"]

    import uuid

    email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Other", "password": "TestPass@123"},
    )
    tok = client.post(
        "/api/auth/login", data={"username": email, "password": "TestPass@123"}
    ).json()["access_token"]
    r = client.get(f"/api/cases/{case_id}", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403

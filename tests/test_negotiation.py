def _make_case(client, auth_headers):
    r = client.post(
        "/api/cases",
        json={"dispute_type": "delayed_payment", "claim_amount": 400000},
        headers=auth_headers,
    )
    return r.json()["id"]


def test_negotiate_returns_mediator_response(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    r = client.post(
        f"/api/cases/{case_id}/negotiate",
        json={"text": "We are owed 4 lakh and it is 90 days overdue.", "offer": 300000},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mediator_response"]
    assert isinstance(body["agreement_reached"], bool)
    assert "is_fallback" in body


def test_negotiation_history_persisted(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    client.post(
        f"/api/cases/{case_id}/negotiate",
        json={"text": "Please pay at least half.", "offer": 200000},
        headers=auth_headers,
    )
    r = client.get(f"/api/cases/{case_id}/messages", headers=auth_headers)
    assert r.status_code == 200
    # The claimant message + mediator reply are stored.
    assert len(r.json()) >= 2


def test_negotiate_requires_auth(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    r = client.post(f"/api/cases/{case_id}/negotiate", json={"text": "hi"})
    assert r.status_code == 401

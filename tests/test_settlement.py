def _make_case(client, auth_headers):
    r = client.post(
        "/api/cases",
        json={"dispute_type": "delayed_payment", "claim_amount": 200000},
        headers=auth_headers,
    )
    return r.json()["id"]


def test_settlement_requires_agreement_amount(client, auth_headers):
    """No negotiated amount yet -> 400, never a fabricated settlement."""
    case_id = _make_case(client, auth_headers)
    r = client.post(f"/api/cases/{case_id}/settlement", headers=auth_headers)
    assert r.status_code == 400


def test_settlement_404_when_absent(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    r = client.get(f"/api/cases/{case_id}/settlement", headers=auth_headers)
    assert r.status_code == 404

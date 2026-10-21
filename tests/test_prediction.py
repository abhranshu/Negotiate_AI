def _make_case(client, auth_headers, amount=300000):
    r = client.post(
        "/api/cases",
        json={"dispute_type": "delayed_payment", "claim_amount": amount, "overdue_days": 80},
        headers=auth_headers,
    )
    return r.json()["id"]


def test_predict_returns_all_fields(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    r = client.post(f"/api/cases/{case_id}/predict", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    for field in (
        "settlement_probability",
        "settlement_range_low",
        "settlement_range_high",
        "adjudication_days",
        "confidence_band",
        "key_factors",
        "recommendation",
        "is_fallback",
    ):
        assert field in body, f"missing {field}"


def test_predict_marks_fallback_explicitly(client, auth_headers):
    """Module 3 output must always say whether it is real ML or a fallback."""
    case_id = _make_case(client, auth_headers)
    body = client.post(f"/api/cases/{case_id}/predict", headers=auth_headers).json()
    assert isinstance(body["is_fallback"], bool)
    if body["is_fallback"]:
        # A fallback must be clearly labelled, never silent.
        assert "FALLBACK" in body["recommendation"]


def test_predict_persists_to_case(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    client.post(f"/api/cases/{case_id}/predict", headers=auth_headers)
    case = client.get(f"/api/cases/{case_id}", headers=auth_headers).json()
    assert case["settlement_probability"] is not None

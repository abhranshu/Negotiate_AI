"""Guards against silently fabricated AI output.

These tests fail if someone re-introduces a fallback that is indistinguishable
from real module output. They are intentionally about the *contract* (schemas +
labelled fallback constants), not about model quality.
"""


def test_response_schemas_expose_fallback_flags():
    from api.schemas.case import NegotiateResponse, PredictionOut

    assert "is_fallback" in PredictionOut.model_fields
    assert "is_fallback" in NegotiateResponse.model_fields


def test_negotiate_fallback_constant_is_labelled():
    from api.routes.negotiate import _FALLBACK_RESULT

    assert _FALLBACK_RESULT.get("is_fallback") is True


def test_prediction_fallback_is_labelled(client, auth_headers):
    """If Module 3 falls back, the recommendation must say so explicitly."""
    case_id = client.post(
        "/api/cases",
        json={"dispute_type": "delayed_payment", "claim_amount": 100000},
        headers=auth_headers,
    ).json()["id"]

    body = client.post(f"/api/cases/{case_id}/predict", headers=auth_headers).json()
    if body["is_fallback"]:
        assert "FALLBACK" in body["recommendation"]
    else:
        assert body["recommendation"]

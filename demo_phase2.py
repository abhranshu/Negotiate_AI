"""
Phase 2 live-proof script for NegotiateAI backend.

Runs a complete API smoke flow using FastAPI TestClient:
1) Register claimant + respondent
2) Login and get JWT tokens
3) Create a case
4) Run outcome prediction (Module 3 integration path)
5) Send negotiation message (Module 4 integration path)
6) Force agreement amount for demo and generate settlement (Module 5 path)

Usage:
    python demo_phase2.py
"""
import os
from pathlib import Path

# Isolate demo DB from normal development DB
os.environ["DATABASE_URL"] = "sqlite:///./phase2_demo.db"
db_file = Path("phase2_demo.db")
if db_file.exists():
    db_file.unlink()

from fastapi.testclient import TestClient

from api.main import app
from api.database import SessionLocal, Base, engine
from api.models.case import Case, CaseStatus


def _print_step(title: str) -> None:
    print(f"\n=== {title} ===")


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    # Ensure tables exist for TestClient-based execution
    Base.metadata.create_all(bind=engine)

    client = TestClient(app)

    claimant_payload = {
        "email": "claimant.demo@negotiateai.in",
        "full_name": "Claimant Demo",
        "password": "DemoPass@123",
        "role": "claimant",
        "company_name": "Demo MSME Pvt Ltd",
        "udyam_number": "UDYAM-UP-00-0000000",
        "gstin": "22AAAAA0000A1Z5",
        "phone": "9000000001",
    }
    respondent_payload = {
        "email": "respondent.demo@negotiateai.in",
        "full_name": "Respondent Demo",
        "password": "DemoPass@123",
        "role": "respondent",
        "company_name": "Demo Buyer Ltd",
        "gstin": "27BBBBB1111B2Z6",
        "phone": "9000000002",
    }

    _print_step("Register users")
    r1 = client.post("/api/auth/register", json=claimant_payload)
    r2 = client.post("/api/auth/register", json=respondent_payload)
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text
    print("Registered claimant + respondent")

    _print_step("Login users")
    login_claimant = client.post(
        "/api/auth/login",
        data={"username": claimant_payload["email"], "password": claimant_payload["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    login_respondent = client.post(
        "/api/auth/login",
        data={"username": respondent_payload["email"], "password": respondent_payload["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_claimant.status_code == 200, login_claimant.text
    assert login_respondent.status_code == 200, login_respondent.text
    claimant_token = login_claimant.json()["access_token"]
    respondent_token = login_respondent.json()["access_token"]
    print("JWT login successful for both users")

    _print_step("Create case")
    case_payload = {
        "dispute_type": "delayed_payment",
        "claim_amount": 250000.0,
        "overdue_days": 90,
        "description": "Invoice overdue beyond agreed payment terms.",
        "state": "UP",
        "industry": "manufacturing",
        "respondent_email": respondent_payload["email"],
    }
    create_case = client.post("/api/cases", json=case_payload, headers=_auth_headers(claimant_token))
    assert create_case.status_code == 201, create_case.text
    case_data = create_case.json()
    case_id = case_data["id"]
    print(f"Case created: {case_data['case_number']} ({case_id})")

    _print_step("Run prediction")
    prediction = client.post(f"/api/cases/{case_id}/predict", headers=_auth_headers(claimant_token))
    assert prediction.status_code == 200, prediction.text
    pred = prediction.json()
    print(
        "Prediction OK | settlement_probability="
        f"{pred['settlement_probability']:.2f}, "
        f"range=({pred['settlement_range_low']:.2f}, {pred['settlement_range_high']:.2f})"
    )

    _print_step("Negotiation message")
    negotiate = client.post(
        f"/api/cases/{case_id}/negotiate",
        json={"text": "We can settle quickly if payment is made this month.", "offer": 200000.0},
        headers=_auth_headers(claimant_token),
    )
    assert negotiate.status_code == 200, negotiate.text
    nego = negotiate.json()
    print(f"Mediator response received | phase={nego['phase']}, round={nego['round']}")

    _print_step("Prepare settlement amount for demo")
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        assert case is not None
        case.agreement_amount = 210000.0
        case.status = CaseStatus.agreement
        db.commit()
    finally:
        db.close()
    print("Agreement amount set to 210000.0 INR")

    _print_step("Generate settlement")
    settlement = client.post(f"/api/cases/{case_id}/settlement", headers=_auth_headers(claimant_token))
    assert settlement.status_code == 200, settlement.text
    data = settlement.json()
    print(f"Settlement generated | valid={data['is_valid']} | agreement_id={data['agreement_id']}")

    _print_step("Demo complete")
    print("Phase 2 backend flow is working end-to-end.")


if __name__ == "__main__":
    main()

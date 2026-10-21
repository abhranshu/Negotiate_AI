"""
Settlement agreement route — triggers Module 5 (SettlementGenerator).
POST /api/cases/{case_id}/settlement  — Generate a settlement agreement
GET  /api/cases/{case_id}/settlement  — Fetch an existing agreement
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.case import Case, CaseStatus, CASE_WITH_PARTIES
from api.models.user import User
from api.schemas.case import SettlementOut
from api.auth import get_current_user

router = APIRouter(prefix="/api/cases", tags=["Settlement"])


def _party_details(user: User) -> dict:
    """Map a User row to the PartyDetails fields the generator needs."""
    return {
        "name":    user.full_name or "Not provided",
        "address": user.company_name or "Not provided",
        "gstin":   user.gstin,
        "udyam_number": user.udyam_number,
    }


def _build_agreement(case: Case) -> "SettlementAgreement":
    """Assemble a SettlementAgreement from the case row (falls back to placeholders)."""
    from AIML.settlement_generator import (
        SettlementAgreement, PartyDetails, SettlementTerms,
    )

    claimant   = _party_details(case.claimant) if case.claimant else {}
    respondent = _party_details(case.respondent) if case.respondent else {}

    agreed = case.agreement_amount or (case.claim_amount or 0.0)

    return SettlementAgreement(
        agreement_id = f"NAIODR-{case.case_number or case.id}",
        date         = datetime.now().strftime("%d %B %Y"),
        claimant     = PartyDetails(
            name=claimant.get("name", "Claimant"),
            address=claimant.get("address", "Not provided"),
            gstin=claimant.get("gstin"),
            udyam_number=claimant.get("udyam_number"),
        ),
        respondent   = PartyDetails(
            name=respondent.get("name", "Respondent"),
            address=respondent.get("address", "Not provided"),
            gstin=respondent.get("gstin"),
        ),
        terms        = SettlementTerms(agreed_amount=agreed),
        dispute_type = case.dispute_type.value if case.dispute_type else "delayed_payment",
        original_claim = case.claim_amount or agreed,
    )


def _serialize(agreement) -> dict:
    """Return the agreement as a JSON-serializable dict for the response."""
    return {
        "agreement_id":     agreement.agreement_id,
        "date":             agreement.date,
        "dispute_type":     agreement.dispute_type,
        "original_claim":   agreement.original_claim,
        "agreed_amount":    agreement.terms.agreed_amount,
        "agreement_text":   agreement.agreement_text,
        "is_valid":         agreement.is_valid,
        "validation_notes": agreement.validation_notes,
    }


@router.post("/{case_id}/settlement", response_model=SettlementOut)
def generate_settlement(
    case_id:      str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    Generate a legally valid settlement agreement for a settled case.
    Requires the negotiation to have reached an agreement amount.
    """
    # Parties are needed to fill in the agreement: load them with the case
    # (previously two lazy SELECTs on top of this one).
    case = (
        db.query(Case)
        .options(*CASE_WITH_PARTIES)
        .filter(Case.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id and case.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    if not case.agreement_amount:
        raise HTTPException(
            status_code=400,
            detail="No agreement amount yet. Complete negotiation first to reach a settlement figure.",
        )

    from AIML.settlement_generator import SettlementGenerator

    agreement = _build_agreement(case)
    # Template mode (deterministic, no external LLM/API dependency) — the
    # generated text passes the built-in legal validator.
    generator = SettlementGenerator()
    result = generator.generate_from_template(agreement)
    agreement.agreement_text = result

    # Validate and persist
    is_valid, notes = generator.validator.validate(agreement)
    agreement.is_valid         = is_valid
    agreement.validation_notes = notes

    case.agreement_text  = agreement.agreement_text
    case.agreement_valid = is_valid
    if case.status != CaseStatus.closed:
        case.status = CaseStatus.closed
    db.commit()

    return _serialize(agreement)


@router.get("/{case_id}/settlement", response_model=SettlementOut)
def get_settlement(
    case_id:      str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Return the previously generated settlement agreement, if any."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id and case.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    if not case.agreement_text:
        raise HTTPException(status_code=404, detail="No settlement found — generate one first")

    return {
        "agreement_id":     f"NAIODR-{case.case_number or case.id}",
        "date":             case.updated_at.strftime("%d %B %Y") if case.updated_at else "",
        "dispute_type":     case.dispute_type.value if case.dispute_type else "delayed_payment",
        "original_claim":   case.claim_amount or 0.0,
        "agreed_amount":    case.agreement_amount or 0.0,
        "agreement_text":   case.agreement_text,
        "is_valid":         bool(case.agreement_valid),
        "validation_notes": [],
    }

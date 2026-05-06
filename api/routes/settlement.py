"""
Settlement generation route — triggers Module 5.
POST /api/cases/{case_id}/settlement  — Generate PDF-ready settlement agreement
GET  /api/cases/{case_id}/settlement  — Retrieve saved agreement text
"""
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.case import Case, CaseStatus
from api.models.user import User
from api.auth import get_current_user

router = APIRouter(prefix="/api/cases", tags=["Settlement"])


class SettlementOut(BaseModel):
    agreement_id:     str
    is_valid:         bool
    validation_notes: list
    agreement_text:   str
    agreed_amount:    float


def _generate_settlement(case: Case) -> dict:
    try:
        from settlement_generator import (
            SettlementGenerator, SettlementAgreement,
            PartyDetails, SettlementTerms
        )

        claimant_user   = case.claimant
        respondent_user = case.respondent

        agreement = SettlementAgreement(
            agreement_id  = f"NAI-{case.case_number}-SETTLE",
            date          = datetime.now().strftime("%d %B %Y"),
            claimant      = PartyDetails(
                name    = claimant_user.company_name or claimant_user.full_name,
                address = "As per records",
                gstin   = claimant_user.gstin,
                udyam_number = claimant_user.udyam_number,
            ),
            respondent    = PartyDetails(
                name    = respondent_user.company_name or respondent_user.full_name if respondent_user else "Respondent",
                address = "As per records",
                gstin   = respondent_user.gstin if respondent_user else None,
            ),
            terms         = SettlementTerms(
                agreed_amount  = case.agreement_amount or case.claim_amount,
                interest_waiver= True,
            ),
            dispute_type  = case.dispute_type.value if case.dispute_type else "delayed_payment",
            original_claim= case.claim_amount or 0,
        )

        gen    = SettlementGenerator(use_llm=False)
        result = asyncio.get_event_loop().run_until_complete(gen.generate(agreement))

        return {
            "agreement_id":     agreement.agreement_id,
            "is_valid":         result.is_valid,
            "validation_notes": result.validation_notes,
            "agreement_text":   result.agreement_text,
            "agreed_amount":    case.agreement_amount or case.claim_amount,
        }
    except Exception as exc:
        return {
            "agreement_id":     f"NAI-{case.case_number}-SETTLE",
            "is_valid":         False,
            "validation_notes": [f"Module 5 unavailable: {exc}"],
            "agreement_text":   "Settlement agreement generation requires full ML stack.",
            "agreed_amount":    case.agreement_amount or 0,
        }


@router.post("/{case_id}/settlement", response_model=SettlementOut)
def generate_settlement(
    case_id:      str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Generate a legally valid settlement agreement via Module 5."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only claimant can generate settlement")
    if not case.agreement_amount:
        raise HTTPException(status_code=400, detail="No agreed amount yet. Complete negotiation first.")

    result = _generate_settlement(case)

    case.agreement_text  = result["agreement_text"]
    case.agreement_valid = result["is_valid"]
    case.status          = CaseStatus.closed
    db.commit()

    return result


@router.get("/{case_id}/settlement", response_model=SettlementOut)
def get_settlement(
    case_id:      str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Return the previously generated settlement agreement."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not case.agreement_text:
        raise HTTPException(status_code=404, detail="No settlement generated yet")
    return {
        "agreement_id":     f"NAI-{case.case_number}-SETTLE",
        "is_valid":         case.agreement_valid or False,
        "validation_notes": [],
        "agreement_text":   case.agreement_text,
        "agreed_amount":    case.agreement_amount or 0,
    }

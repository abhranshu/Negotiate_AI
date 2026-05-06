"""
Negotiation chat route — triggers Module 4 (NegotiationSession).
POST /api/cases/{case_id}/negotiate  — Send a message; get AI mediator response
GET  /api/cases/{case_id}/messages   — Retrieve full chat history
"""
import asyncio
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.case import Case, Message, CaseStatus
from api.models.user import User
from api.schemas.case import NegotiateRequest, NegotiateResponse, MessageOut
from api.auth import get_current_user

router = APIRouter(prefix="/api/cases", tags=["Negotiation"])

_SESSIONS: dict = {}   # in-memory session cache; swap for Redis in production


def _get_or_create_session(case: Case):
    try:
        from negotiation_ai import NegotiationSession, NegotiationState
        if case.id not in _SESSIONS:
            state = NegotiationState(
                case_id               = case.id,
                claim_amount          = case.claim_amount or 100_000,
                predicted_range       = (
                    case.settlement_range_low  or (case.claim_amount or 100_000) * 0.6,
                    case.settlement_range_high or (case.claim_amount or 100_000) * 0.9,
                ),
                settlement_probability= case.settlement_probability or 0.65,
            )
            _SESSIONS[case.id] = NegotiationSession(state, language="en")
        return _SESSIONS[case.id]
    except ImportError:
        return None


def _party_from_user(case: Case, user: User) -> str:
    if case.claimant_id == user.id:
        return "claimant"
    if case.respondent_id == user.id:
        return "respondent"
    raise HTTPException(status_code=403, detail="You are not a party to this case")


@router.post("/{case_id}/negotiate", response_model=NegotiateResponse)
def send_message(
    case_id:      str,
    payload:      NegotiateRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Send a negotiation message. Module 4 returns a mediator response."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    party_str = _party_from_user(case, current_user)
    if case.status in (CaseStatus.draft, CaseStatus.submitted):
        case.status = CaseStatus.in_progress

    session = _get_or_create_session(case)

    if session:
        from negotiation_ai import Party
        party_enum = Party.CLAIMANT if party_str == "claimant" else Party.RESPONDENT
        result = asyncio.get_event_loop().run_until_complete(
            session.process_message(party_enum, payload.text, payload.offer)
        )
    else:
        result = {
            "mediator_response":  "Thank you. The AI mediator will respond shortly.",
            "sentiment_detected": "neutral",
            "phase":              "bargaining",
            "round":              1,
            "agreement_reached":  False,
            "agreement_amount":   None,
            "strategy_hints":     {},
        }

    db.add(Message(case_id=case_id, party=party_str, text=payload.text,
                   offer=payload.offer, sentiment=result.get("sentiment_detected"),
                   phase=result.get("phase"), round_num=result.get("round")))
    db.add(Message(case_id=case_id, party="mediator", text=result["mediator_response"],
                   phase=result.get("phase"), round_num=result.get("round")))

    if result.get("agreement_reached") and result.get("agreement_amount"):
        case.agreement_amount = result["agreement_amount"]
        case.status           = CaseStatus.agreement

    db.commit()
    return result


@router.get("/{case_id}/messages", response_model=List[MessageOut])
def get_messages(
    case_id:      str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Return the full negotiation chat history for a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id and case.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")
    return sorted(case.messages, key=lambda m: m.timestamp)

"""
Case management routes.
POST /api/cases              — Create a new case
GET  /api/cases              — List all cases for the current user
GET  /api/cases/{id}         — Get full case detail
PATCH /api/cases/{id}/status — Update case status
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.case import Case, CaseStatus
from api.models.user import User
from api.schemas.case import CaseCreate, CaseOut, CaseListItem, CaseDescriptionUpdate
from api.auth import get_current_user

router = APIRouter(prefix="/api/cases", tags=["Cases"])


def _generate_case_number(db: Session) -> str:
    """Generate sequential case number like NAI-2025-0001.

    Uses the highest existing number for the year (not a count), so it keeps
    incrementing correctly even after deletions. Callers retry on the unique
    constraint for true concurrency safety.
    """
    from datetime import datetime
    year   = datetime.utcnow().year
    prefix = f"NAI-{year}-"
    last = (
        db.query(Case.case_number)
        .filter(Case.case_number.like(f"{prefix}%"))
        .order_by(Case.case_number.desc())
        .first()
    )
    seq = int(last[0].rsplit("-", 1)[1]) + 1 if last and last[0] else 1
    return f"{prefix}{seq:04d}"


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    db:      Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Open a new dispute case for the authenticated claimant."""
    # Optionally link respondent by email
    respondent = None
    if payload.respondent_email:
        respondent = db.query(User).filter(User.email == payload.respondent_email).first()
        # If respondent not yet registered, we leave respondent_id NULL for now

    # Retry on unique-case-number collisions (parallel creates can race on the
    # same sequence number). Max 3 attempts, then surface a clean 500.
    for _attempt in range(3):
        case = Case(
            id            = str(uuid.uuid4()),
            case_number   = _generate_case_number(db),
            claimant_id   = current_user.id,
            respondent_id = respondent.id if respondent else None,
            dispute_type  = payload.dispute_type,
            claim_amount  = payload.claim_amount,
            overdue_days  = payload.overdue_days,
            description   = payload.description,
            state         = payload.state,
            industry      = payload.industry,
            status        = CaseStatus.draft,
        )
        db.add(case)
        try:
            db.commit()
            break
        except IntegrityError:
            db.rollback()
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not allocate a unique case number — try again.",
        )
    db.refresh(case)
    return case


@router.get("", response_model=List[CaseListItem])
def list_cases(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Return all cases where the user is claimant or respondent."""
    cases = (
        db.query(Case)
        .filter(
            (Case.claimant_id == current_user.id) |
            (Case.respondent_id == current_user.id)
        )
        .order_by(Case.created_at.desc())
        .all()
    )
    return cases


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case_id:      str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Return full details for a single case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id and case.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to view this case")
    return case


@router.patch("/{case_id}/status", response_model=CaseOut)
def update_status(
    case_id:      str,
    new_status:   CaseStatus,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Manually update a case status (e.g., mark as escalated)."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the claimant can update case status")
    case.status = new_status
    db.commit()
    db.refresh(case)
    return case


@router.patch("/{case_id}/description", response_model=CaseOut)
def update_description(
    case_id:      str,
    payload:      CaseDescriptionUpdate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Update the case description, for example from voice dictation."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the claimant can update case description")
    case.description = payload.description.strip()
    db.commit()
    db.refresh(case)
    return case

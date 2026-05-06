"""
Pydantic schemas for Case, Document, Message, Predict, Negotiate endpoints.
"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

from api.models.case import CaseStatus, DisputeType


# ─── Case ─────────────────────────────────────────────────────────────────────

class CaseCreate(BaseModel):
    dispute_type:  Optional[DisputeType] = None
    claim_amount:  Optional[float]       = None
    overdue_days:  Optional[int]         = None
    description:   Optional[str]        = None
    state:         Optional[str]        = None    # e.g. "MH"
    industry:      Optional[str]        = None
    respondent_email: Optional[str]     = None    # invite respondent by email


class CaseOut(BaseModel):
    id:           str
    case_number:  Optional[str]
    status:       CaseStatus
    dispute_type: Optional[DisputeType]
    claim_amount: Optional[float]
    overdue_days: Optional[int]
    description:  Optional[str]
    state:        Optional[str]
    industry:     Optional[str]
    created_at:   datetime
    # Module outputs
    case_strength:             Optional[str]
    settlement_probability:    Optional[float]
    settlement_range_low:      Optional[float]
    settlement_range_high:     Optional[float]
    adjudication_days:         Optional[int]
    prediction_recommendation: Optional[str]
    agreement_amount:          Optional[float]

    class Config:
        from_attributes = True


class CaseListItem(BaseModel):
    id:           str
    case_number:  Optional[str]
    status:       CaseStatus
    dispute_type: Optional[DisputeType]
    claim_amount: Optional[float]
    created_at:   datetime

    class Config:
        from_attributes = True


# ─── Document ─────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id:          str
    filename:    str
    doc_type:    Optional[str]
    confidence:  Optional[float]
    is_valid:    bool
    issues:      Optional[List[str]]
    key_fields:  Optional[Any]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ─── Message / Chat ───────────────────────────────────────────────────────────

class MessageCreate(BaseModel):
    text:  str
    offer: Optional[float] = None   # INR offer amount if applicable


class MessageOut(BaseModel):
    id:        str
    party:     str
    text:      str
    offer:     Optional[float]
    sentiment: Optional[str]
    phase:     Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


# ─── Prediction ───────────────────────────────────────────────────────────────

class PredictionOut(BaseModel):
    settlement_probability:  float
    settlement_range_low:    float
    settlement_range_high:   float
    adjudication_days:       int
    confidence_band:         str
    key_factors:             List[Any]
    recommendation:          str


# ─── Negotiate ────────────────────────────────────────────────────────────────

class NegotiateRequest(BaseModel):
    text:  str
    offer: Optional[float] = None


class NegotiateResponse(BaseModel):
    mediator_response: str
    sentiment_detected: str
    phase:             str
    round:             int
    agreement_reached: bool
    agreement_amount:  Optional[float]
    strategy_hints:    Any

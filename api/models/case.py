"""
Case, Document, and Message ORM models.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, Boolean,
    DateTime, ForeignKey, JSON, Enum as SAEnum, Text
)
from sqlalchemy.orm import relationship
import enum

from api.database import Base


class CaseStatus(str, enum.Enum):
    draft        = "draft"
    submitted    = "submitted"
    in_progress  = "in_progress"
    agreement    = "agreement"
    closed       = "closed"
    escalated    = "escalated"   # sent to MSEFC for adjudication


class DisputeType(str, enum.Enum):
    delayed_payment  = "delayed_payment"
    non_payment      = "non_payment"
    short_payment    = "short_payment"
    quality_dispute  = "quality_dispute"
    quantity_dispute = "quantity_dispute"
    contract_breach  = "contract_breach"


class Case(Base):
    __tablename__ = "cases"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number  = Column(String, unique=True, index=True)   # e.g. NAI-2025-001

    # Parties
    claimant_id   = Column(String, ForeignKey("users.id"), nullable=False)
    respondent_id = Column(String, ForeignKey("users.id"), nullable=True)   # may be added later

    # Dispute details
    dispute_type  = Column(SAEnum(DisputeType), nullable=True)
    claim_amount  = Column(Float, nullable=True)
    overdue_days  = Column(Integer, nullable=True)
    description   = Column(Text, nullable=True)
    state         = Column(String, nullable=True)   # Indian state code e.g. "MH"
    industry      = Column(String, nullable=True)

    # Status & lifecycle
    status        = Column(SAEnum(CaseStatus), default=CaseStatus.draft)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Module 2 outputs (stored as JSON)
    doc_gap_analysis   = Column(JSON, nullable=True)
    case_summary_text  = Column(Text, nullable=True)
    case_strength      = Column(String, nullable=True)   # "strong" | "moderate" | "weak"

    # Module 3 outputs
    settlement_probability  = Column(Float, nullable=True)
    settlement_range_low    = Column(Float, nullable=True)
    settlement_range_high   = Column(Float, nullable=True)
    adjudication_days       = Column(Integer, nullable=True)
    prediction_confidence   = Column(String, nullable=True)
    prediction_recommendation = Column(Text, nullable=True)

    # Module 5 outputs
    agreement_text    = Column(Text, nullable=True)
    agreement_amount  = Column(Float, nullable=True)
    agreement_valid   = Column(Boolean, nullable=True)

    # Relationships
    claimant   = relationship("User", back_populates="cases_as_claimant",   foreign_keys=[claimant_id])
    respondent = relationship("User", back_populates="cases_as_respondent", foreign_keys=[respondent_id])
    documents  = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    messages   = relationship("Message",  back_populates="case", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id      = Column(String, ForeignKey("cases.id"), nullable=False)

    filename     = Column(String, nullable=False)
    file_path    = Column(String, nullable=False)
    file_size_kb = Column(Integer, nullable=True)

    # Module 2 classification result
    doc_type     = Column(String, nullable=True)   # "invoice" | "purchase_order" | ...
    confidence   = Column(Float, nullable=True)
    extracted_text = Column(Text, nullable=True)
    key_fields   = Column(JSON, nullable=True)
    is_valid     = Column(Boolean, default=True)
    issues       = Column(JSON, nullable=True)

    uploaded_at  = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="documents")


class Message(Base):
    __tablename__ = "messages"

    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id    = Column(String, ForeignKey("cases.id"), nullable=False)

    party      = Column(String, nullable=False)   # "claimant" | "respondent" | "mediator"
    text       = Column(Text, nullable=False)
    language   = Column(String, default="en")
    offer      = Column(Float, nullable=True)     # INR offer amount if present

    # Module 4 analysis results
    sentiment  = Column(String, nullable=True)
    phase      = Column(String, nullable=True)
    round_num  = Column(Integer, nullable=True)

    timestamp  = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="messages")

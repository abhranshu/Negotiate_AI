"""
User model — supports Claimant and Respondent roles.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from api.database import Base


class UserRole(str, enum.Enum):
    claimant   = "claimant"
    respondent = "respondent"
    admin      = "admin"


class User(Base):
    __tablename__ = "users"

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email       = Column(String, unique=True, nullable=False, index=True)
    full_name   = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role        = Column(SAEnum(UserRole), nullable=False, default=UserRole.claimant)
    company_name    = Column(String, nullable=True)
    udyam_number    = Column(String, nullable=True)   # MSME registration
    gstin           = Column(String, nullable=True)
    phone           = Column(String, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cases_as_claimant   = relationship("Case", back_populates="claimant",   foreign_keys="Case.claimant_id")
    cases_as_respondent = relationship("Case", back_populates="respondent", foreign_keys="Case.respondent_id")

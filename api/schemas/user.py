"""
Pydantic schemas for User & Auth endpoints.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from api.models.user import UserRole


class UserCreate(BaseModel):
    email:        EmailStr
    full_name:    str
    password:     str
    role:         UserRole       = UserRole.claimant
    company_name: Optional[str] = None
    udyam_number: Optional[str] = None
    gstin:        Optional[str] = None
    phone:        Optional[str] = None


class UserOut(BaseModel):
    id:           str
    email:        str
    full_name:    str
    role:         UserRole
    company_name: Optional[str]
    udyam_number: Optional[str]
    gstin:        Optional[str]

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None

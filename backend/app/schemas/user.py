from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base user schema."""

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""

    email: EmailStr
    password: str
    username: str
    role: Optional[str] = None


class UserLogin(BaseModel):
    """User login schema."""

    username: str
    password: str


class UserResponse(UserBase):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    recommendation_count: int
    last_recommendation_date: Optional[datetime] = None
    daily_limit: int
    role: str


class Token(BaseModel):
    """Token schema."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""

    username: Optional[str] = None
    id: Optional[str] = None

from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""

    email: EmailStr
    password: str
    username: str


class UserLogin(BaseModel):
    """User login schema."""

    username: str
    password: str


class UserResponse(UserBase):
    """User response schema."""

    id: int
    is_active: bool

    class Config:
        orm_mode = True


class Token(BaseModel):
    """Token schema."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""

    username: Optional[str] = None

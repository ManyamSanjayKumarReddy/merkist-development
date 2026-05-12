import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

INDIAN_PHONE_RE = re.compile(r"^\+91[6-9]\d{9}$")


class UserRegister(BaseModel):
    name: str
    username: str
    email: EmailStr
    phone_number: str
    password: str

    @field_validator("phone_number")
    @classmethod
    def validate_indian_phone(cls, v: str) -> str:
        if not INDIAN_PHONE_RE.match(v):
            raise ValueError("Must be a valid Indian number in +91XXXXXXXXXX format")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError("3–30 characters, alphanumeric or underscore only")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: str
    role: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatusResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    role: str
    member_since: datetime

    class Config:
        from_attributes = True


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
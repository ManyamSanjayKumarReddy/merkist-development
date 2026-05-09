from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IGAccountResponse(BaseModel):
    id: int
    instagram_user_id: str
    username: str
    profile_picture_url: Optional[str] = None
    followers_count: Optional[int] = None
    token_expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class IGAccountListResponse(BaseModel):
    accounts: list[IGAccountResponse]
    total: int


class OAuthURLResponse(BaseModel):
    url: str


class DisconnectResponse(BaseModel):
    message: str
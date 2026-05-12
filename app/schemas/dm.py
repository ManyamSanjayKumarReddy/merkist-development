from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: int
    ig_message_id: str
    sender_type: str
    sender_ig_id: Optional[str] = None
    text: Optional[str] = None
    timestamp: Optional[datetime] = None
    is_read: bool

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    ig_conversation_id: str
    participant_username: Optional[str] = None
    participant_ig_id: Optional[str] = None
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    unread_count: int
    is_archived: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    conversation: ConversationResponse


class ReplyRequest(BaseModel):
    text: str


class ReplyResponse(BaseModel):
    message_id: str
    recipient_id: str
    status: str = "sent"


class SyncResponse(BaseModel):
    synced: int
    message: str
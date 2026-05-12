from enum import Enum
from tortoise import fields
from tortoise.models import Model


class SenderType(str, Enum):
    USER = "user"        # the IG business account owner
    CONTACT = "contact"  # the person who messaged them


class IGConversation(Model):
    id = fields.IntField(pk=True)
    account = fields.ForeignKeyField("models.IGAccount", related_name="conversations")
    ig_conversation_id = fields.CharField(max_length=255, unique=True)
    participant_username = fields.CharField(max_length=150, null=True)
    participant_ig_id = fields.CharField(max_length=100, null=True)
    last_message_at = fields.DatetimeField(null=True)
    last_message_preview = fields.CharField(max_length=255, null=True)
    unread_count = fields.IntField(default=0)
    is_archived = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "ig_conversations"


class IGMessage(Model):
    id = fields.IntField(pk=True)
    conversation = fields.ForeignKeyField("models.IGConversation", related_name="messages")
    ig_message_id = fields.CharField(max_length=255, unique=True)
    sender_type = fields.CharEnumField(SenderType)
    sender_ig_id = fields.CharField(max_length=255, null=True)
    text = fields.TextField(null=True)
    timestamp = fields.DatetimeField(null=True)
    is_read = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "ig_messages"
        ordering = ["timestamp"]
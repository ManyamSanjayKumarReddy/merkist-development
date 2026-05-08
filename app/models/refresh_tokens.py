import uuid
from tortoise import fields
from tortoise.models import Model

class RefreshToken(Model):
    id = fields.IntField(pk=True)
    token = fields.CharField(max_length=512, unique=True)
    user = fields.ForeignKeyField("models.User", related_name="refresh_tokens")
    expires_at = fields.DatetimeField()
    family_id = fields.UUIDField(default=uuid.uuid4)
    is_revoked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "refresh_tokens"
from tortoise import fields
from tortoise.models import Model

class IGAccount(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="ig_accounts")
    instagram_user_id = fields.CharField(max_length=100, unique=True)
    username = fields.CharField(max_length=150)
    profile_picture_url = fields.TextField(null=True)
    followers_count = fields.IntField(null=True)
    access_token = fields.TextField()
    token_expires_at = fields.DatetimeField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "ig_accounts"

class IGMedia(Model):
    id = fields.IntField(pk=True)
    account = fields.ForeignKeyField("models.IGAccount", related_name="media")
    instagram_media_id = fields.CharField(max_length=100, unique=True)
    media_type = fields.CharField(max_length=20)
    caption = fields.TextField(null=True)
    media_url = fields.TextField(null=True)
    permalink = fields.TextField(null=True)
    timestamp = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "ig_media"
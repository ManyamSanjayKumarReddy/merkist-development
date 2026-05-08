from enum import Enum
from tortoise import fields
from tortoise.models import Model

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=150)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    phone_number = fields.CharField(max_length=13, unique=True)
    hashed_password = fields.CharField(max_length=255)
    role = fields.CharEnumField(UserRole, default=UserRole.USER)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"
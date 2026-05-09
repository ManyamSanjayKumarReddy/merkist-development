import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def _prepare_password(password: str) -> str:
    """SHA-256 pre-hash to bypass bcrypt 72-byte limit"""
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare_password(password).encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_prepare_password(plain_password).encode(), hashed_password.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            return None
        return {"user_id": int(user_id), "role": role}
    except JWTError:
        return None


def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def is_refresh_token_expired(expires_at: datetime) -> bool:
    return datetime.now(timezone.utc) > expires_at.astimezone(timezone.utc)
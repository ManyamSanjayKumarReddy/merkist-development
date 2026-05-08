import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.exceptions import IntegrityError

from app.config import get_settings
from app.core.dependencies import get_current_active_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    is_refresh_token_expired,
    verify_password,
)
from app.models.refresh_tokens import RefreshToken
from app.models.user import User, UserRole
from app.schemas.user import RefreshTokenRequest, TokenPair, UserLogin, UserRegister, UserResponse

settings = get_settings()
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    try:
        user = await User.create(
            name=payload.name,
            username=payload.username.lower(),
            email=payload.email.lower(),
            phone_number=payload.phone_number,
            hashed_password=hash_password(payload.password),
            role=UserRole.USER,
        )
    except IntegrityError as e:
        err = str(e).lower()
        if "username" in err:
            raise HTTPException(status_code=409, detail="Username already taken")
        if "email" in err:
            raise HTTPException(status_code=409, detail="Email already registered")
        if "phone" in err:
            raise HTTPException(status_code=409, detail="Phone number already registered")
        raise HTTPException(status_code=409, detail="Account already exists")
    return user


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin):
    user = await User.get_or_none(username=payload.username.lower())
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token_str = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    await RefreshToken.create(
        token=refresh_token_str,
        user=user,
        expires_at=expires_at,
        family_id=uuid.uuid4(),
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token_str)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshTokenRequest):
    record = await RefreshToken.get_or_none(token=payload.refresh_token).prefetch_related("user")
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if record.is_revoked:
        # Reuse detected — invalidate entire family
        await RefreshToken.filter(family_id=record.family_id, is_revoked=False).update(is_revoked=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected. All sessions have been invalidated.",
        )

    if is_refresh_token_expired(record.expires_at):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired")

    # Rotate — revoke old, issue new in same family
    record.is_revoked = True
    await record.save()

    access_token = create_access_token(
        data={"sub": str(record.user.id), "role": record.user.role.value},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    new_refresh_token_str = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    await RefreshToken.create(
        token=new_refresh_token_str,
        user=record.user,
        expires_at=expires_at,
        family_id=record.family_id,  # inherit same family
    )
    return TokenPair(access_token=access_token, refresh_token=new_refresh_token_str)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    payload: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user),
):
    record = await RefreshToken.get_or_none(token=payload.refresh_token, user=current_user)
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    record.is_revoked = True
    await record.save()
    return {"message": "Successfully logged out"}


@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all(current_user: User = Depends(get_current_active_user)):
    """Revoke all sessions — logout from every device."""
    await RefreshToken.filter(user=current_user, is_revoked=False).update(is_revoked=True)
    return {"message": "All sessions have been terminated"}
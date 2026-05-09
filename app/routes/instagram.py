import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.core.dependencies import get_current_active_user
from app.models.instagram import IGAccount
from app.models.user import User
from app.schemas.instagram import (
    DisconnectResponse,
    IGAccountListResponse,
    IGAccountResponse,
    OAuthURLResponse,
)
from app.services.instagram import (
    build_oauth_url,
    calculate_token_expiry,
    exchange_code_for_token,
    exchange_for_long_lived_token,
    fetch_instagram_profile,
)

settings = get_settings()
auth_router = APIRouter()   # mounted at /auth/instagram
router = APIRouter()        # mounted at /instagram

# Temporary in-memory state store — replace with Redis in Phase 6
_oauth_states: dict[str, int] = {}


@auth_router.get("/connect", response_model=OAuthURLResponse)
async def get_instagram_oauth_url(
    current_user: User = Depends(get_current_active_user),
):
    """
    Step 1: Generate Instagram OAuth URL.
    Frontend opens this URL in a new tab or redirect.
    """
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = current_user.id
    url = build_oauth_url(state=state)
    print(url)
    return OAuthURLResponse(url=url)


@auth_router.get("/callback")
async def instagram_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None),
    error_reason: str = Query(None),
):
    """
    Step 2: Instagram redirects here after user grants permission.
    Exchanges code for tokens, fetches profile, saves IGAccount.
    Redirects user to dashboard/accounts on success.
    """
    if error:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard/accounts?error=access_denied"
        )

    user_id = _oauth_states.pop(state, None)
    if user_id is None:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard/accounts?error=invalid_state"
        )

    try:
        token_data = await exchange_code_for_token(code)
        short_lived_token = token_data["access_token"]
        instagram_user_id = str(token_data["user_id"])

        long_lived_data = await exchange_for_long_lived_token(short_lived_token)
        access_token = long_lived_data["access_token"]
        expires_in = long_lived_data.get("expires_in", 5183944)
        token_expires_at = calculate_token_expiry(expires_in)

        profile = await fetch_instagram_profile(access_token)
        username = profile.get("username", "")
        profile_picture_url = profile.get("profile_picture_url")
        followers_count = profile.get("followers_count")

    except ValueError:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard/accounts?error=token_exchange_failed"
        )

    existing = await IGAccount.get_or_none(instagram_user_id=instagram_user_id)

    if existing:
        existing.access_token = access_token
        existing.token_expires_at = token_expires_at
        existing.username = username
        existing.profile_picture_url = profile_picture_url
        existing.followers_count = followers_count
        existing.is_active = True
        await existing.save()
    else:
        user = await User.get(id=user_id)
        await IGAccount.create(
            user=user,
            instagram_user_id=instagram_user_id,
            username=username,
            profile_picture_url=profile_picture_url,
            followers_count=followers_count,
            access_token=access_token,
            token_expires_at=token_expires_at,
        )

    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/dashboard/accounts?connected=true"
    )


@router.get("/accounts", response_model=IGAccountListResponse)
async def list_instagram_accounts(
    current_user: User = Depends(get_current_active_user),
):
    """List all connected Instagram accounts for the current user."""
    accounts = await IGAccount.filter(user=current_user, is_active=True).order_by("-created_at")
    return IGAccountListResponse(
        accounts=[IGAccountResponse.model_validate(a) for a in accounts],
        total=len(accounts),
    )


@router.get("/accounts/{account_id}", response_model=IGAccountResponse)
async def get_instagram_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Get a single connected Instagram account."""
    account = await IGAccount.get_or_none(id=account_id, user=current_user, is_active=True)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram account not found",
        )
    return account


@router.post("/accounts/{account_id}/disconnect", response_model=DisconnectResponse)
async def disconnect_instagram_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Soft disconnect an Instagram account (is_active = False)."""
    account = await IGAccount.get_or_none(id=account_id, user=current_user, is_active=True)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram account not found",
        )
    account.is_active = False
    await account.save()
    return DisconnectResponse(message=f"@{account.username} has been disconnected")
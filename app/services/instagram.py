import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import get_settings

settings = get_settings()

INSTAGRAM_AUTH_URL = "https://www.instagram.com/oauth/authorize"
INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
INSTAGRAM_LONG_LIVED_TOKEN_URL = "https://graph.instagram.com/access_token"
INSTAGRAM_GRAPH_URL = "https://graph.instagram.com/v21.0"

SCOPES = "instagram_business_basic,instagram_manage_comments,instagram_business_manage_messages"


def build_oauth_url(state: str) -> str:
    """Build the Instagram OAuth consent screen URL."""
    params = (
        f"?client_id={settings.INSTAGRAM_APP_ID}"
        f"&redirect_uri={settings.INSTAGRAM_REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&response_type=code"
        f"&state={state}"
    )
    return INSTAGRAM_AUTH_URL + params


async def exchange_code_for_token(code: str) -> dict:
    """Exchange auth code for a short-lived token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            INSTAGRAM_TOKEN_URL,
            data={
                "client_id": settings.INSTAGRAM_APP_ID,
                "client_secret": settings.INSTAGRAM_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
                "code": code,
            },
        )

    if response.status_code != 200:
        raise ValueError(f"Token exchange failed: {response.text}")

    return response.json()  # {access_token, token_type, permissions, user_id}


async def exchange_for_long_lived_token(short_lived_token: str) -> dict:
    """Exchange short-lived token (1hr) for long-lived token (60 days)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            INSTAGRAM_LONG_LIVED_TOKEN_URL,
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": settings.INSTAGRAM_APP_SECRET,
                "access_token": short_lived_token,
            },
        )

    if response.status_code != 200:
        raise ValueError(f"Long-lived token exchange failed: {response.text}")

    data = response.json()  # {access_token, token_type, expires_in}
    return data


async def fetch_instagram_profile(access_token: str) -> dict:
    """Fetch profile info: id, username, profile_picture_url, followers_count."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INSTAGRAM_GRAPH_URL}/me",
            params={
                "fields": "id,username,profile_picture_url,followers_count",
                "access_token": access_token,
            },
        )

    if response.status_code != 200:
        raise ValueError(f"Profile fetch failed: {response.text}")

    return response.json()


def calculate_token_expiry(expires_in_seconds: int) -> datetime:
    """Calculate token expiry datetime from seconds offset."""
    return datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
import httpx
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings

settings = get_settings()

INSTAGRAM_GRAPH_URL = "https://graph.instagram.com/v21.0"


async def fetch_conversations(access_token: str, after: Optional[str] = None) -> dict:
    """
    Fetch DM conversations for the connected IG Business account.
    Returns paginated list of conversation objects.
    """
    params = {
        "platform": "instagram",
        "fields": "id,participants,updated_time,messages{id,message,from,created_time}",
        "access_token": access_token,
        "limit": 20,
    }
    if after:
        params["after"] = after

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{INSTAGRAM_GRAPH_URL}/me/conversations", params=params)

    if response.status_code != 200:
        raise ValueError(f"Fetch conversations failed: {response.text}")

    return response.json()


async def fetch_messages_for_conversation(
    access_token: str, conversation_id: str, after: Optional[str] = None
) -> dict:
    """
    Fetch messages within a specific conversation.
    """
    params = {
        "fields": "id,message,from,created_time,to",
        "access_token": access_token,
        "limit": 50,
    }
    if after:
        params["after"] = after

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INSTAGRAM_GRAPH_URL}/{conversation_id}/messages", params=params
        )

    if response.status_code != 200:
        raise ValueError(f"Fetch messages failed: {response.text}")

    return response.json()


async def send_dm(access_token: str, recipient_ig_id: str, text: str) -> dict:
    """
    Send a DM to a user on behalf of the connected IG Business account.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{INSTAGRAM_GRAPH_URL}/me/messages",
            params={"access_token": access_token},
            json={
                "recipient": {"id": recipient_ig_id},
                "message": {"text": text},
            },
        )

    if response.status_code != 200:
        raise ValueError(f"Send DM failed: {response.text}")

    return response.json()  # {message_id, recipient_id}


async def fetch_ig_user_info(access_token: str, ig_user_id: str) -> dict:
    """
    Fetch basic info of an IG user (to get username for participant display).
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INSTAGRAM_GRAPH_URL}/{ig_user_id}",
            params={
                "fields": "id,username,name,profile_pic",
                "access_token": access_token,
            },
        )

    if response.status_code != 200:
        return {}

    return response.json()
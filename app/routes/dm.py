from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_current_active_user
from app.models.instagram import IGAccount
from app.models.dm import IGConversation, IGMessage, SenderType
from app.models.user import User
from app.schemas.dm import (
    ConversationListResponse,
    ConversationResponse,
    MessageListResponse,
    MessageResponse,
    ReplyRequest,
    ReplyResponse,
    SyncResponse,
)
from app.services.dm import (
    fetch_conversations,
    fetch_messages_for_conversation,
    fetch_ig_user_info,
    send_dm,
)

router = APIRouter()


async def _get_account_or_404(account_id: int, user: User) -> IGAccount:
    account = await IGAccount.get_or_none(id=account_id, user=user, is_active=True)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instagram account not found")
    return account

@router.post("/{account_id}/conversations/sync", response_model=SyncResponse)
async def sync_conversations(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
):
    account = await _get_account_or_404(account_id, current_user)

    # First sync: use account created_at. Subsequent: use last_synced_at
    since = account.last_synced_at or account.created_at

    try:
        data = await fetch_conversations(account.access_token, since=since)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    conversations = data.get("data", [])
    synced = 0

    for conv in conversations:
        ig_conv_id = conv.get("id")
        if not ig_conv_id:
            continue

        participants = conv.get("participants", {}).get("data", [])
        contact = next(
            (p for p in participants if p.get("id") != account.instagram_user_id),
            None,
        )

        participant_ig_id = contact.get("id") if contact else None
        participant_username = contact.get("username") if contact else None

        if participant_ig_id and not participant_username:
            info = await fetch_ig_user_info(account.access_token, participant_ig_id)
            participant_username = info.get("username") or info.get("name")

        last_message_at = None
        updated_time = conv.get("updated_time")
        if updated_time:
            try:
                last_message_at = datetime.fromisoformat(updated_time.replace("Z", "+00:00"))
            except Exception:
                pass

        existing = await IGConversation.get_or_none(ig_conversation_id=ig_conv_id)
        if existing:
            existing.participant_username = participant_username or existing.participant_username
            existing.participant_ig_id = participant_ig_id or existing.participant_ig_id
            existing.last_message_at = last_message_at or existing.last_message_at
            await existing.save()
        else:
            await IGConversation.create(
                account=account,
                ig_conversation_id=ig_conv_id,
                participant_username=participant_username,
                participant_ig_id=participant_ig_id,
                last_message_at=last_message_at,
            )
            synced += 1

    # Update last synced timestamp
    account.last_synced_at = datetime.now(timezone.utc)
    await account.save()

    return SyncResponse(synced=synced, message=f"Synced {synced} new conversations, {len(conversations) - synced} updated")


@router.get("/{account_id}/conversations", response_model=ConversationListResponse)
async def list_conversations(
    account_id: int,
    archived: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
):
    """List all conversations for an IG account from local DB."""
    account = await _get_account_or_404(account_id, current_user)

    conversations = await IGConversation.filter(
        account=account, is_archived=archived
    ).order_by("-last_message_at")

    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(c) for c in conversations],
        total=len(conversations),
    )


@router.post("/{account_id}/conversations/{conv_id}/messages/sync", response_model=SyncResponse)
async def sync_messages(
    account_id: int,
    conv_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Pull latest messages from Instagram API for a conversation."""
    account = await _get_account_or_404(account_id, current_user)

    conversation = await IGConversation.get_or_none(id=conv_id, account=account)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    try:
        data = await fetch_messages_for_conversation(
            account.access_token, conversation.ig_conversation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    messages = data.get("data", [])
    synced = 0

    for msg in messages:
        ig_msg_id = msg.get("id")
        if not ig_msg_id:
            continue

        exists = await IGMessage.get_or_none(ig_message_id=ig_msg_id)
        if exists:
            continue

        sender_id = msg.get("from", {}).get("id")
        sender_type = (
            SenderType.USER
            if str(sender_id) == account.instagram_user_id
            else SenderType.CONTACT
        )

        timestamp = None
        if msg.get("created_time"):
            try:
                timestamp = datetime.fromisoformat(msg["created_time"].replace("Z", "+00:00"))
            except Exception:
                pass

        await IGMessage.create(
            conversation=conversation,
            ig_message_id=ig_msg_id,
            sender_type=sender_type,
            sender_ig_id=sender_id,
            text=msg.get("message"),
            timestamp=timestamp,
            is_read=sender_type == SenderType.USER,
        )
        synced += 1

    # Update unread count
    unread = await IGMessage.filter(conversation=conversation, is_read=False).count()
    conversation.unread_count = unread
    await conversation.save()

    return SyncResponse(synced=synced, message=f"Synced {synced} new messages")


@router.get("/{account_id}/conversations/{conv_id}/messages", response_model=MessageListResponse)
async def get_messages(
    account_id: int,
    conv_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Get all messages for a conversation from local DB."""
    account = await _get_account_or_404(account_id, current_user)

    conversation = await IGConversation.get_or_none(id=conv_id, account=account)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = await IGMessage.filter(conversation=conversation).order_by("timestamp")

    return MessageListResponse(
        messages=[MessageResponse.model_validate(m) for m in messages],
        total=len(messages),
        conversation=ConversationResponse.model_validate(conversation),
    )


@router.post("/{account_id}/conversations/{conv_id}/reply", response_model=ReplyResponse)
async def reply_to_conversation(
    account_id: int,
    conv_id: int,
    payload: ReplyRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Send a DM reply in a conversation."""
    account = await _get_account_or_404(account_id, current_user)

    conversation = await IGConversation.get_or_none(id=conv_id, account=account)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not conversation.participant_ig_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Participant ID not available for this conversation",
        )

    if not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message text cannot be empty")

    try:
        result = await send_dm(account.access_token, conversation.participant_ig_id, payload.text.strip())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    # Persist sent message locally
    await IGMessage.create(
        conversation=conversation,
        ig_message_id=result.get("message_id", f"local_{int(datetime.now(timezone.utc).timestamp())}"),
        sender_type=SenderType.USER,
        sender_ig_id=account.instagram_user_id,
        text=payload.text.strip(),
        timestamp=datetime.now(timezone.utc),
        is_read=True,
    )

    # Update conversation preview
    conversation.last_message_preview = payload.text.strip()[:255]
    conversation.last_message_at = datetime.now(timezone.utc)
    await conversation.save()

    return ReplyResponse(
        message_id=result.get("message_id", ""),
        recipient_id=conversation.participant_ig_id,
    )


@router.patch("/{account_id}/conversations/{conv_id}/read", response_model=ConversationResponse)
async def mark_conversation_read(
    account_id: int,
    conv_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Mark all messages in a conversation as read."""
    account = await _get_account_or_404(account_id, current_user)

    conversation = await IGConversation.get_or_none(id=conv_id, account=account)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    await IGMessage.filter(conversation=conversation, is_read=False).update(is_read=True)
    conversation.unread_count = 0
    await conversation.save()

    return ConversationResponse.model_validate(conversation)


@router.patch("/{account_id}/conversations/{conv_id}/archive", response_model=ConversationResponse)
async def archive_conversation(
    account_id: int,
    conv_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Toggle archive state of a conversation."""
    account = await _get_account_or_404(account_id, current_user)

    conversation = await IGConversation.get_or_none(id=conv_id, account=account)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    conversation.is_archived = not conversation.is_archived
    await conversation.save()

    return ConversationResponse.model_validate(conversation)
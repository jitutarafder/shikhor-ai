from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, List, Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.image_safety import sanitize_and_reencode_image
from app.core.errors import NotFoundException, ShikhorException
from app.db.mongo.schemas import (
    ConversationDocument,
    MessageDocument,
    ModerationReportDocument,
    UserBlockDocument,
)
from app.db.service_bridge import get_mongo_registry, is_mongodb_backend
from app.modules.messaging.models import (
    Conversation,
    Message,
    ModerationReport,
    UserBlock,
)
from app.modules.messaging.schemas import (
    ConversationResponse,
    MessageResponse,
    ModerationReportCreateRequest,
    ModerationReportResponse,
)
from app.modules.users.models import User

# Local storage for sanitized message image attachments (Rule 18)
MESSAGE_ATTACHMENTS_DIR = Path("storage/message_attachments")
MESSAGE_ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)


def _map_conversation(conv: Conversation) -> ConversationResponse:
    p1_name = conv.participant1.full_name if conv.participant1 else "ব্যবহারকারী ১"
    p2_name = conv.participant2.full_name if conv.participant2 else "ব্যবহারকারী ২"

    return ConversationResponse(
        id=conv.id,
        participant1Id=conv.participant1_id,
        participant1Name=p1_name,
        participant2Id=conv.participant2_id,
        participant2Name=p2_name,
        contextType=conv.context_type,
        contextId=conv.context_id,
        createdAt=conv.created_at,
        updatedAt=conv.updated_at,
    )


def _map_mongo_message(m: MessageDocument, sender_name: str) -> MessageResponse:
    target_att = m.attachment_url or m.attachment_filename
    if target_att:
        if target_att.startswith("http://") or target_att.startswith("https://"):
            attachment_url = target_att
        else:
            attachment_url = f"/api/v1/conversations/{m.conversation_id}/messages/{m.id}/attachment"
    else:
        attachment_url = None

    return MessageResponse(
        id=m.id,
        conversationId=m.conversation_id,
        senderId=m.sender_id,
        senderName=sender_name,
        content=m.content or "",
        attachmentFilename=m.attachment_filename or m.attachment_url,
        attachmentUrl=attachment_url,
        isRead=m.is_read,
        createdAt=m.created_at,
    )


def _map_message(msg: Message) -> MessageResponse:
    sender_name = msg.sender.full_name if msg.sender else "প্রেরক"
    if msg.attachment_filename:
        if msg.attachment_filename.startswith("http://") or msg.attachment_filename.startswith("https://"):
            attachment_url = msg.attachment_filename
        else:
            attachment_url = f"/api/v1/conversations/{msg.conversation_id}/messages/{msg.id}/attachment"
    else:
        attachment_url = None

    return MessageResponse(
        id=msg.id,
        conversationId=msg.conversation_id,
        senderId=msg.sender_id,
        senderName=sender_name,
        content=msg.content or "",
        attachmentFilename=msg.attachment_filename,
        attachmentUrl=attachment_url,
        isRead=msg.is_read,
        createdAt=msg.created_at,
    )


async def _is_blocked(db: AsyncSession, user_a_id: str, user_b_id: str) -> bool:
    """Checks if either user has blocked the other (Rule 27)."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        return reg.user_blocks.is_blocked(user_a_id, user_b_id)

    stmt = select(UserBlock).where(
        or_(
            (UserBlock.blocker_id == user_a_id) & (UserBlock.blocked_id == user_b_id),
            (UserBlock.blocker_id == user_b_id) & (UserBlock.blocked_id == user_a_id),
        )
    )
    result = await db.scalar(stmt)
    return result is not None


async def get_or_create_conversation(
    db: AsyncSession,
    user: Any,
    recipient_id: str,
    context_type: Optional[str] = None,
    context_id: Optional[str] = None,
    initial_message: Optional[str] = None,
) -> ConversationResponse:
    """Gets an existing conversation or creates a new one between two users."""
    if user.id == recipient_id:
        raise ShikhorException(
            code="INVALID_RECIPIENT",
            message="You cannot start a conversation with yourself.",
            status_code=400,
        )

    if is_mongodb_backend():
        reg = get_mongo_registry()
        recipient = reg.users.find_by_id(recipient_id)
        if not recipient:
            raise NotFoundException(code="USER_NOT_FOUND", message="Recipient user not found.")

        if reg.user_blocks.is_blocked(user.id, recipient_id):
            raise ShikhorException(
                code="USER_BLOCKED",
                message="Cannot initiate conversation because communication is blocked.",
                status_code=403,
            )

        conv_doc = reg.conversations.find_or_create(
            user.id, recipient_id, context_type=context_type, context_id=context_id
        )
        if initial_message:
            msg_doc = MessageDocument(
                conversation_id=conv_doc.id,
                sender_id=user.id,
                content=initial_message,
            )
            reg.messages.insert_one(msg_doc)

        p1 = reg.users.find_by_id(conv_doc.participant1_id)
        p2 = reg.users.find_by_id(conv_doc.participant2_id)
        return ConversationResponse(
            id=conv_doc.id,
            participant1Id=conv_doc.participant1_id,
            participant1Name=p1.full_name if p1 else "ব্যবহারকারী ১",
            participant2Id=conv_doc.participant2_id,
            participant2Name=p2.full_name if p2 else "ব্যবহারকারী ২",
            contextType=conv_doc.context_type,
            contextId=conv_doc.context_id,
            createdAt=conv_doc.created_at,
            updatedAt=conv_doc.updated_at,
        )

    recipient = await db.get(User, recipient_id)
    if not recipient:
        raise NotFoundException(code="USER_NOT_FOUND", message="Recipient user not found.")

    if await _is_blocked(db, user.id, recipient_id):
        raise ShikhorException(
            code="USER_BLOCKED",
            message="Cannot initiate conversation because communication is blocked.",
            status_code=403,
        )

    # Check for existing conversation
    stmt = select(Conversation).where(
        or_(
            (Conversation.participant1_id == user.id)
            & (Conversation.participant2_id == recipient_id),
            (Conversation.participant1_id == recipient_id)
            & (Conversation.participant2_id == user.id),
        )
    )
    conv = await db.scalar(stmt)

    if not conv:
        conv = Conversation(
            participant1_id=user.id,
            participant2_id=recipient_id,
            context_type=context_type,
            context_id=context_id,
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    if initial_message:
        msg = Message(
            conversation_id=conv.id,
            sender_id=user.id,
            content=initial_message,
        )
        db.add(msg)
        conv.updated_at = datetime.now(timezone.utc)
        await db.commit()

    # Re-fetch with relationships loaded
    conv_stmt = select(Conversation).where(Conversation.id == conv.id)
    loaded = await db.scalar(conv_stmt)
    return _map_conversation(loaded)


async def list_user_conversations(
    db: AsyncSession,
    user: Any,
) -> List[ConversationResponse]:
    """Lists conversations where user is an active participant."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        conv_docs = reg.conversations.get_user_conversations(user.id)
        responses = []
        for c in conv_docs:
            p1 = reg.users.find_by_id(c.participant1_id)
            p2 = reg.users.find_by_id(c.participant2_id)
            responses.append(
                ConversationResponse(
                    id=c.id,
                    participant1Id=c.participant1_id,
                    participant1Name=p1.full_name if p1 else "ব্যবহারকারী ১",
                    participant2Id=c.participant2_id,
                    participant2Name=p2.full_name if p2 else "ব্যবহারকারী ২",
                    contextType=c.context_type,
                    contextId=c.context_id,
                    createdAt=c.created_at,
                    updatedAt=c.updated_at,
                )
            )
        return responses

    stmt = (
        select(Conversation)
        .where(
            or_(
                Conversation.participant1_id == user.id,
                Conversation.participant2_id == user.id,
            )
        )
        .order_by(Conversation.updated_at.desc())
    )
    result = await db.execute(stmt)
    convs = result.scalars().all()

    return [_map_conversation(c) for c in convs]


async def get_conversation_messages(
    db: AsyncSession,
    user: Any,
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[MessageResponse]:
    """Retrieves messages for a conversation, strictly checking participant authorization (Rule 12)."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        conv = reg.conversations.find_by_id(conversation_id)
        if not conv:
            raise NotFoundException(
                code="CONVERSATION_NOT_FOUND", message="Conversation not found."
            )
        if user.id != conv.participant1_id and user.id != conv.participant2_id:
            raise ShikhorException(
                code="UNAUTHORIZED_CONVERSATION_ACCESS",
                message="You are not authorized to view messages in this conversation.",
                status_code=403,
            )
        msg_docs = reg.messages.get_by_conversation(conversation_id, skip=offset, limit=limit)
        reg.messages.mark_as_read(conversation_id, user.id)
        responses = []
        for m in msg_docs:
            sender = reg.users.find_by_id(m.sender_id)
            sender_name = sender.full_name if sender else "প্রেরক"
            responses.append(_map_mongo_message(m, sender_name))
        return responses

    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise NotFoundException(
            code="CONVERSATION_NOT_FOUND", message="Conversation not found."
        )

    # Rule 12: Object-level authorization policy
    if user.id != conv.participant1_id and user.id != conv.participant2_id:
        raise ShikhorException(
            code="UNAUTHORIZED_CONVERSATION_ACCESS",
            message="You are not authorized to view messages in this conversation.",
            status_code=403,
        )

    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    messages = list(result.scalars().all())

    # Mark unread messages sent by the other participant as read
    unreads = [m for m in messages if not m.is_read and m.sender_id != user.id]
    if unreads:
        for m in unreads:
            m.is_read = True
        await db.commit()

    return [_map_message(m) for m in messages]


async def send_message(
    db: AsyncSession,
    user: Any,
    conversation_id: str,
    content: str,
) -> MessageResponse:
    """Sends a message verifying participant authorization, block status, and spam limits."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        conv = reg.conversations.find_by_id(conversation_id)
        if not conv:
            raise NotFoundException(
                code="CONVERSATION_NOT_FOUND", message="Conversation not found."
            )
        if user.id != conv.participant1_id and user.id != conv.participant2_id:
            raise ShikhorException(
                code="UNAUTHORIZED_CONVERSATION_ACCESS",
                message="You cannot send messages to a conversation you are not part of.",
                status_code=403,
            )
        other_user_id = (
            conv.participant2_id if user.id == conv.participant1_id else conv.participant1_id
        )
        if reg.user_blocks.is_blocked(user.id, other_user_id):
            raise ShikhorException(
                code="USER_BLOCKED",
                message="Cannot send message because one of the participants has blocked communication.",
                status_code=403,
            )
        msg_doc = MessageDocument(
            conversation_id=conversation_id,
            sender_id=user.id,
            content=content,
        )
        saved = reg.messages.insert_one(msg_doc)
        sender_name = getattr(user, "full_name", "প্রেরক")
        return _map_mongo_message(saved, sender_name)
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise NotFoundException(
            code="CONVERSATION_NOT_FOUND", message="Conversation not found."
        )

    # 1. Authorization: participant check (Rule 12)
    if user.id != conv.participant1_id and user.id != conv.participant2_id:
        raise ShikhorException(
            code="UNAUTHORIZED_CONVERSATION_ACCESS",
            message="You cannot send messages to a conversation you are not part of.",
            status_code=403,
        )

    other_user_id = (
        conv.participant2_id if user.id == conv.participant1_id else conv.participant1_id
    )

    # 2. Block check (Rule 27)
    if await _is_blocked(db, user.id, other_user_id):
        raise ShikhorException(
            code="USER_BLOCKED",
            message="Cannot send message because one of the participants has blocked communication.",
            status_code=403,
        )

    # 3. Anti-Spam frequency control (Rule 27: New account / rate limit abuse control)
    one_minute_ago = datetime.now(timezone.utc) - timedelta(seconds=60)
    count_stmt = select(Message).where(
        Message.sender_id == user.id,
        Message.created_at >= one_minute_ago,
    )
    recent_msgs = await db.execute(count_stmt)
    if len(recent_msgs.scalars().all()) >= 10:
        raise ShikhorException(
            code="MESSAGE_RATE_LIMIT_EXCEEDED",
            message="You are sending messages too quickly. Please wait a moment before sending again.",
            status_code=429,
        )

    # 4. Insert message
    msg = Message(
        conversation_id=conversation_id,
        sender_id=user.id,
        content=content.strip(),
    )
    db.add(msg)
    conv.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(msg)

    # Re-fetch with sender relationship
    stmt = select(Message).where(Message.id == msg.id)
    loaded = await db.scalar(stmt)
    return _map_message(loaded)


async def send_message_with_attachment(
    db: AsyncSession,
    user: Any,
    conversation_id: str,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    content: Optional[str] = None,
) -> MessageResponse:
    """Sanitizes image, checks participant authorization, anti-spam, and stores message derivative."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        conv = reg.conversations.find_by_id(conversation_id)
        if not conv:
            raise NotFoundException(
                code="CONVERSATION_NOT_FOUND", message="Conversation not found."
            )

        # 1. Authorization: participant check (Rule 12)
        if user.id != conv.participant1_id and user.id != conv.participant2_id:
            raise ShikhorException(
                code="UNAUTHORIZED_CONVERSATION_ACCESS",
                message="You cannot send messages to a conversation you are not part of.",
                status_code=403,
            )

        other_user_id = (
            conv.participant2_id if user.id == conv.participant1_id else conv.participant1_id
        )

        # 2. Block check (Rule 27)
        if reg.user_blocks.is_blocked(user.id, other_user_id):
            raise ShikhorException(
                code="USER_BLOCKED",
                message="Cannot send message because one of the participants has blocked communication.",
                status_code=403,
            )

        # 3. Anti-Spam frequency control (Rule 27)
        one_minute_ago = datetime.now(timezone.utc) - timedelta(seconds=60)
        recent_count = reg.messages.collection.count_documents({
            "sender_id": user.id,
            "$or": [
                {"created_at": {"$gte": one_minute_ago}},
                {"created_at": {"$gte": one_minute_ago.isoformat()}},
            ],
        })
        if recent_count >= 10:
            raise ShikhorException(
                code="MESSAGE_RATE_LIMIT_EXCEEDED",
                message="You are sending messages too quickly. Please wait a moment before sending again.",
                status_code=429,
            )

        # 4. Enforce strict image safety and EXIF/metadata stripping (Rule 18)
        sanitized_bytes, safe_filename, _, _ = sanitize_and_reencode_image(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
        )

        # 5. Upload sanitized derivative to Cloudinary / storage
        from app.integrations.storage import upload_image_to_storage
        uploaded_url = await upload_image_to_storage(
            file_bytes=sanitized_bytes,
            filename=safe_filename,
            folder="messages",
        )
        is_cloud = bool(uploaded_url and uploaded_url.startswith("http"))
        attachment_url = uploaded_url if is_cloud else None
        attachment_filename = safe_filename

        # 6. Insert message with attachment filename/URL
        msg_doc = MessageDocument(
            conversation_id=conversation_id,
            sender_id=user.id,
            content=content.strip() if content else "",
            attachment_url=attachment_url,
            attachment_filename=attachment_filename,
        )
        saved = reg.messages.insert_one(msg_doc)

        reg.conversations.collection.update_one(
            {"id": conversation_id},
            {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
        )

        sender_name = getattr(user, "full_name", "প্রেরক")
        return _map_mongo_message(saved, sender_name)

    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise NotFoundException(
            code="CONVERSATION_NOT_FOUND", message="Conversation not found."
        )

    # 1. Authorization: participant check (Rule 12)
    if user.id != conv.participant1_id and user.id != conv.participant2_id:
        raise ShikhorException(
            code="UNAUTHORIZED_CONVERSATION_ACCESS",
            message="You cannot send messages to a conversation you are not part of.",
            status_code=403,
        )

    other_user_id = (
        conv.participant2_id if user.id == conv.participant1_id else conv.participant1_id
    )

    # 2. Block check (Rule 27)
    if await _is_blocked(db, user.id, other_user_id):
        raise ShikhorException(
            code="USER_BLOCKED",
            message="Cannot send message because one of the participants has blocked communication.",
            status_code=403,
        )

    # 3. Anti-Spam frequency control (Rule 27)
    one_minute_ago = datetime.now(timezone.utc) - timedelta(seconds=60)
    count_stmt = select(Message).where(
        Message.sender_id == user.id,
        Message.created_at >= one_minute_ago,
    )
    recent_msgs = await db.execute(count_stmt)
    if len(recent_msgs.scalars().all()) >= 10:
        raise ShikhorException(
            code="MESSAGE_RATE_LIMIT_EXCEEDED",
            message="You are sending messages too quickly. Please wait a moment before sending again.",
            status_code=429,
        )

    # 4. Enforce strict image safety and EXIF/metadata stripping (Rule 18)
    sanitized_bytes, safe_filename, _, _ = sanitize_and_reencode_image(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
    )

    # 5. Upload sanitized derivative to Cloudinary / storage
    from app.integrations.storage import upload_image_to_storage
    uploaded_url = await upload_image_to_storage(
        file_bytes=sanitized_bytes,
        filename=safe_filename,
        folder="messages",
    )
    attachment_ref = uploaded_url if uploaded_url.startswith("http") else safe_filename

    # 6. Insert message with attachment filename/URL
    msg = Message(
        conversation_id=conversation_id,
        sender_id=user.id,
        content=content.strip() if content else "",
        attachment_filename=attachment_ref,
    )
    db.add(msg)
    conv.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(msg)

    stmt = select(Message).where(Message.id == msg.id)
    loaded = await db.scalar(stmt)
    return _map_message(loaded)


async def get_message_attachment_path(
    db: AsyncSession,
    user: Any,
    conversation_id: str,
    message_id: str,
) -> Path:
    """Verifies participant authorization and returns the path to the message attachment (Rule 12)."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        conv = reg.conversations.find_by_id(conversation_id)
        if not conv:
            raise NotFoundException(
                code="CONVERSATION_NOT_FOUND", message="Conversation not found."
            )

        # Rule 12: Object-level authorization policy (participants or staff)
        is_participant = user.id in (conv.participant1_id, conv.participant2_id)
        user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        is_staff = user_role_str in ("admin", "moderator")
        if not (is_participant or is_staff):
            raise ShikhorException(
                code="UNAUTHORIZED_ATTACHMENT_ACCESS",
                message="You are not authorized to view attachments from this conversation.",
                status_code=403,
            )

        msg = reg.messages.find_by_id(message_id)
        if not msg or msg.conversation_id != conversation_id or not msg.attachment_filename:
            raise NotFoundException(
                code="ATTACHMENT_NOT_FOUND", message="Attachment not found."
            )

        file_path = MESSAGE_ATTACHMENTS_DIR / msg.attachment_filename
        if not file_path.exists() or not file_path.is_file():
            raise NotFoundException(
                code="ATTACHMENT_FILE_MISSING", message="Attachment file missing from storage."
            )

        return file_path

    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise NotFoundException(
            code="CONVERSATION_NOT_FOUND", message="Conversation not found."
        )

    # Rule 12: Object-level authorization policy (participants or staff)
    is_participant = user.id in (conv.participant1_id, conv.participant2_id)
    user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    is_staff = user_role_str in ("admin", "moderator")
    if not (is_participant or is_staff):
        raise ShikhorException(
            code="UNAUTHORIZED_ATTACHMENT_ACCESS",
            message="You are not authorized to view attachments from this conversation.",
            status_code=403,
        )

    msg = await db.get(Message, message_id)
    if not msg or msg.conversation_id != conversation_id or not msg.attachment_filename:
        raise NotFoundException(
            code="ATTACHMENT_NOT_FOUND", message="Attachment not found."
        )

    file_path = MESSAGE_ATTACHMENTS_DIR / msg.attachment_filename
    if not file_path.exists() or not file_path.is_file():
        raise NotFoundException(
            code="ATTACHMENT_FILE_MISSING", message="Attachment file missing from storage."
        )

    return file_path


async def block_user(
    db: AsyncSession,
    blocker: Any,
    target_user_id: str,
) -> None:
    """Blocks a user from messaging the blocker (Rule 27)."""
    if blocker.id == target_user_id:
        raise ShikhorException(
            code="INVALID_BLOCK_TARGET",
            message="You cannot block yourself.",
            status_code=400,
        )

    if is_mongodb_backend():
        reg = get_mongo_registry()
        target_user = reg.users.find_by_id(target_user_id)
        if not target_user:
            raise NotFoundException(code="USER_NOT_FOUND", message="Target user not found.")
        existing = reg.user_blocks.collection.find_one(
            {"blocker_id": blocker.id, "blocked_id": target_user_id}
        )
        if not existing:
            reg.user_blocks.insert_one(
                UserBlockDocument(blocker_id=blocker.id, blocked_id=target_user_id)
            )
        return

    target_user = await db.get(User, target_user_id)
    if not target_user:
        raise NotFoundException(code="USER_NOT_FOUND", message="Target user not found.")

    existing = await db.scalar(
        select(UserBlock).where(
            UserBlock.blocker_id == blocker.id, UserBlock.blocked_id == target_user_id
        )
    )
    if not existing:
        block = UserBlock(blocker_id=blocker.id, blocked_id=target_user_id)
        db.add(block)
        await db.commit()


async def create_moderation_report(
    db: AsyncSession,
    reporter: Any,
    req: ModerationReportCreateRequest,
) -> ModerationReportResponse:
    """Submits a moderation report for abusive conduct or fraudulent listings."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        report_doc = ModerationReportDocument(
            reporter_id=reporter.id,
            reported_user_id=req.reportedUserId,
            content_type=req.contentType,
            content_id=req.contentId,
            reason=req.reason,
            details=req.details,
            status="pending",
        )
        saved = reg.moderation_reports.insert_one(report_doc)
        return ModerationReportResponse(
            id=saved.id,
            reporterId=saved.reporter_id,
            reportedUserId=saved.reported_user_id,
            contentType=saved.content_type,
            contentId=saved.content_id,
            reason=saved.reason,
            details=saved.details,
            status=saved.status,
            createdAt=saved.created_at,
        )

    report = ModerationReport(
        reporter_id=reporter.id,
        reported_user_id=req.reportedUserId,
        content_type=req.contentType,
        content_id=req.contentId,
        reason=req.reason,
        details=req.details,
        status="pending",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ModerationReportResponse(
        id=report.id,
        reporterId=report.reporter_id,
        reportedUserId=report.reported_user_id,
        contentType=report.content_type,
        contentId=report.content_id,
        reason=report.reason,
        details=report.details,
        status=report.status,
        createdAt=report.created_at,
    )

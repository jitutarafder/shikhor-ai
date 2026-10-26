"""API endpoints for Conversations, Messaging, User Blocks, and Moderation Reports."""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.errors import ForbiddenException, NotFoundException, ShikhorException, UnauthorizedException
from app.core.security import decode_token
from app.db.service_bridge import get_mongo_registry, is_mongodb_backend
from app.db.session import get_db_session
from app.modules.messaging.schemas import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageCreateRequest,
    MessageResponse,
    ModerationReportCreateRequest,
    ModerationReportResponse,
    UserBlockRequest,
)
from app.modules.messaging.service import (
    block_user,
    create_moderation_report,
    get_conversation_messages,
    get_message_attachment_path,
    get_or_create_conversation,
    list_user_conversations,
    send_message,
    send_message_with_attachment,
)
from app.modules.messaging.models import Conversation, Message
from app.modules.users.models import User

router = APIRouter(tags=["messaging"])


async def _resolve_user_for_attachment(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """Authenticates user either from Authorization Header or from query param token."""
    raw_token = None
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]
    elif token:
        raw_token = token

    if not raw_token:
        raise UnauthorizedException(
            code="UNAUTHENTICATED",
            message="Valid access token is required to view attachments.",
        )

    payload = decode_token(raw_token, expected_type="access")
    user_id = payload.get("sub")

    if is_mongodb_backend():
        reg = get_mongo_registry()
        user = reg.users.find_by_id(user_id)
        if not user:
            raise UnauthorizedException(code="USER_NOT_FOUND", message="User account no longer exists.")
        if not user.is_active:
            raise ForbiddenException(code="ACCOUNT_INACTIVE", message="Account is deactivated.")
        return user

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException(code="USER_NOT_FOUND", message="User account no longer exists.")
    if not user.is_active:
        raise ForbiddenException(code="ACCOUNT_INACTIVE", message="Account is deactivated.")

    return user


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_or_get_conversation(
    req: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ConversationResponse:
    """Initiates a conversation or retrieves an existing one with another user."""
    return await get_or_create_conversation(
        db=db,
        user=current_user,
        recipient_id=req.recipientId,
        context_type=req.contextType,
        context_id=req.contextId,
        initial_message=req.initialMessage,
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_my_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[ConversationResponse]:
    """Lists conversations where current user is an active participant."""
    return await list_user_conversations(db=db, user=current_user)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageResponse],
)
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[MessageResponse]:
    """Retrieves conversation messages with object-level participant authorization (Rule 12)."""
    return await get_conversation_messages(
        db=db,
        user=current_user,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_message(
    conversation_id: str,
    req: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    """Sends a text message with authorization, block check, and spam frequency guard (Rule 27)."""
    return await send_message(
        db=db,
        user=current_user,
        conversation_id=conversation_id,
        content=req.content,
    )


@router.post(
    "/conversations/{conversation_id}/messages/attachment",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message with image attachment",
)
async def post_message_attachment(
    conversation_id: str,
    image: UploadFile = File(..., description="Crop, equipment, or produce photo (JPEG, PNG, WebP)"),
    content: Optional[str] = Form(None, description="Optional caption or message text"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    """Uploads, sanitizes, and attaches an image to a conversation with strict participant check."""
    file_bytes = await image.read()
    return await send_message_with_attachment(
        db=db,
        user=current_user,
        conversation_id=conversation_id,
        file_bytes=file_bytes,
        filename=image.filename or "attachment.jpg",
        content_type=image.content_type or "image/jpeg",
        content=content,
    )


@router.get(
    "/conversations/{conversation_id}/messages/{message_id}/attachment",
    summary="Securely view sanitized message attachment",
)
async def get_message_attachment(
    conversation_id: str,
    message_id: str,
    user: Any = Depends(_resolve_user_for_attachment),
    db: AsyncSession = Depends(get_db_session),
):
    """Streams sanitized message attachment derivative with object-level participant authorization (Rule 12)."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        conv = reg.conversations.find_by_id(conversation_id)
        if not conv:
            raise NotFoundException(code="CONVERSATION_NOT_FOUND", message="Conversation not found.")

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
        if not msg or msg.conversation_id != conversation_id or not (msg.attachment_filename or msg.attachment_url):
            raise NotFoundException(code="ATTACHMENT_NOT_FOUND", message="Attachment not found.")

        target_att = msg.attachment_url or msg.attachment_filename
        if target_att.startswith("http://") or target_att.startswith("https://"):
            from fastapi.responses import RedirectResponse
            from app.integrations.storage import get_optimized_image_url
            return RedirectResponse(url=get_optimized_image_url(target_att, width=1200), status_code=307)

        file_path = await get_message_attachment_path(
            db=db,
            user=user,
            conversation_id=conversation_id,
            message_id=message_id,
        )
        media_type = "image/webp" if file_path.suffix.lower() == ".webp" else "image/jpeg"
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            headers={
                "Content-Disposition": "inline",
                "X-Content-Type-Options": "nosniff",
            },
        )

    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise NotFoundException(code="CONVERSATION_NOT_FOUND", message="Conversation not found.")

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
        raise NotFoundException(code="ATTACHMENT_NOT_FOUND", message="Attachment not found.")

    if msg.attachment_filename.startswith("http://") or msg.attachment_filename.startswith("https://"):
        from fastapi.responses import RedirectResponse
        from app.integrations.storage import get_optimized_image_url
        return RedirectResponse(url=get_optimized_image_url(msg.attachment_filename, width=1200), status_code=307)

    file_path = await get_message_attachment_path(
        db=db,
        user=user,
        conversation_id=conversation_id,
        message_id=message_id,
    )
    media_type = "image/webp" if file_path.suffix.lower() == ".webp" else "image/jpeg"
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/users/block", status_code=status.HTTP_200_OK)
async def block_target_user(
    req: UserBlockRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Blocks a user from communicating with the current user."""
    await block_user(db=db, blocker=current_user, target_user_id=req.targetUserId)
    return {"status": "ok", "message": "User blocked successfully."}


@router.post(
    "/reports",
    response_model=ModerationReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_moderation_report(
    req: ModerationReportCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ModerationReportResponse:
    """Submits a report for abusive conduct, fraud, or inappropriate content."""
    return await create_moderation_report(db=db, reporter=current_user, req=req)

"""Notification service for dispatching, listing, and updating user alerts."""

from typing import List, Optional
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenException, NotFoundException
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationResponse, UnreadCountResponse
from app.modules.users.models import User


def _map_to_response(n: Notification) -> NotificationResponse:
    return NotificationResponse.model_validate(n)


async def create_notification(
    db: AsyncSession,
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "general",
    link: Optional[str] = None,
) -> NotificationResponse:
    """Dispatches a notification to a specific user."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        is_read=False,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return _map_to_response(notif)


async def list_user_notifications(
    db: AsyncSession,
    user: User,
    unread_only: bool = False,
    limit: int = 50,
) -> List[NotificationResponse]:
    """Retrieves notifications belonging strictly to the current user (Rule 12)."""
    stmt = (
        select(Notification)
        .where(Notification.user_id == user.id)
    )
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712

    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [_map_to_response(n) for n in records]


async def get_unread_notification_count(
    db: AsyncSession,
    user: User,
) -> UnreadCountResponse:
    """Returns total unread alerts for notification badge."""
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user.id,
        Notification.is_read == False,  # noqa: E712
    )
    count = await db.scalar(stmt) or 0
    return UnreadCountResponse(unreadCount=count)


async def mark_notification_as_read(
    db: AsyncSession,
    user: User,
    notification_id: str,
) -> NotificationResponse:
    """Marks single notification as read, enforcing object ownership (Rule 12)."""
    notif = await db.get(Notification, notification_id)
    if not notif:
        raise NotFoundException(code="NOTIFICATION_NOT_FOUND", message="Notification not found.")

    if notif.user_id != user.id:
        raise ForbiddenException(code="FORBIDDEN_NOTIFICATION", message="Cannot access another user's notifications.")

    notif.is_read = True
    await db.commit()
    await db.refresh(notif)
    return _map_to_response(notif)


async def mark_all_notifications_as_read(
    db: AsyncSession,
    user: User,
) -> int:
    """Marks all unread notifications of the user as read."""
    stmt = (
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount

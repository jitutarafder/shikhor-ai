"""Notification endpoints for in-app alert delivery and read tracking."""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.modules.notifications.schemas import NotificationResponse, UnreadCountResponse
from app.modules.notifications.service import (
    get_unread_notification_count,
    list_user_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationResponse])
async def get_my_notifications(
    unread_only: bool = Query(False, alias="unreadOnly"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[NotificationResponse]:
    """Lists current user's notifications."""
    return await list_user_notifications(db=db, user=current_user, unread_only=unread_only, limit=limit)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_my_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UnreadCountResponse:
    """Returns number of unread notifications for badge display."""
    return await get_unread_notification_count(db=db, user=current_user)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_single_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> NotificationResponse:
    """Marks a single notification as read."""
    return await mark_notification_as_read(db=db, user=current_user, notification_id=notification_id)


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Marks all notifications of the user as read."""
    count = await mark_all_notifications_as_read(db=db, user=current_user)
    return {"markedCount": count}

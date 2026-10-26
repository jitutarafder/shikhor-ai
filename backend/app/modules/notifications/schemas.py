"""Pydantic schemas for User Notifications."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, protected_namespaces=())

    id: str
    user_id: str = Field(serialization_alias="userId", alias="userId")
    title: str
    message: str
    notification_type: str = Field(serialization_alias="notificationType", alias="notificationType")
    link: Optional[str] = None
    is_read: bool = Field(serialization_alias="isRead", alias="isRead")
    created_at: datetime = Field(serialization_alias="createdAt", alias="createdAt")


class UnreadCountResponse(BaseModel):
    unreadCount: int = Field(serialization_alias="unreadCount")

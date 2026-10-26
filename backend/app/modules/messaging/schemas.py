"""Pydantic v2 schemas for Conversations, Messages, and Moderation Reports."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ConversationCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    recipientId: str = Field(alias="recipient_id")
    contextType: Optional[str] = Field(None, alias="context_type", max_length=50)
    contextId: Optional[str] = Field(None, alias="context_id", max_length=36)
    initialMessage: Optional[str] = Field(None, alias="initial_message", max_length=1000)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    participant1Id: str = Field(serialization_alias="participant1Id")
    participant1Name: str = Field(serialization_alias="participant1Name")
    participant2Id: str = Field(serialization_alias="participant2Id")
    participant2Name: str = Field(serialization_alias="participant2Name")
    contextType: Optional[str] = Field(None, serialization_alias="contextType")
    contextId: Optional[str] = Field(None, serialization_alias="contextId")
    createdAt: datetime = Field(serialization_alias="createdAt")
    updatedAt: datetime = Field(serialization_alias="updatedAt")


class MessageCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    content: str = Field(..., min_length=1, max_length=1000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=(), populate_by_name=True)

    id: str
    conversationId: str = Field(serialization_alias="conversationId")
    senderId: str = Field(serialization_alias="senderId")
    senderName: str = Field(serialization_alias="senderName")
    content: Optional[str] = Field("", serialization_alias="content")
    attachmentFilename: Optional[str] = Field(None, serialization_alias="attachmentFilename")
    attachmentUrl: Optional[str] = Field(None, serialization_alias="attachmentUrl")
    isRead: bool = Field(serialization_alias="isRead")
    createdAt: datetime = Field(serialization_alias="createdAt")


class UserBlockRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    targetUserId: str = Field(alias="target_user_id")


class ModerationReportCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    reportedUserId: Optional[str] = Field(None, alias="reported_user_id")
    contentType: str = Field(alias="content_type", max_length=50)
    contentId: str = Field(alias="content_id", max_length=36)
    reason: str = Field(..., min_length=2, max_length=100)
    details: Optional[str] = Field(None, max_length=1000)


class ModerationReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    reporterId: str = Field(serialization_alias="reporterId")
    reportedUserId: Optional[str] = Field(None, serialization_alias="reportedUserId")
    contentType: str = Field(serialization_alias="contentType")
    contentId: str = Field(serialization_alias="contentId")
    reason: str
    details: Optional[str] = None
    status: str
    createdAt: datetime = Field(serialization_alias="createdAt")

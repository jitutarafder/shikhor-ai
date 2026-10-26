"""Admin and Moderation Pydantic v2 schemas.

Strictly complies with:
- AGENTS.md Rule 11: Authoritative backend validation.
- AGENTS.md Rule 26: Redact PII in audit records.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.modules.knowledge.schemas import KnowledgeArticleResponse
from app.modules.users.models import UserRole


class ReportResolveRequest(BaseModel):
    action: str = Field(
        ...,
        pattern="^(dismiss|warn|hide_content|suspend_user)$",
        description="Action taken on the report",
    )
    resolutionNotes: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Justification and notes recorded in audit log",
    )


class UserStatusToggleRequest(BaseModel):
    isActive: bool
    reason: str = Field(..., min_length=5, max_length=500)


class UserVerificationToggleRequest(BaseModel):
    isVerified: bool = Field(alias="is_verified")
    notes: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(populate_by_name=True)


class ModerationReportDetailResponse(BaseModel):
    id: str
    reporterId: str
    reporterName: str
    reportedUserId: str
    reportedUserName: str
    contentType: str
    contentId: str
    reason: str
    details: Optional[str] = None
    status: str
    createdAt: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: str
    actorId: Optional[str] = None
    actorPhone: str
    actorRole: str
    action: str
    resourceType: str
    resourceId: str
    details: str
    requestId: Optional[str] = None
    createdAt: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserItem(BaseModel):
    id: str
    phone: str
    email: Optional[str] = None
    fullName: str
    role: UserRole
    isActive: bool = Field(alias="isActive")
    isVerified: bool = Field(alias="isVerified")
    district: Optional[str] = None
    upazila: Optional[str] = None
    nid: Optional[str] = None
    dob: Optional[str] = None
    nidFrontImage: Optional[str] = Field(None, alias="nidFrontImage")
    nidBackImage: Optional[str] = Field(None, alias="nidBackImage")
    isNidVerified: bool = Field(False, alias="isNidVerified")
    nidVerificationStatus: str = Field("pending", alias="nidVerificationStatus")
    nidRejectionReason: Optional[str] = Field(None, alias="nidRejectionReason")
    createdAt: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NidReviewRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$", description="approve or reject NID verification")
    reason: Optional[str] = Field(None, max_length=500, description="Optional rejection reason")


class AdminMetricsResponse(BaseModel):
    totalUsers: int
    farmersCount: int
    buyersCount: int
    ownersCount: int
    expertsCount: int
    activeCropListings: int
    totalRentalRequests: int
    pendingModerationReports: int
    totalAuditEvents: int
    systemStatus: str
    timestamp: datetime


class KnowledgeArticleCreateRequest(BaseModel):
    cropType: str = Field(..., min_length=2, max_length=50)
    category: str = Field(..., min_length=2, max_length=50)
    titleBn: str = Field(..., min_length=3, max_length=200)
    titleEn: Optional[str] = Field(None, max_length=200)
    summaryBn: str = Field(..., min_length=10)
    contentBn: str = Field(..., min_length=20)
    recommendedPracticesBn: Optional[str] = None

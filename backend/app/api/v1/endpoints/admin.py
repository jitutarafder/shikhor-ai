"""Admin and Moderation API endpoints.

Strictly complies with:
- AGENTS.md Rule 12: Object-level authorization policy (Role guards deny-by-default).
- AGENTS.md Rule 26: Audit history and logging.
- AGENTS.md Rule 31: Definition of done (authoritative real data only).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_role
from app.db.session import get_db_session
from app.modules.admin.schemas import (
    AdminMetricsResponse,
    AdminUserItem,
    AuditLogResponse,
    KnowledgeArticleCreateRequest,
    ModerationReportDetailResponse,
    NidReviewRequest,
    ReportResolveRequest,
    UserStatusToggleRequest,
    UserVerificationToggleRequest,
)
from app.modules.admin.service import (
    get_platform_metrics,
    list_admin_users,
    list_audit_logs,
    list_moderation_reports,
    list_nid_verifications,
    publish_admin_knowledge_article,
    resolve_moderation_report,
    review_user_nid,
    toggle_user_status,
    toggle_user_verification,
)
from app.modules.knowledge.schemas import KnowledgeArticleResponse
from app.modules.users.models import User, UserRole

router = APIRouter(prefix="/admin", tags=["Admin & Moderation"])


@router.get(
    "/metrics",
    response_model=AdminMetricsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_metrics(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> AdminMetricsResponse:
    """Returns authoritative system-wide health and usage metrics."""
    return await get_platform_metrics(db=db)


@router.get(
    "/reports",
    response_model=List[ModerationReportDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_reports(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> List[ModerationReportDetailResponse]:
    """Lists moderation reports with reporter and target user info."""
    return await list_moderation_reports(
        db=db, status_filter=status_filter, limit=limit, offset=offset
    )


@router.post(
    "/reports/{report_id}/resolve",
    response_model=ModerationReportDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def resolve_report(
    report_id: str,
    req: ReportResolveRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> ModerationReportDetailResponse:
    """Resolves or dismisses a report and audits the administrative action."""
    request_id = request.headers.get("X-Correlation-ID")
    return await resolve_moderation_report(
        db=db,
        actor=current_user,
        report_id=report_id,
        action=req.action,
        resolution_notes=req.resolutionNotes,
        request_id=request_id,
    )


@router.get(
    "/users",
    response_model=List[AdminUserItem],
    status_code=status.HTTP_200_OK,
)
async def get_users(
    role: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> List[AdminUserItem]:
    """Lists registered accounts for review."""
    return await list_admin_users(db=db, role_filter=role, limit=limit, offset=offset)


@router.post(
    "/users/{user_id}/status",
    response_model=AdminUserItem,
    status_code=status.HTTP_200_OK,
)
async def set_user_status(
    user_id: str,
    req: UserStatusToggleRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> AdminUserItem:
    """Toggles user account status (active/suspended) with audit trail."""
    request_id = request.headers.get("X-Correlation-ID")
    return await toggle_user_status(
        db=db,
        actor=current_user,
        user_id=user_id,
        is_active=req.isActive,
        reason=req.reason,
        request_id=request_id,
    )


@router.post(
    "/users/{user_id}/verify",
    response_model=AdminUserItem,
    status_code=status.HTTP_200_OK,
)
async def set_user_verification(
    user_id: str,
    req: UserVerificationToggleRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> AdminUserItem:
    """Awards or revokes verified badge for owner/buyer/farmer with audit trail."""
    request_id = request.headers.get("X-Correlation-ID")
    return await toggle_user_verification(
        db=db,
        actor=current_user,
        user_id=user_id,
        is_verified=req.isVerified,
        notes=req.notes,
        request_id=request_id,
    )


@router.get(
    "/nid-verifications",
    response_model=List[AdminUserItem],
    status_code=status.HTTP_200_OK,
)
async def get_nid_verifications(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> List[AdminUserItem]:
    """Lists users with NID submissions for verification."""
    return await list_nid_verifications(db=db, status_filter=status, limit=limit, offset=offset)


@router.post(
    "/nid-verifications/{user_id}/review",
    response_model=AdminUserItem,
    status_code=status.HTTP_200_OK,
)
async def review_nid_submission(
    user_id: str,
    req: NidReviewRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> AdminUserItem:
    """Manually approves or rejects NID verification with audit logging."""
    request_id = request.headers.get("X-Correlation-ID")
    return await review_user_nid(
        db=db,
        actor=current_user,
        user_id=user_id,
        action=req.action,
        reason=req.reason,
        request_id=request_id,
    )


@router.get(
    "/audit-logs",
    response_model=List[AuditLogResponse],
    status_code=status.HTTP_200_OK,
)
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> List[AuditLogResponse]:
    """Retrieves immutable audit trail of privileged administrative operations."""
    return await list_audit_logs(db=db, limit=limit, offset=offset)


@router.post(
    "/knowledge",
    response_model=KnowledgeArticleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def publish_knowledge(
    req: KnowledgeArticleCreateRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> KnowledgeArticleResponse:
    """Publishes a new verified agricultural advisory article with version tracking."""
    request_id = request.headers.get("X-Correlation-ID")
    return await publish_admin_knowledge_article(
        db=db,
        actor=current_user,
        req=req,
        request_id=request_id,
    )

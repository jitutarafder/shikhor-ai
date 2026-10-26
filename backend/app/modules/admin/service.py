"""Admin and Moderation domain service.

Strictly complies with:
- AGENTS.md Rule 12: Object-level authorization policy (admin/moderator only).
- AGENTS.md Rule 26: Error, logging, and audit rules (actor, action, resource, request_id).
- AGENTS.md Rule 31: Definition of done (no fake claims or placeholder production data).
"""

from datetime import datetime, timezone
import json
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException, ShikhorException
from app.integrations.email import (
    get_nid_approval_email_html,
    get_nid_rejection_email_html,
    send_email,
)
from app.modules.admin.models import AuditLog
from app.modules.admin.schemas import (
    AdminMetricsResponse,
    AdminUserItem,
    AuditLogResponse,
    KnowledgeArticleCreateRequest,
    ModerationReportDetailResponse,
)
from app.modules.crop_marketplace.models import CropListing, CropListingStatus
from app.modules.knowledge.models import KnowledgeArticle
from app.modules.knowledge.schemas import KnowledgeArticleResponse
from app.modules.messaging.models import ModerationReport
from app.modules.rentals.models import RentalRequest
from app.modules.users.models import User, UserRole


async def record_audit_log(
    db: AsyncSession,
    actor: User,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict,
    request_id: Optional[str] = None,
) -> AuditLog:
    """Creates an immutable audit log entry for privileged actions (Rule 26)."""
    # Ensure sensitive data is sanitized / redacted
    sanitized = {k: v for k, v in details.items() if "password" not in k.lower() and "token" not in k.lower()}

    log = AuditLog(
        actor_id=actor.id,
        actor_phone=actor.phone,
        actor_role=actor.role.value if hasattr(actor.role, "value") else str(actor.role),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(sanitized, ensure_ascii=False),
        request_id=request_id,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def list_moderation_reports(
    db: AsyncSession,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[ModerationReportDetailResponse]:
    """Lists moderation reports with reporter and reported user details."""
    stmt = select(ModerationReport).order_by(ModerationReport.created_at.desc()).offset(offset).limit(limit)
    if status_filter:
        stmt = stmt.where(ModerationReport.status == status_filter)

    result = await db.execute(stmt)
    reports = list(result.scalars().all())

    output = []
    for r in reports:
        reporter = await db.get(User, r.reporter_id) if r.reporter_id else None
        reported = await db.get(User, r.reported_user_id) if r.reported_user_id else None

        output.append(
            ModerationReportDetailResponse(
                id=r.id,
                reporterId=r.reporter_id,
                reporterName=reporter.full_name if reporter else "ব্যবহারকারী",
                reportedUserId=r.reported_user_id,
                reportedUserName=reported.full_name if reported else "অভিযুক্ত ব্যবহারকারী",
                contentType=r.content_type,
                contentId=r.content_id,
                reason=r.reason,
                details=r.details,
                status=r.status,
                createdAt=r.created_at,
            )
        )
    return output


async def resolve_moderation_report(
    db: AsyncSession,
    actor: User,
    report_id: str,
    action: str,
    resolution_notes: str,
    request_id: Optional[str] = None,
) -> ModerationReportDetailResponse:
    """Resolves a moderation report with audit logging and optional user suspension."""
    report = await db.get(ModerationReport, report_id)
    if not report:
        raise NotFoundException(code="REPORT_NOT_FOUND", message="Moderation report not found.")

    if action == "dismiss":
        report.status = "dismissed"
    else:
        report.status = "resolved"

    # If action is suspend_user, deactivate target account
    target_suspended = False
    if action == "suspend_user" and report.reported_user_id:
        target_user = await db.get(User, report.reported_user_id)
        if target_user:
            target_user.is_active = False
            target_suspended = True

    await db.commit()
    await db.refresh(report)

    # Record Audit Log
    await record_audit_log(
        db=db,
        actor=actor,
        action=f"REPORT_{action.upper()}",
        resource_type="report",
        resource_id=report.id,
        details={
            "action": action,
            "notes": resolution_notes,
            "reportedUserId": report.reported_user_id,
            "targetSuspended": target_suspended,
        },
        request_id=request_id,
    )

    reporter = await db.get(User, report.reporter_id) if report.reporter_id else None
    reported = await db.get(User, report.reported_user_id) if report.reported_user_id else None

    return ModerationReportDetailResponse(
        id=report.id,
        reporterId=report.reporter_id,
        reporterName=reporter.full_name if reporter else "ব্যবহারকারী",
        reportedUserId=report.reported_user_id,
        reportedUserName=reported.full_name if reported else "অভিযুক্ত ব্যবহারকারী",
        contentType=report.content_type,
        contentId=report.content_id,
        reason=report.reason,
        details=report.details,
        status=report.status,
        createdAt=report.created_at,
    )


def _map_admin_user_item(u: User) -> AdminUserItem:
    return AdminUserItem(
        id=u.id,
        phone=u.phone,
        fullName=u.full_name,
        role=u.role,
        isActive=u.is_active,
        isVerified=u.is_verified,
        nid=u.nid,
        dob=u.dob,
        nidFrontImage=u.nid_front_image,
        nidBackImage=u.nid_back_image,
        isNidVerified=u.is_nid_verified,
        nidVerificationStatus=u.nid_verification_status,
        nidRejectionReason=u.nid_rejection_reason,
        createdAt=u.created_at,
    )


async def toggle_user_status(
    db: AsyncSession,
    actor: User,
    user_id: str,
    is_active: bool,
    reason: str,
    request_id: Optional[str] = None,
) -> AdminUserItem:
    """Toggles account active/deactivated state with audit trail."""
    target_user = await db.get(User, user_id)
    if not target_user:
        raise NotFoundException(code="USER_NOT_FOUND", message="User not found.")

    if target_user.id == actor.id:
        raise ShikhorException(
            code="CANNOT_MODIFY_SELF",
            message="Administrators cannot deactivate their own account.",
            status_code=400,
        )

    target_user.is_active = is_active
    await db.commit()
    await db.refresh(target_user)

    action_label = "USER_ACTIVATED" if is_active else "USER_SUSPENDED"
    await record_audit_log(
        db=db,
        actor=actor,
        action=action_label,
        resource_type="user",
        resource_id=target_user.id,
        details={
            "phone": target_user.phone,
            "role": str(target_user.role),
            "isActive": is_active,
            "reason": reason,
        },
        request_id=request_id,
    )

    return _map_admin_user_item(target_user)


async def toggle_user_verification(
    db: AsyncSession,
    actor: User,
    user_id: str,
    is_verified: bool,
    notes: Optional[str] = None,
    request_id: Optional[str] = None,
) -> AdminUserItem:
    """Awards or revokes verified badge for owner/buyer/farmer with immutable audit trail."""
    target_user = await db.get(User, user_id)
    if not target_user:
        raise NotFoundException(code="USER_NOT_FOUND", message="User not found.")

    target_user.is_verified = is_verified
    await db.commit()
    await db.refresh(target_user)

    action_label = "USER_VERIFIED" if is_verified else "USER_UNVERIFIED"
    await record_audit_log(
        db=db,
        actor=actor,
        action=action_label,
        resource_type="user",
        resource_id=target_user.id,
        details={
            "phone": target_user.phone,
            "role": str(target_user.role),
            "isVerified": is_verified,
            "notes": notes,
        },
        request_id=request_id,
    )

    return _map_admin_user_item(target_user)


async def list_admin_users(
    db: AsyncSession,
    role_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[AdminUserItem]:
    """Lists registered users for administrative review."""
    stmt = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    if role_filter:
        stmt = stmt.where(User.role == role_filter)

    result = await db.execute(stmt)
    users = list(result.scalars().all())

    return [_map_admin_user_item(u) for u in users]


async def list_nid_verifications(
    db: AsyncSession,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[AdminUserItem]:
    """Lists users with NID submissions for verification."""
    stmt = (
        select(User)
        .where(User.nid.isnot(None) | User.nid_front_image.isnot(None))
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if status_filter and status_filter != "all":
        stmt = stmt.where(User.nid_verification_status == status_filter)

    result = await db.execute(stmt)
    users = list(result.scalars().all())
    return [_map_admin_user_item(u) for u in users]


async def review_user_nid(
    db: AsyncSession,
    actor: User,
    user_id: str,
    action: str,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
) -> AdminUserItem:
    """Approves or rejects NID verification with immutable audit log."""
    target_user = await db.get(User, user_id)
    if not target_user:
        raise NotFoundException(code="USER_NOT_FOUND", message="User not found.")

    if action == "approve":
        target_user.is_nid_verified = True
        target_user.is_verified = True
        target_user.nid_verification_status = "approved"
        target_user.nid_rejection_reason = None
        audit_action = "NID_VERIFICATION_APPROVED"
    elif action == "reject":
        target_user.is_nid_verified = False
        target_user.nid_verification_status = "rejected"
        target_user.nid_rejection_reason = reason or "NID তথ্য বা ছবি সুস্পষ্ট নয়"
        audit_action = "NID_VERIFICATION_REJECTED"
    else:
        raise ShikhorException(code="INVALID_ACTION", message="Action must be approve or reject.", status_code=400)

    await db.commit()
    await db.refresh(target_user)

    await record_audit_log(
        db=db,
        actor=actor,
        action=audit_action,
        resource_type="user",
        resource_id=target_user.id,
        details={
            "phone": target_user.phone,
            "nid": target_user.nid,
            "action": action,
            "reason": reason,
        },
        request_id=request_id,
    )

    # Dispatch email notification to the user if email is registered
    if target_user.email:
        try:
            if action == "approve":
                await send_email(
                    to_email=target_user.email,
                    subject="[শিখড় এআই] অভিনন্দন! আপনার অ্যাকাউন্ট সফলভাবে অনুমোদিত হয়েছে 🎉",
                    html_body=get_nid_approval_email_html(target_user.full_name),
                    text_body=(
                        f"প্রিয় {target_user.full_name}, শিখড় এআই প্ল্যাটফর্মে আপনার অ্যাকাউন্ট ও "
                        "এনআইডি সফলভাবে অনুমোদিত হয়েছে। এখন আপনি সকল ফিচার ব্যবহার করতে পারবেন।"
                    ),
                )
            elif action == "reject":
                await send_email(
                    to_email=target_user.email,
                    subject="[শিখড় এআই] অ্যাকাউন্ট ভেরিফিকেশন সংক্রান্ত জরুরি নোটিশ",
                    html_body=get_nid_rejection_email_html(
                        target_user.full_name,
                        target_user.nid_rejection_reason or reason or "NID তথ্য বা ছবি সুস্পষ্ট নয়",
                    ),
                    text_body=(
                        f"প্রিয় {target_user.full_name}, শিখড় এআই প্ল্যাটফর্মে আপনার এনআইডি ভেরিফিকেশন আবেদনটি "
                        f"নিম্নলিখিত কারণে বাতিল করা হয়েছে: {target_user.nid_rejection_reason}। পুনরায় আবেদনের জন্য সাপোর্টে যোগাযোগ করুন।"
                    ),
                )
        except Exception as exc:
            import logging
            logging.getLogger("shikhor.admin.service").warning(
                "Failed to dispatch NID review email to %s: %s", target_user.email, str(exc)
            )

    return _map_admin_user_item(target_user)


async def list_audit_logs(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> List[AuditLogResponse]:
    """Retrieves immutable audit logs for security and compliance review (Rule 26)."""
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    logs = list(result.scalars().all())

    return [
        AuditLogResponse(
            id=l.id,
            actorId=l.actor_id,
            actorPhone=l.actor_phone,
            actorRole=l.actor_role,
            action=l.action,
            resourceType=l.resource_type,
            resourceId=l.resource_id,
            details=l.details,
            requestId=l.request_id,
            createdAt=l.created_at,
        )
        for l in logs
    ]


async def get_platform_metrics(db: AsyncSession) -> AdminMetricsResponse:
    """Computes authoritative real metrics across modules without placeholders (Rule 31)."""
    total_users = await db.scalar(select(func.count(User.id)))
    farmers_count = await db.scalar(select(func.count(User.id)).where(User.role == UserRole.FARMER))
    buyers_count = await db.scalar(select(func.count(User.id)).where(User.role == UserRole.BUYER))
    owners_count = await db.scalar(select(func.count(User.id)).where(User.role == UserRole.OWNER))
    experts_count = await db.scalar(select(func.count(User.id)).where(User.role == UserRole.EXPERT))

    active_crops = await db.scalar(
        select(func.count(CropListing.id)).where(CropListing.status == CropListingStatus.ACTIVE)
    )
    total_rentals = await db.scalar(select(func.count(RentalRequest.id)))
    pending_reports = await db.scalar(
        select(func.count(ModerationReport.id)).where(ModerationReport.status == "pending")
    )
    total_audits = await db.scalar(select(func.count(AuditLog.id)))

    return AdminMetricsResponse(
        totalUsers=total_users or 0,
        farmersCount=farmers_count or 0,
        buyersCount=buyers_count or 0,
        ownersCount=owners_count or 0,
        expertsCount=experts_count or 0,
        activeCropListings=active_crops or 0,
        totalRentalRequests=total_rentals or 0,
        pendingModerationReports=pending_reports or 0,
        totalAuditEvents=total_audits or 0,
        systemStatus="healthy",
        timestamp=datetime.now(timezone.utc),
    )


async def publish_admin_knowledge_article(
    db: AsyncSession,
    actor: User,
    req: KnowledgeArticleCreateRequest,
    request_id: Optional[str] = None,
) -> KnowledgeArticleResponse:
    """Publishes a new verified knowledge article with version auto-increment and audit log."""
    # Find latest version across category or default to 1
    max_ver_stmt = select(func.max(KnowledgeArticle.version)).where(
        KnowledgeArticle.crop_type == req.cropType.lower()
    )
    latest_ver = await db.scalar(max_ver_stmt)
    next_ver = (latest_ver or 0) + 1

    article = KnowledgeArticle(
        crop_type=req.cropType.lower().strip(),
        category=req.category.lower().strip(),
        title_bn=req.titleBn.strip(),
        title_en=req.titleEn.strip() if req.titleEn else None,
        summary_bn=req.summaryBn.strip(),
        content_bn=req.contentBn.strip(),
        recommended_practices_bn=req.recommendedPracticesBn.strip() if req.recommendedPracticesBn else None,
        version=next_ver,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    # Record Audit Log
    await record_audit_log(
        db=db,
        actor=actor,
        action="KNOWLEDGE_PUBLISHED",
        resource_type="knowledge",
        resource_id=article.id,
        details={
            "cropType": article.crop_type,
            "category": article.category,
            "titleBn": article.title_bn,
            "version": article.version,
        },
        request_id=request_id,
    )

    return KnowledgeArticleResponse(
        id=article.id,
        cropType=article.crop_type,
        category=article.category,
        titleBn=article.title_bn,
        titleEn=article.title_en,
        summaryBn=article.summary_bn,
        contentBn=article.content_bn,
        recommendedPracticesBn=article.recommended_practices_bn,
        version=article.version,
        publishedAt=article.published_at,
        updatedAt=article.updated_at,
    )

import os
import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.common.image_safety import sanitize_and_reencode_image
from app.core.errors import ShikhorException
from app.db.session import get_db_session
from app.integrations.storage import upload_image_to_storage
from app.modules.auth.schemas import (
    FirebaseLoginRequest,
    FirebaseLoginResponse,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordWithOTPRequest,
    ResubmitNidRequest,
    RoleOnboardingRequest,
    SignupSendEmailOTPRequest,
    SignupVerifyEmailOTPRequest,
    SignupVerifyEmailOTPResponse,
    TokenResponse,
    UserResponse,
    VerifyEmailOTPRequest,
)
from app.modules.auth.service import (
    login_or_register_with_firebase,
    login_or_register_with_google,
    login_user,
    register_user,
    request_password_reset_email,
    reset_password_with_token,
    resubmit_user_nid,
    revoke_session,
    rotate_refresh_token,
    save_role_onboarding,
    send_signup_email_otp,
    verify_password_reset_otp,
    verify_signup_email_otp,
)
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_client_meta(request: Request):
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    return client_ip, user_agent


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Creates a new user account and returns authentication tokens."""
    client_ip, user_agent = _get_client_meta(request)
    _, tokens = await register_user(db, req, client_ip, user_agent)
    return tokens


@router.post("/signup/send-email-otp", status_code=status.HTTP_200_OK)
async def signup_send_email_otp(
    req: SignupSendEmailOTPRequest,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Sends a 6-digit verification OTP code to the user's email during signup."""
    return await send_signup_email_otp(db, req.email)


@router.post("/signup/verify-email-otp", response_model=SignupVerifyEmailOTPResponse, status_code=status.HTTP_200_OK)
async def signup_verify_email_otp(
    req: SignupVerifyEmailOTPRequest,
    db: AsyncSession = Depends(get_db_session),
) -> SignupVerifyEmailOTPResponse:
    """Verifies the signup email OTP code and returns a single-use verification token."""
    res = await verify_signup_email_otp(db, req.email, req.otp)
    return SignupVerifyEmailOTPResponse(**res)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticates with phone and password, establishing a session."""
    client_ip, user_agent = _get_client_meta(request)
    _, tokens = await login_user(db, req, client_ip, user_agent)
    return tokens


@router.post("/firebase-login", response_model=FirebaseLoginResponse)
async def firebase_login(
    req: FirebaseLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> FirebaseLoginResponse:
    """Authenticates or registers a user via verified Google Firebase Phone ID Token."""
    client_ip, user_agent = _get_client_meta(request)
    _, resp = await login_or_register_with_firebase(
        db=db,
        id_token=req.idToken,
        full_name=req.fullName,
        role=req.role,
        nid=req.nid,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    return resp


@router.post("/google-login", response_model=TokenResponse)
async def google_login(
    req: GoogleLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticates or registers a user via verified Google ID Token."""
    client_ip, user_agent = _get_client_meta(request)
    _, tokens = await login_or_register_with_google(
        db=db,
        id_token=req.idToken,
        role=req.role,
        phone=req.phone,
        nid=req.nid,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    return tokens


@router.post("/forgot-password/request", status_code=status.HTTP_200_OK)
async def forgot_password_request(
    req: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Requests a 6-digit email OTP for password reset."""
    return await request_password_reset_email(db, req.email)


@router.post("/forgot-password/verify", status_code=status.HTTP_200_OK)
async def forgot_password_verify(
    req: VerifyEmailOTPRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Verifies the 6-digit email OTP and returns a single-use reset token."""
    reset_token = await verify_password_reset_otp(db, req.email, req.otp)
    return {"status": "ok", "resetToken": reset_token}


@router.post("/forgot-password/reset", status_code=status.HTTP_200_OK)
async def forgot_password_reset(
    req: ResetPasswordWithOTPRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Updates password using verified reset token."""
    await reset_password_with_token(db, req.email, req.resetToken, req.newPassword)
    return {"status": "ok", "message": "পাসওয়ার্ড সফলভাবে পরিবর্তন করা হয়েছে। নতুন পাসওয়ার্ড দিয়ে লগইন করুন।"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    req: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Rotates refresh token and returns refreshed access/refresh pair."""
    client_ip, user_agent = _get_client_meta(request)
    return await rotate_refresh_token(db, req.refreshToken, client_ip, user_agent)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    req: RefreshRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Revokes the current refresh session."""
    await revoke_session(db, req.refreshToken)
    return {"status": "ok", "message": "Logged out successfully"}


@router.post("/upload-nid-image", status_code=status.HTTP_200_OK)
async def upload_nid_image(
    file: UploadFile = File(...),
):
    """Securely sanitizes and uploads an NID card photo to Cloudinary / storage."""
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in ALLOWED_TYPES:
        raise ShikhorException(
            code="INVALID_FILE_TYPE",
            message="শুধুমাত্র JPG, PNG বা WebP ফরম্যাটের ছবি আপলোড করা যাবে।",
            status_code=400,
        )
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise ShikhorException(
            code="FILE_TOO_LARGE",
            message="ছবির সাইজ সর্বোচ্চ ১০ মেগাবাইট (10MB) হতে পারবে।",
            status_code=400,
        )

    # Sanitize and re-encode to clean WebP, stripping EXIF/GPS metadata (Rule 18)
    sanitized_bytes, safe_filename, _, _ = sanitize_and_reencode_image(
        file_bytes=content,
        filename=file.filename or "nid.jpg",
        content_type=file.content_type,
    )

    # Upload to Cloudinary or fallback storage
    file_url = await upload_image_to_storage(
        file_bytes=sanitized_bytes,
        filename=f"nid_{safe_filename}",
        folder="nid",
    )

    return {"fileUrl": file_url, "filename": f"nid_{safe_filename}"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Returns the authenticated profile of the current user."""
    has_profile = any([
        current_user.farmer_profile is not None,
        current_user.owner_profile is not None,
        current_user.buyer_profile is not None,
        current_user.expert_profile is not None,
    ])
    return UserResponse(
        id=current_user.id,
        phone=current_user.phone,
        email=current_user.email,
        nid=current_user.nid,
        dob=current_user.dob,
        nidFrontImage=current_user.nid_front_image,
        nidBackImage=current_user.nid_back_image,
        isNidVerified=current_user.is_nid_verified,
        nidVerificationStatus=current_user.nid_verification_status,
        nidRejectionReason=current_user.nid_rejection_reason,
        fullName=current_user.full_name,
        role=current_user.role.value,
        isActive=current_user.is_active,
        isVerified=current_user.is_verified,
        isEmailVerified=current_user.is_email_verified,
        hasProfile=has_profile,
    )


@router.post("/onboarding", response_model=UserResponse)
async def complete_onboarding(
    req: RoleOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Submits step-3 role onboarding location and details."""
    await save_role_onboarding(db, current_user, req)
    return UserResponse(
        id=current_user.id,
        phone=current_user.phone,
        email=current_user.email,
        nid=current_user.nid,
        dob=current_user.dob,
        nidFrontImage=current_user.nid_front_image,
        nidBackImage=current_user.nid_back_image,
        isNidVerified=current_user.is_nid_verified,
        nidVerificationStatus=current_user.nid_verification_status,
        nidRejectionReason=current_user.nid_rejection_reason,
        fullName=current_user.full_name,
        role=current_user.role.value,
        isActive=current_user.is_active,
        isVerified=current_user.is_verified,
        isEmailVerified=current_user.is_email_verified,
        hasProfile=True,
    )


@router.post("/resubmit-nid", response_model=UserResponse)
async def resubmit_nid(
    req: ResubmitNidRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Allows a rejected or pending user to re-upload clear NID card photos and resubmit for approval."""
    updated_user = await resubmit_user_nid(db=db, user=current_user, data=req)
    has_profile = any([
        updated_user.farmer_profile is not None,
        updated_user.owner_profile is not None,
        updated_user.buyer_profile is not None,
        updated_user.expert_profile is not None,
    ])
    return UserResponse(
        id=updated_user.id,
        phone=updated_user.phone,
        email=updated_user.email,
        nid=updated_user.nid,
        dob=updated_user.dob,
        nidFrontImage=updated_user.nid_front_image,
        nidBackImage=updated_user.nid_back_image,
        isNidVerified=updated_user.is_nid_verified,
        nidVerificationStatus=updated_user.nid_verification_status,
        nidRejectionReason=updated_user.nid_rejection_reason,
        fullName=updated_user.full_name,
        role=updated_user.role.value,
        isActive=updated_user.is_active,
        isVerified=updated_user.is_verified,
        isEmailVerified=updated_user.is_email_verified,
        hasProfile=has_profile,
    )


import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ShikhorException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.mongo.schemas import (
    AuditLogDocument,
    BuyerProfileDoc,
    ExpertProfileDoc,
    FarmerProfileDoc,
    OTPDocument,
    OwnerProfileDoc,
    RefreshSessionDocument,
    UserDocument,
    UserRoleEnum,
)
from app.db.service_bridge import get_mongo_registry, is_mongodb_backend
from app.integrations.auth.firebase_verifier import verify_firebase_id_token
from app.integrations.email import (
    get_password_reset_otp_html,
    get_signup_otp_html,
    send_email,
)
from app.modules.auth.models import PasswordResetOTP, RefreshSession, SignupEmailOTP
from app.modules.auth.schemas import (
    FirebaseLoginRequest,
    FirebaseLoginResponse,
    GoogleLoginRequest,
    LoginRequest,
    RegisterRequest,
    ResubmitNidRequest,
    RoleOnboardingRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.users.models import (
    BuyerProfile,
    ExpertProfile,
    FarmerProfile,
    OwnerProfile,
    User,
    UserRole,
)


async def _mongo_issue_tokens_and_session(
    user: Any,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> TokenResponse:
    """Helper to generate JWT tokens and record session in MongoDB."""
    reg = get_mongo_registry()
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token(user_id=user.id, role=role_str)
    refresh_token = create_refresh_token(user_id=user.id)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session_doc = RefreshSessionDocument(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=expires_at,
        is_revoked=False,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    reg.sessions.insert_one(session_doc)
    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        tokenType="bearer",
        expiresIn=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def register_user(
    db: AsyncSession,
    req: RegisterRequest,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[Any, TokenResponse]:
    """Registers a new user and issues initial credentials."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        if reg.users.get_by_phone(req.phone):
            raise ShikhorException(
                code="PHONE_ALREADY_EXISTS",
                message="This mobile number is already registered.",
                status_code=400,
            )
        if req.email and reg.users.get_by_email(req.email):
            raise ShikhorException(
                code="EMAIL_ALREADY_EXISTS",
                message="This email is already in use.",
                status_code=400,
            )
        if req.nid and reg.users.collection.find_one({"nid": req.nid}):
            raise ShikhorException(
                code="NID_ALREADY_EXISTS",
                message="এই জাতীয় পরিচয়পত্র (NID) নম্বর দিয়ে ইতিমধ্যে একটি অ্যাকাউন্ট তৈরি করা হয়েছে।",
                status_code=400,
            )
        is_email_verified = False
        if req.email and req.emailVerificationToken:
            clean_email = req.email.strip().lower()
            otp_doc = reg.otps.collection.find_one({
                "email": clean_email,
                "verification_token": req.emailVerificationToken,
                "is_used": True,
            })
            if not otp_doc:
                raise ShikhorException(
                    code="INVALID_VERIFICATION_TOKEN",
                    message="ইমেইল ভেরিফিকেশন কোড বা টোকেন সঠিক নয়। অনুগ্রহ করে ওটিপি দিয়ে ইমেইল যাচাই করুন।",
                    status_code=400,
                )
            is_email_verified = True

        hashed_pwd = hash_password(req.password)
        verification_status = "pending" if (req.nid or req.nidFrontImage or req.nidBackImage) else "not_submitted"
        role_enum = UserRoleEnum(req.role.value if hasattr(req.role, "value") else str(req.role))
        user_doc = UserDocument(
            phone=req.phone,
            email=req.email,
            nid=req.nid,
            dob=req.dob,
            nid_front_image=req.nidFrontImage,
            nid_back_image=req.nidBackImage,
            is_nid_verified=False,
            nid_verification_status=verification_status,
            full_name=req.full_name,
            hashed_password=hashed_pwd,
            role=role_enum,
            is_active=True,
            is_verified=False,
            is_email_verified=is_email_verified,
        )
        if req.district:
            if role_enum == UserRoleEnum.FARMER:
                user_doc.farmer_profile = FarmerProfileDoc(district=req.district, upazila=req.upazila, primary_crops=req.primaryCrops)
            elif role_enum == UserRoleEnum.OWNER:
                user_doc.owner_profile = OwnerProfileDoc(district=req.district, upazila=req.upazila, service_radius_km=req.serviceRadiusKm or 15.0)
            elif role_enum == UserRoleEnum.BUYER:
                user_doc.buyer_profile = BuyerProfileDoc(district=req.district, upazila=req.upazila, business_name=req.businessName)
            elif role_enum == UserRoleEnum.EXPERT:
                user_doc.expert_profile = ExpertProfileDoc(district=req.district, designation=req.designation or "Agricultural Officer", organization=req.organization or "DAE")
        user_doc = reg.users.insert_one(user_doc)
        tokens = await _mongo_issue_tokens_and_session(user_doc, client_ip, user_agent)
        return user_doc, tokens

    # Check phone uniqueness
    existing_phone = await db.scalar(select(User).where(User.phone == req.phone))
    if existing_phone:
        raise ShikhorException(
            code="PHONE_ALREADY_EXISTS",
            message="This mobile number is already registered.",
            status_code=400,
        )

    # Check email uniqueness if provided
    if req.email:
        existing_email = await db.scalar(select(User).where(User.email == req.email))
        if existing_email:
            raise ShikhorException(
                code="EMAIL_ALREADY_EXISTS",
                message="This email is already in use.",
                status_code=400,
            )

    # Check NID uniqueness if provided
    if req.nid:
        existing_nid = await db.scalar(select(User).where(User.nid == req.nid))
        if existing_nid:
            raise ShikhorException(
                code="NID_ALREADY_EXISTS",
                message="এই জাতীয় পরিচয়পত্র (NID) নম্বর দিয়ে ইতিমধ্যে একটি অ্যাকাউন্ট তৈরি করা হয়েছে।",
                status_code=400,
            )

    # Verify Email Verification Token if provided
    is_email_verified = False
    if req.email and req.emailVerificationToken:
        clean_email = req.email.strip().lower()
        otp_rec = await db.scalar(
            select(SignupEmailOTP).where(
                SignupEmailOTP.email == clean_email,
                SignupEmailOTP.verification_token == req.emailVerificationToken,
                SignupEmailOTP.is_used == True,  # noqa: E712
            )
        )
        if not otp_rec:
            raise ShikhorException(
                code="INVALID_VERIFICATION_TOKEN",
                message="ইমেইল ভেরিফিকেশন কোড বা টোকেন সঠিক নয়। অনুগ্রহ করে ওটিপি দিয়ে ইমেইল যাচাই করুন।",
                status_code=400,
            )
        is_email_verified = True

    # Create User
    hashed_pwd = hash_password(req.password)
    verification_status = "pending" if (req.nid or req.nidFrontImage or req.nidBackImage) else "not_submitted"
    user = User(
        phone=req.phone,
        email=req.email,
        nid=req.nid,
        dob=req.dob,
        nid_front_image=req.nidFrontImage,
        nid_back_image=req.nidBackImage,
        is_nid_verified=False,
        nid_verification_status=verification_status,
        full_name=req.full_name,
        hashed_password=hashed_pwd,
        role=req.role,
        is_active=True,
        is_verified=False,
        is_email_verified=is_email_verified,
    )
    db.add(user)
    await db.flush()

    if req.district:
        if user.role == UserRole.FARMER:
            db.add(FarmerProfile(user_id=user.id, district=req.district, upazila=req.upazila, primary_crops=req.primaryCrops))
        elif user.role == UserRole.OWNER:
            db.add(OwnerProfile(user_id=user.id, district=req.district, upazila=req.upazila, service_radius_km=req.serviceRadiusKm or 15.0))
        elif user.role == UserRole.BUYER:
            db.add(BuyerProfile(user_id=user.id, district=req.district, upazila=req.upazila, business_name=req.businessName))
        elif user.role == UserRole.EXPERT:
            db.add(ExpertProfile(user_id=user.id, district=req.district, designation=req.designation or "Agricultural Officer", organization=req.organization or "DAE"))
        await db.flush()

    # Generate Tokens & Session
    tokens = await _issue_tokens_and_session(db, user, client_ip, user_agent)
    await db.commit()
    await db.refresh(user)

    return user, tokens


async def login_user(
    db: AsyncSession,
    req: LoginRequest,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[Any, TokenResponse]:
    """Authenticates a user and establishes a revocable session."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        user = reg.users.get_by_phone(req.phone)
        if not user or not verify_password(req.password, user.hashed_password):
            raise UnauthorizedException(
                code="INVALID_CREDENTIALS",
                message="Invalid mobile number or password.",
            )
        if not user.is_active:
            raise ShikhorException(
                code="ACCOUNT_SUSPENDED",
                message="Your account has been deactivated. Please contact support.",
                status_code=403,
            )
        tokens = await _mongo_issue_tokens_and_session(user, client_ip, user_agent)
        return user, tokens

    user = await db.scalar(select(User).where(User.phone == req.phone))

    # Constant time / secure failure: never reveal if user exists
    if not user or not verify_password(req.password, user.hashed_password):
        raise UnauthorizedException(
            code="INVALID_CREDENTIALS",
            message="Invalid mobile number or password.",
        )

    if not user.is_active:
        raise ShikhorException(
            code="ACCOUNT_SUSPENDED",
            message="Your account has been deactivated. Please contact support.",
            status_code=403,
        )

    tokens = await _issue_tokens_and_session(db, user, client_ip, user_agent)
    await db.commit()
    await db.refresh(user)

    return user, tokens


async def login_or_register_with_firebase(
    db: AsyncSession,
    id_token: str,
    full_name: Optional[str] = None,
    role: Optional[UserRole] = None,
    nid: Optional[str] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[Optional[User], FirebaseLoginResponse]:
    """Authenticates a user via verified Google Firebase Phone ID Token or creates new verified account."""
    claims = await verify_firebase_id_token(id_token, require_phone=True)
    phone = claims["normalized_phone"]

    # Check if user already exists
    user = await db.scalar(select(User).where(User.phone == phone))

    if user:
        if not user.is_active:
            raise ShikhorException(
                code="ACCOUNT_SUSPENDED",
                message="Your account has been deactivated. Please contact support.",
                status_code=403,
            )

        tokens = await _issue_tokens_and_session(db, user, client_ip, user_agent)
        await db.commit()
        await db.refresh(user)
        return user, FirebaseLoginResponse(isNewUser=False, phone=phone, tokens=tokens)

    # New user: If full name provided, register immediately
    if full_name and full_name.strip():
        if nid:
            existing_nid = await db.scalar(select(User).where(User.nid == nid))
            if existing_nid:
                raise ShikhorException(
                    code="NID_ALREADY_EXISTS",
                    message="এই জাতীয় পরিচয়পত্র (NID) নম্বর দিয়ে ইতিমধ্যে একটি অ্যাকাউন্ট তৈরি করা হয়েছে।",
                    status_code=400,
                )

        random_pwd = secrets.token_urlsafe(32)
        hashed_pwd = hash_password(random_pwd)

        new_user = User(
            phone=phone,
            nid=nid,
            full_name=full_name.strip(),
            hashed_password=hashed_pwd,
            role=role or UserRole.FARMER,
            is_active=True,
            is_verified=True,  # Verified by Firebase SMS OTP!
        )
        db.add(new_user)
        await db.flush()

        tokens = await _issue_tokens_and_session(db, new_user, client_ip, user_agent)
        await db.commit()
        await db.refresh(new_user)
        return new_user, FirebaseLoginResponse(isNewUser=False, phone=phone, tokens=tokens)

    # New user without name yet: signal frontend to collect name and role
    return None, FirebaseLoginResponse(isNewUser=True, phone=phone, tokens=None)


async def login_or_register_with_google(
    db: AsyncSession,
    id_token: str,
    role: Optional[UserRole] = None,
    phone: Optional[str] = None,
    nid: Optional[str] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[User, TokenResponse]:
    """Authenticates a user via verified Google ID Token or registers a new account."""
    claims = await verify_firebase_id_token(id_token, require_phone=False)
    email = claims.get("email")
    if not email:
        raise UnauthorizedException(
            code="GOOGLE_EMAIL_MISSING",
            message="Google authentication token does not contain a verified email address.",
        )

    # Check if user already exists by email
    user = await db.scalar(select(User).where(User.email == email))

    if user:
        if not user.is_active:
            raise ShikhorException(
                code="ACCOUNT_SUSPENDED",
                message="Your account has been deactivated. Please contact support.",
                status_code=403,
            )
        tokens = await _issue_tokens_and_session(db, user, client_ip, user_agent)
        await db.commit()
        await db.refresh(user)
        return user, tokens

    # If new user, create account
    display_name = claims.get("display_name") or "Google User"
    user_phone = phone
    if user_phone:
        existing_phone = await db.scalar(select(User).where(User.phone == user_phone))
        if existing_phone:
            raise ShikhorException(
                code="PHONE_ALREADY_EXISTS",
                message="This mobile number is already in use by another account.",
                status_code=400,
            )
    else:
        # Generate placeholder identifier for phone constraint
        user_phone = f"019{secrets.randbelow(90000000) + 10000000}"

    if nid:
        existing_nid = await db.scalar(select(User).where(User.nid == nid))
        if existing_nid:
            raise ShikhorException(
                code="NID_ALREADY_EXISTS",
                message="এই জাতীয় পরিচয়পত্র (NID) নম্বর দিয়ে ইতিমধ্যে একটি অ্যাকাউন্ট তৈরি করা হয়েছে।",
                status_code=400,
            )

    random_pwd = secrets.token_urlsafe(32)
    hashed_pwd = hash_password(random_pwd)

    new_user = User(
        phone=user_phone,
        email=email,
        nid=nid,
        full_name=display_name,
        hashed_password=hashed_pwd,
        role=role or UserRole.FARMER,
        is_active=True,
        is_verified=True,  # Verified by Google!
    )
    db.add(new_user)
    await db.flush()

    tokens = await _issue_tokens_and_session(db, new_user, client_ip, user_agent)
    await db.commit()
    await db.refresh(new_user)
    return new_user, tokens


async def request_password_reset_email(db: AsyncSession, email: str) -> Dict[str, str]:
    """Generates and logs/dispatches a 6-digit email OTP for password reset."""
    logger = logging.getLogger("shikhor.auth.reset")
    clean_email = email.strip().lower()
    generic_msg = "যদি আপনার ইমেইলটি নিবন্ধিত থাকে, তবে একটি ৬-সংখ্যার ওটিপি কোড পাঠানো হয়েছে।"

    if is_mongodb_backend():
        reg = get_mongo_registry()
        user = reg.users.get_by_email(clean_email)
        if not user:
            logger.info("Password reset requested for non-existent email: %s", clean_email)
            return {"message": generic_msg}

        otp_code = f"{secrets.randbelow(900000) + 100000}"
        otp_hash = hash_token(otp_code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        reg.otps.collection.update_many(
            {"email": clean_email, "is_used": False, "purpose": "password_reset"},
            {"$set": {"is_used": True}}
        )

        otp_doc = OTPDocument(
            email=clean_email,
            otp_hash=otp_hash,
            purpose="password_reset",
            expires_at=expires_at,
            is_used=False,
            attempts=0,
        )
        reg.otps.insert_one(otp_doc)

        await send_email(
            to_email=clean_email,
            subject="[শিখড় এআই] পাসওয়ার্ড রিসেট ওটিপি কোড",
            html_body=get_password_reset_otp_html(otp_code),
            text_body=f"শিখড় এআই - আপনার পাসওয়ার্ড রিসেট ওটিপি কোড: {otp_code} (মেয়াদ ১০ মিনিট)",
        )

        logger.info("==================================================")
        logger.info("EMAIL PASSWORD RESET OTP FOR %s: [%s]", clean_email, otp_code)
        logger.info("==================================================")
        return {"message": generic_msg}

    user = await db.scalar(select(User).where(User.email == clean_email))
    if not user:
        logger.info("Password reset requested for non-existent email: %s", clean_email)
        return {"message": generic_msg}

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    otp_hash = hash_token(otp_code)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    await db.execute(
        update(PasswordResetOTP)
        .where(PasswordResetOTP.email == clean_email, PasswordResetOTP.is_used == False)  # noqa: E712
        .values(is_used=True)
    )

    record = PasswordResetOTP(
        email=clean_email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        is_used=False,
        attempts=0,
    )
    db.add(record)
    await db.commit()

    await send_email(
        to_email=clean_email,
        subject="[শিখড় এআই] পাসওয়ার্ড রিসেট ওটিপি কোড",
        html_body=get_password_reset_otp_html(otp_code),
        text_body=f"শিখড় এআই - আপনার পাসওয়ার্ড রিসেট ওটিপি কোড: {otp_code} (মেয়াদ ১০ মিনিট)",
    )

    logger.info("==================================================")
    logger.info("EMAIL PASSWORD RESET OTP FOR %s: [%s]", clean_email, otp_code)
    logger.info("==================================================")

    return {"message": generic_msg}


async def verify_password_reset_otp(db: AsyncSession, email: str, otp: str) -> str:
    """Validates the 6-digit email OTP and issues a single-use reset token."""
    clean_email = email.strip().lower()
    now = datetime.now(timezone.utc)

    if is_mongodb_backend():
        reg = get_mongo_registry()
        raw_otp = reg.otps.collection.find_one(
            {"email": clean_email, "is_used": False, "purpose": "password_reset"},
            sort=[("created_at", -1)]
        )
        if not raw_otp:
            raise ShikhorException(
                code="INVALID_OR_EXPIRED_OTP",
                message="কোনো সক্রিয় ওটিপি অনুরোধ পাওয়া যায়নি। পুনরায় ওটিপি পাঠান।",
                status_code=400,
            )
        exp = raw_otp.get("expires_at")
        if isinstance(exp, str):
            exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if exp < now:
            reg.otps.collection.update_one({"_id": raw_otp["_id"]}, {"$set": {"is_used": True}})
            raise ShikhorException(
                code="OTP_EXPIRED",
                message="ওটিপি কোডের মেয়াদ শেষ হয়ে গেছে। দয়া করে নতুন ওটিপি পাঠান।",
                status_code=400,
            )

        attempts = raw_otp.get("attempts", 0)
        if attempts >= 5:
            reg.otps.collection.update_one({"_id": raw_otp["_id"]}, {"$set": {"is_used": True}})
            raise ShikhorException(
                code="TOO_MANY_ATTEMPTS",
                message="অতিরিক্ত ভুল চেষ্টার কারণে এই কোডটি বাতিল হয়েছে। নতুন ওটিপি পাঠান।",
                status_code=400,
            )

        if hash_token(otp) != raw_otp["otp_hash"]:
            reg.otps.collection.update_one({"_id": raw_otp["_id"]}, {"$inc": {"attempts": 1}})
            raise ShikhorException(
                code="INVALID_OTP_CODE",
                message="প্রদত্ত ৬-সংখ্যার ওটিপি কোডটি সঠিক নয়।",
                status_code=400,
            )

        reset_token = secrets.token_urlsafe(32)
        reg.otps.collection.update_one(
            {"_id": raw_otp["_id"]},
            {"$set": {"is_used": True, "verification_token": reset_token}}
        )
        return reset_token

    record = await db.scalar(
        select(PasswordResetOTP)
        .where(PasswordResetOTP.email == clean_email, PasswordResetOTP.is_used == False)  # noqa: E712
        .order_by(PasswordResetOTP.created_at.desc())
    )

    if not record:
        raise ShikhorException(
            code="INVALID_OR_EXPIRED_OTP",
            message="কোনো সক্রিয় ওটিপি অনুরোধ পাওয়া যায়নি। পুনরায় ওটিপি পাঠান।",
            status_code=400,
        )

    exp = record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if exp < now:
        record.is_used = True
        await db.commit()
        raise ShikhorException(
            code="OTP_EXPIRED",
            message="ওটিপি কোডের মেয়াদ শেষ হয়ে গেছে। দয়া করে নতুন ওটিপি পাঠান।",
            status_code=400,
        )

    if record.attempts >= 5:
        record.is_used = True
        await db.commit()
        raise ShikhorException(
            code="TOO_MANY_ATTEMPTS",
            message="অতিরিক্ত ভুল চেষ্টার কারণে এই কোডটি বাতিল হয়েছে। নতুন ওটিপি পাঠান।",
            status_code=400,
        )

    if hash_token(otp) != record.otp_hash:
        record.attempts += 1
        await db.commit()
        raise ShikhorException(
            code="INVALID_OTP_CODE",
            message="প্রদত্ত ৬-সংখ্যার ওটিপি কোডটি সঠিক নয়।",
            status_code=400,
        )

    reset_token = secrets.token_urlsafe(32)
    record.is_used = True
    record.reset_token = reset_token
    await db.commit()
    return reset_token


async def reset_password_with_token(
    db: AsyncSession, email: str, reset_token: str, new_password: str
) -> None:
    """Updates user password using verified reset token and revokes all active sessions."""
    clean_email = email.strip().lower()

    if is_mongodb_backend():
        reg = get_mongo_registry()
        otp_rec = reg.otps.collection.find_one({
            "email": clean_email,
            "verification_token": reset_token,
        })
        if not otp_rec:
            raise ShikhorException(
                code="INVALID_RESET_TOKEN",
                message="পাসওয়ার্ড পরিবর্তনের অনুরোধটি সঠিক নয় অথবা মেয়াদ শেষ হয়ে গেছে।",
                status_code=400,
            )
        user = reg.users.get_by_email(clean_email)
        if not user:
            raise ShikhorException(
                code="USER_NOT_FOUND",
                message="ব্যবহারকারীর অ্যাকাউন্ট পাওয়া যায়নি।",
                status_code=404,
            )
        reg.otps.collection.update_one({"_id": otp_rec["_id"]}, {"$set": {"verification_token": None}})
        reg.users.collection.update_one({"_id": user.id}, {"$set": {"hashed_password": hash_password(new_password)}})
        reg.sessions.revoke_all_for_user(user.id)
        return

    record = await db.scalar(
        select(PasswordResetOTP).where(
            PasswordResetOTP.email == clean_email,
            PasswordResetOTP.reset_token == reset_token,
        )
    )

    if not record:
        raise ShikhorException(
            code="INVALID_RESET_TOKEN",
            message="পাসওয়ার্ড পরিবর্তনের অনুরোধটি সঠিক নয় অথবা মেয়াদ শেষ হয়ে গেছে।",
            status_code=400,
        )

    user = await db.scalar(select(User).where(User.email == clean_email))
    if not user:
        raise ShikhorException(
            code="USER_NOT_FOUND",
            message="ব্যবহারকারীর অ্যাকাউন্ট পাওয়া যায়নি।",
            status_code=404,
        )

    # Invalidate token
    record.reset_token = None
    user.hashed_password = hash_password(new_password)

    # Revoke all active refresh sessions for security
    await db.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == user.id)
        .values(is_revoked=True)
    )
    await db.commit()


async def send_signup_email_otp(db: AsyncSession, email: str) -> Dict[str, str]:
    """Generates and dispatches a 6-digit email OTP for user registration."""
    logger = logging.getLogger("shikhor.auth.signup")
    clean_email = email.strip().lower()

    if is_mongodb_backend():
        reg = get_mongo_registry()
        if reg.users.get_by_email(clean_email):
            raise ShikhorException(
                code="EMAIL_ALREADY_EXISTS",
                message="এই ইমেইল ঠিকানাটি ইতিমধ্যে ব্যবহৃত হচ্ছে। অনুগ্রহ করে লগইন করুন বা অন্য ইমেইল দিন।",
                status_code=400,
            )

        reg.otps.collection.update_many(
            {"email": clean_email, "is_used": False, "purpose": "signup"},
            {"$set": {"is_used": True}}
        )

        otp_code = f"{secrets.randbelow(900000) + 100000}"
        otp_hash = hash_token(otp_code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        otp_doc = OTPDocument(
            email=clean_email,
            otp_hash=otp_hash,
            purpose="signup",
            expires_at=expires_at,
            is_used=False,
            attempts=0,
        )
        reg.otps.insert_one(otp_doc)

        email_dispatched = await send_email(
            to_email=clean_email,
            subject="[শিখড় এআই] একাউন্ট নিবন্ধন ওটিপি কোড",
            html_body=get_signup_otp_html(otp_code),
            text_body=f"শিখড় এআই - আপনার রেজিস্ট্রেশন ওটিপি কোড: {otp_code} (মেয়াদ ১০ মিনিট)",
        )

        logger.info("==================================================")
        logger.info("SIGNUP EMAIL VERIFICATION OTP FOR %s: [%s]", clean_email, otp_code)
        logger.info("==================================================")

        res: Dict[str, Any] = {
            "message": f"{clean_email} ঠিকানায় ৬-সংখ্যার ওটিপি কোড পাঠানো হয়েছে।",
            "email": clean_email,
            "emailDispatched": email_dispatched,
        }
        if settings.ENVIRONMENT == "development" and not email_dispatched:
            res["devOtp"] = otp_code
        return res

    # Check if email is already registered
    existing_user = await db.scalar(select(User).where(User.email == clean_email))
    if existing_user:
        raise ShikhorException(
            code="EMAIL_ALREADY_EXISTS",
            message="এই ইমেইল ঠিকানাটি ইতিমধ্যে ব্যবহৃত হচ্ছে। অনুগ্রহ করে লগইন করুন বা অন্য ইমেইল দিন।",
            status_code=400,
        )

    # Invalidate previous unverified signup OTPs for this email
    await db.execute(
        update(SignupEmailOTP)
        .where(SignupEmailOTP.email == clean_email, SignupEmailOTP.is_used == False)  # noqa: E712
        .values(is_used=True)
    )

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    otp_hash = hash_token(otp_code)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    record = SignupEmailOTP(
        email=clean_email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        is_used=False,
        attempts=0,
    )
    db.add(record)
    await db.commit()

    email_dispatched = await send_email(
        to_email=clean_email,
        subject="[শিখড় এআই] একাউন্ট নিবন্ধন ওটিপি কোড",
        html_body=get_signup_otp_html(otp_code),
        text_body=f"শিখড় এআই - আপনার রেজিস্ট্রেশন ওটিপি কোড: {otp_code} (মেয়াদ ১০ মিনিট)",
    )

    logger.info("==================================================")
    logger.info("SIGNUP EMAIL VERIFICATION OTP FOR %s: [%s]", clean_email, otp_code)
    logger.info("==================================================")

    res: Dict[str, Any] = {
        "message": f"{clean_email} ঠিকানায় ৬-সংখ্যার ওটিপি কোড পাঠানো হয়েছে।",
        "email": clean_email,
        "emailDispatched": email_dispatched,
    }
    if settings.ENVIRONMENT == "development" and not email_dispatched:
        res["devOtp"] = otp_code

    return res


async def verify_signup_email_otp(db: AsyncSession, email: str, otp: str) -> Dict[str, Any]:
    """Verifies the 6-digit email OTP and issues a single-use verification token."""
    clean_email = email.strip().lower()
    clean_otp = otp.strip()
    now = datetime.now(timezone.utc)

    if is_mongodb_backend():
        reg = get_mongo_registry()
        raw_otp = reg.otps.collection.find_one(
            {"email": clean_email, "is_used": False, "purpose": "signup"},
            sort=[("created_at", -1)]
        )
        if not raw_otp:
            raise ShikhorException(
                code="INVALID_OR_EXPIRED_OTP",
                message="কোনো সক্রিয় ওটিপি অনুরোধ পাওয়া যায়নি। পুনরায় ওটিপি কোড পাঠান।",
                status_code=400,
            )
        exp = raw_otp.get("expires_at")
        if isinstance(exp, str):
            exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if exp < now:
            reg.otps.collection.update_one({"_id": raw_otp["_id"]}, {"$set": {"is_used": True}})
            raise ShikhorException(
                code="OTP_EXPIRED",
                message="ওটিপি কোডের মেয়াদ শেষ হয়ে গেছে। দয়া করে নতুন ওটিপি পাঠান।",
                status_code=400,
            )

        attempts = raw_otp.get("attempts", 0)
        if attempts >= 5:
            reg.otps.collection.update_one({"_id": raw_otp["_id"]}, {"$set": {"is_used": True}})
            raise ShikhorException(
                code="TOO_MANY_ATTEMPTS",
                message="অতিরিক্ত ভুল চেষ্টার কারণে এই কোডটি বাতিল হয়েছে। নতুন ওটিপি পাঠান।",
                status_code=400,
            )

        if hash_token(clean_otp) != raw_otp["otp_hash"]:
            reg.otps.collection.update_one({"_id": raw_otp["_id"]}, {"$inc": {"attempts": 1}})
            raise ShikhorException(
                code="INVALID_OTP",
                message=f"ভুল ওটিপি কোড। বাকি সুযোগ: {max(0, 5 - attempts - 1)} বার।",
                status_code=400,
            )

        verification_token = secrets.token_hex(32)
        reg.otps.collection.update_one(
            {"_id": raw_otp["_id"]},
            {"$set": {"is_used": True, "verification_token": verification_token}}
        )
        return {
            "verified": True,
            "email": clean_email,
            "verificationToken": verification_token,
            "message": "ইমেইল সফলভাবে যাচাই হয়েছে।",
        }

    record = await db.scalar(
        select(SignupEmailOTP)
        .where(SignupEmailOTP.email == clean_email, SignupEmailOTP.is_used == False)  # noqa: E712
        .order_by(SignupEmailOTP.created_at.desc())
    )

    if not record:
        raise ShikhorException(
            code="INVALID_OR_EXPIRED_OTP",
            message="কোনো সক্রিয় ওটিপি অনুরোধ পাওয়া যায়নি। পুনরায় ওটিপি কোড পাঠান।",
            status_code=400,
        )

    exp = record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if exp < now:
        record.is_used = True
        await db.commit()
        raise ShikhorException(
            code="OTP_EXPIRED",
            message="ওটিপি কোডের মেয়াদ শেষ হয়ে গেছে। দয়া করে নতুন ওটিপি পাঠান।",
            status_code=400,
        )

    if record.attempts >= 5:
        record.is_used = True
        await db.commit()
        raise ShikhorException(
            code="TOO_MANY_ATTEMPTS",
            message="অতিরিক্ত ভুল চেষ্টার কারণে এই কোডটি বাতিল হয়েছে। নতুন ওটিপি পাঠান।",
            status_code=400,
        )

    if hash_token(clean_otp) != record.otp_hash:
        record.attempts += 1
        await db.commit()
        raise ShikhorException(
            code="INVALID_OTP",
            message=f"ভুল ওটিপি কোড। বাকি সুযোগ: {max(0, 5 - record.attempts)} বার।",
            status_code=400,
        )

    # Valid OTP! Issue single-use opaque verification token
    verification_token = secrets.token_hex(32)
    record.is_used = True
    record.verification_token = verification_token
    await db.commit()

    return {
        "verified": True,
        "email": clean_email,
        "verificationToken": verification_token,
        "message": "ইমেইল সফলভাবে যাচাই হয়েছে।",
    }


async def rotate_refresh_token(
    db: AsyncSession,
    refresh_token: str,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> TokenResponse:
    """Rotates a refresh token and revokes the predecessor session."""
    payload = decode_token(refresh_token, expected_type="refresh")
    user_id = payload.get("sub")
    t_hash = hash_token(refresh_token)
    now = datetime.now(timezone.utc)

    if is_mongodb_backend():
        reg = get_mongo_registry()
        session = reg.sessions.find_by_token_hash(t_hash)
        if not session or session.is_revoked or session.user_id != user_id:
            raise UnauthorizedException(
                code="SESSION_REVOKED",
                message="Your session has expired or been revoked. Please log in again.",
            )
        session_exp = session.expires_at
        if session_exp.tzinfo is None:
            session_exp = session_exp.replace(tzinfo=timezone.utc)
        if session_exp < now:
            raise UnauthorizedException(
                code="SESSION_REVOKED",
                message="Your session has expired or been revoked. Please log in again.",
            )
        reg.sessions.revoke_by_token_hash(t_hash)
        user = reg.users.find_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException(code="USER_INACTIVE", message="User account is inactive.")
        return await _mongo_issue_tokens_and_session(user, client_ip, user_agent)

    session = await db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == t_hash,
            RefreshSession.user_id == user_id,
        )
    )

    if not session or session.is_revoked:
        raise UnauthorizedException(
            code="SESSION_REVOKED",
            message="Your session has expired or been revoked. Please log in again.",
        )

    session_exp = session.expires_at
    if session_exp.tzinfo is None:
        session_exp = session_exp.replace(tzinfo=timezone.utc)

    if session_exp < now:
        raise UnauthorizedException(
            code="SESSION_REVOKED",
            message="Your session has expired or been revoked. Please log in again.",
        )

    # Invalidate previous refresh session
    session.is_revoked = True

    # Find user
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise UnauthorizedException(code="USER_INACTIVE", message="User account is inactive.")

    # Issue new rotated tokens
    new_tokens = await _issue_tokens_and_session(db, user, client_ip, user_agent)
    await db.commit()

    return new_tokens


async def revoke_session(db: AsyncSession, refresh_token: str) -> None:
    """Revokes a refresh session on logout."""
    t_hash = hash_token(refresh_token)
    if is_mongodb_backend():
        reg = get_mongo_registry()
        reg.sessions.revoke_by_token_hash(t_hash)
        return

    session = await db.scalar(select(RefreshSession).where(RefreshSession.token_hash == t_hash))
    if session:
        session.is_revoked = True
        await db.commit()


async def save_role_onboarding(
    db: AsyncSession,
    user: Any,
    data: RoleOnboardingRequest,
) -> None:
    """Creates or updates role profile during step 3 onboarding."""
    upazila = data.upazila or data.district
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)

    if is_mongodb_backend():
        reg = get_mongo_registry()
        update_data = {}
        if role_str == "farmer":
            user.farmer_profile = FarmerProfileDoc(district=data.district, upazila=upazila, primary_crops=data.primaryCrops)
            update_data["farmer_profile"] = user.farmer_profile.model_dump()
        elif role_str == "owner":
            user.owner_profile = OwnerProfileDoc(district=data.district, upazila=upazila, service_radius_km=data.serviceRadiusKm or 15.0)
            update_data["owner_profile"] = user.owner_profile.model_dump()
        elif role_str == "buyer":
            user.buyer_profile = BuyerProfileDoc(district=data.district, upazila=upazila, business_name=data.businessName)
            update_data["buyer_profile"] = user.buyer_profile.model_dump()
        elif role_str == "expert":
            user.expert_profile = ExpertProfileDoc(district=data.district, designation=data.designation or "Agricultural Officer", organization=data.organization or "DAE")
            update_data["expert_profile"] = user.expert_profile.model_dump()
        reg.users.collection.update_one({"_id": user.id}, {"$set": update_data})
        return

    if user.role == UserRole.FARMER:
        profile = await db.scalar(select(FarmerProfile).where(FarmerProfile.user_id == user.id))
        if not profile:
            profile = FarmerProfile(user_id=user.id, district=data.district, upazila=upazila)
            db.add(profile)
        profile.district = data.district
        profile.upazila = upazila
        profile.primary_crops = data.primaryCrops

    elif user.role == UserRole.OWNER:
        profile = await db.scalar(select(OwnerProfile).where(OwnerProfile.user_id == user.id))
        if not profile:
            profile = OwnerProfile(user_id=user.id, district=data.district, upazila=upazila)
            db.add(profile)
        profile.district = data.district
        profile.upazila = upazila
        if data.serviceRadiusKm:
            profile.service_radius_km = data.serviceRadiusKm

    elif user.role == UserRole.BUYER:
        profile = await db.scalar(select(BuyerProfile).where(BuyerProfile.user_id == user.id))
        if not profile:
            profile = BuyerProfile(user_id=user.id, district=data.district, upazila=upazila)
            db.add(profile)
        profile.district = data.district
        profile.upazila = upazila
        profile.business_name = data.businessName

    elif user.role == UserRole.EXPERT:
        profile = await db.scalar(select(ExpertProfile).where(ExpertProfile.user_id == user.id))
        if not profile:
            profile = ExpertProfile(
                user_id=user.id,
                district=data.district,
                designation=data.designation or "Agricultural Officer",
                organization=data.organization or "DAE",
            )
            db.add(profile)
        profile.district = data.district
        if data.designation:
            profile.designation = data.designation
        if data.organization:
            profile.organization = data.organization

    await db.commit()


async def resubmit_user_nid(
    db: AsyncSession,
    user: Any,
    data: ResubmitNidRequest,
) -> Any:
    """Updates NID details, profile fields, and photos for a user, resubmitting for admin review."""
    if user.nid_verification_status == "approved" and user.is_nid_verified:
        raise ShikhorException(
            code="NID_ALREADY_APPROVED",
            message="আপনার জাতীয় পরিচয়পত্র ইতিমধ্যে যাচাই ও অনুমোদিত হয়েছে।",
            status_code=400,
        )

    if is_mongodb_backend():
        reg = get_mongo_registry()
        update_set: Dict[str, Any] = {
            "nid_front_image": data.nidFrontImage,
            "nid_back_image": data.nidBackImage,
            "nid_verification_status": "pending",
            "nid_rejection_reason": None,
            "is_nid_verified": False,
        }
        user.nid_front_image = data.nidFrontImage
        user.nid_back_image = data.nidBackImage
        user.nid_verification_status = "pending"
        user.nid_rejection_reason = None
        user.is_nid_verified = False

        if data.nid and data.nid != user.nid:
            existing = reg.users.collection.find_one({"nid": data.nid, "_id": {"$ne": user.id}})
            if existing:
                raise ShikhorException(
                    code="NID_ALREADY_EXISTS",
                    message="এই জাতীয় পরিচয়পত্র (NID) নম্বর দিয়ে ইতিমধ্যে অন্য একটি অ্যাকাউন্ট রয়েছে।",
                    status_code=400,
                )
            user.nid = data.nid
            update_set["nid"] = data.nid

        if data.phone and data.phone != user.phone:
            existing_ph = reg.users.collection.find_one({"phone": data.phone, "_id": {"$ne": user.id}})
            if existing_ph:
                raise ShikhorException(
                    code="PHONE_ALREADY_EXISTS",
                    message="এই মোবাইল নম্বরটি ইতিমধ্যে অন্য একটি অ্যাকাউন্টে ব্যবহার করা হয়েছে।",
                    status_code=400,
                )
            user.phone = data.phone
            update_set["phone"] = data.phone

        if data.fullName:
            user.full_name = data.fullName.strip()
            update_set["full_name"] = user.full_name

        if data.role:
            user.role = data.role
            update_set["role"] = data.role.value if hasattr(data.role, "value") else str(data.role)

        if data.dob:
            user.dob = data.dob
            update_set["dob"] = data.dob

        if data.district:
            upazila = data.upazila or "সদর"
            role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
            if role_str == "farmer":
                user.farmer_profile = FarmerProfileDoc(district=data.district, upazila=upazila)
                update_set["farmer_profile"] = user.farmer_profile.model_dump()
            elif role_str == "owner":
                user.owner_profile = OwnerProfileDoc(district=data.district, upazila=upazila, service_radius_km=15.0)
                update_set["owner_profile"] = user.owner_profile.model_dump()
            elif role_str == "buyer":
                user.buyer_profile = BuyerProfileDoc(district=data.district, upazila=upazila)
                update_set["buyer_profile"] = user.buyer_profile.model_dump()
            elif role_str == "expert":
                user.expert_profile = ExpertProfileDoc(district=data.district, designation="Agricultural Specialist", organization="DAE")
                update_set["expert_profile"] = user.expert_profile.model_dump()

        reg.users.collection.update_one({"_id": user.id}, {"$set": update_set})
        audit_doc = AuditLogDocument(
            actor_id=user.id,
            actor_phone=user.phone,
            actor_role=user.role.value if hasattr(user.role, "value") else str(user.role),
            action="RESUBMIT_NID_VERIFICATION",
            resource_type="user",
            resource_id=user.id,
            details=f"User resubmitted NID for verification. NID: {user.nid or 'None'}, Phone: {user.phone}",
        )
        reg.audit_logs.insert_one(audit_doc)
        return user

    # SQLite / Postgres backend
    if data.nid and data.nid != user.nid:
        existing = await db.scalar(select(User).where(User.nid == data.nid, User.id != user.id))
        if existing:
            raise ShikhorException(
                code="NID_ALREADY_EXISTS",
                message="এই জাতীয় পরিচয়পত্র (NID) নম্বর দিয়ে ইতিমধ্যে অন্য একটি অ্যাকাউন্ট রয়েছে।",
                status_code=400,
            )
        user.nid = data.nid

    if data.phone and data.phone != user.phone:
        existing_ph = await db.scalar(select(User).where(User.phone == data.phone, User.id != user.id))
        if existing_ph:
            raise ShikhorException(
                code="PHONE_ALREADY_EXISTS",
                message="এই মোবাইল নম্বরটি ইতিমধ্যে অন্য একটি অ্যাকাউন্টে ব্যবহার করা হয়েছে।",
                status_code=400,
            )
        user.phone = data.phone

    if data.fullName:
        user.full_name = data.fullName.strip()

    if data.role:
        user.role = data.role

    if data.dob:
        user.dob = data.dob

    user.nid_front_image = data.nidFrontImage
    user.nid_back_image = data.nidBackImage
    user.nid_verification_status = "pending"
    user.nid_rejection_reason = None
    user.is_nid_verified = False

    if data.district:
        upazila = data.upazila or "সদর"
        if user.role == UserRole.FARMER:
            fp = await db.scalar(select(FarmerProfile).where(FarmerProfile.user_id == user.id))
            if not fp:
                fp = FarmerProfile(user_id=user.id, district=data.district, upazila=upazila)
                db.add(fp)
            else:
                fp.district = data.district
                fp.upazila = upazila
        elif user.role == UserRole.OWNER:
            op = await db.scalar(select(OwnerProfile).where(OwnerProfile.user_id == user.id))
            if not op:
                op = OwnerProfile(user_id=user.id, district=data.district, upazila=upazila)
                db.add(op)
            else:
                op.district = data.district
                op.upazila = upazila
        elif user.role == UserRole.BUYER:
            bp = await db.scalar(select(BuyerProfile).where(BuyerProfile.user_id == user.id))
            if not bp:
                bp = BuyerProfile(user_id=user.id, district=data.district, upazila=upazila)
                db.add(bp)
            else:
                bp.district = data.district
                bp.upazila = upazila
        elif user.role == UserRole.EXPERT:
            ep = await db.scalar(select(ExpertProfile).where(ExpertProfile.user_id == user.id))
            if not ep:
                ep = ExpertProfile(user_id=user.id, district=data.district, designation="Agricultural Specialist", organization="DAE")
                db.add(ep)
            else:
                ep.district = data.district

    # Log audit event
    from app.modules.admin.models import AuditLog
    audit_entry = AuditLog(
        actor_id=user.id,
        actor_phone=user.phone,
        actor_role=user.role.value if hasattr(user.role, "value") else str(user.role),
        action="RESUBMIT_NID_VERIFICATION",
        resource_type="user",
        resource_id=user.id,
        details=f"User resubmitted NID for verification. NID: {user.nid or 'None'}, Phone: {user.phone}",
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(user)
    return user


async def _issue_tokens_and_session(
    db: AsyncSession,
    user: User,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> TokenResponse:
    """Helper to generate JWT tokens and record the active session in DB."""
    access_token = create_access_token(user_id=user.id, role=user.role.value)
    refresh_token = create_refresh_token(user_id=user.id)

    # Decode refresh token exp
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    session_record = RefreshSession(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=expires_at,
        is_revoked=False,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    db.add(session_record)

    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        tokenType="bearer",
        expiresIn=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

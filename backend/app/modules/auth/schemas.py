"""Authentication and user profile Pydantic v2 schemas."""

import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.modules.users.models import UserRole

# Bangladeshi mobile regex: 013 to 019 followed by 8 digits
BD_PHONE_REGEX = re.compile(r"^(?:\+8801|8801|01)[3-9]\d{8}$")
# Bangladeshi National ID regex: 10 digits (Smart Card), 13 digits (Old NID), or 17 digits (Birth year prefixed)
BD_NID_REGEX = re.compile(r"^(\d{10}|\d{13}|\d{17})$")
EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def normalize_bd_phone(phone: str) -> str:
    """Normalizes Bangladeshi phone to canonical format (e.g., 017XXXXXXXX)."""
    cleaned = re.sub(r"[\s\-]", "", phone)
    if cleaned.startswith("+88"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("88"):
        cleaned = cleaned[2:]
    return cleaned


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    phone: str = Field(..., description="Bangladeshi mobile number")
    password: str = Field(..., min_length=10, description="Minimum 10 characters password")
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    role: UserRole = Field(default=UserRole.FARMER, description="Initial account role")
    email: Optional[str] = Field(None, pattern=EMAIL_REGEX, description="User email address")
    emailVerificationToken: Optional[str] = Field(None, alias="email_verification_token", description="Token proving email was verified via OTP")
    nid: Optional[str] = Field(None, description="Bangladeshi National ID (10, 13, or 17 digits)")
    dob: Optional[str] = Field(None, description="Date of birth")
    nidFrontImage: Optional[str] = Field(None, alias="nid_front_image", description="URL or relative path to front of NID")
    nidBackImage: Optional[str] = Field(None, alias="nid_back_image", description="URL or relative path to back of NID")
    district: Optional[str] = Field(None, description="District name in Bangla or English")
    upazila: Optional[str] = Field(None, description="Upazila name in Bangla or English")
    primaryCrops: Optional[str] = Field(None, alias="primary_crops", description="Primary crops for farmer")
    serviceRadiusKm: Optional[float] = Field(None, alias="service_radius_km", description="Service radius for owner")
    businessName: Optional[str] = Field(None, alias="business_name", description="Business name for buyer")
    designation: Optional[str] = Field(None, description="Designation for expert")
    organization: Optional[str] = Field(None, description="Organization for expert")

    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = normalize_bd_phone(v)
        if not BD_PHONE_REGEX.match(cleaned):
            raise ValueError("Invalid Bangladeshi mobile number format (e.g., 017XXXXXXXX)")
        return cleaned

    @field_validator("nid")
    @classmethod
    def validate_nid(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = re.sub(r"[\s\-]", "", v)
        if not BD_NID_REGEX.match(cleaned):
            raise ValueError("জাতীয় পরিচয়পত্র (NID) নম্বর ১০, ১৩ অথবা ১৭ সংখ্যার হতে হবে।")
        return cleaned


class ResubmitNidRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    nid: Optional[str] = Field(None, description="Bangladeshi National ID (10, 13, or 17 digits)")
    dob: Optional[str] = Field(None, description="Date of birth")
    nidFrontImage: str = Field(..., alias="nid_front_image", description="URL or relative path to front of NID")
    nidBackImage: str = Field(..., alias="nid_back_image", description="URL or relative path to back of NID")
    fullName: Optional[str] = Field(None, alias="full_name", max_length=150)
    phone: Optional[str] = Field(None, description="Mobile number")
    role: Optional[UserRole] = Field(None, description="Selected account role")
    district: Optional[str] = Field(None, max_length=100)
    upazila: Optional[str] = Field(None, max_length=100)

    @field_validator("nid")
    @classmethod
    def validate_nid(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = re.sub(r"[\s\-]", "", v)
        if not BD_NID_REGEX.match(cleaned):
            raise ValueError("জাতীয় পরিচয়পত্র (NID) নম্বর ১০, ১৩ অথবা ১৭ সংখ্যার হতে হবে।")
        return cleaned

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        return normalize_bd_phone(v)


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    phone: str = Field(..., description="Mobile number")
    password: str = Field(..., description="Account password")

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        return normalize_bd_phone(v)


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    expiresIn: int


class RefreshRequest(BaseModel):
    refreshToken: str


class FarmerProfileData(BaseModel):
    district: str = Field(..., min_length=2, max_length=100)
    upazila: str = Field(..., min_length=2, max_length=100)
    primaryCrops: Optional[str] = Field(None, max_length=255)


class OwnerProfileData(BaseModel):
    district: str = Field(..., min_length=2, max_length=100)
    upazila: str = Field(..., min_length=2, max_length=100)
    serviceRadiusKm: float = Field(default=15.0, ge=1.0, le=100.0)


class BuyerProfileData(BaseModel):
    district: str = Field(..., min_length=2, max_length=100)
    upazila: str = Field(..., min_length=2, max_length=100)
    businessName: Optional[str] = Field(None, max_length=150)


class ExpertProfileData(BaseModel):
    district: str = Field(..., min_length=2, max_length=100)
    designation: str = Field(..., min_length=2, max_length=100)
    organization: str = Field(..., min_length=2, max_length=150)


class RoleOnboardingRequest(BaseModel):
    district: str = Field(..., min_length=2, max_length=100)
    upazila: Optional[str] = Field(None, max_length=100)
    primaryCrops: Optional[str] = None
    serviceRadiusKm: Optional[float] = None
    businessName: Optional[str] = None
    designation: Optional[str] = None
    organization: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    phone: str
    email: Optional[str] = None
    nid: Optional[str] = None
    dob: Optional[str] = None
    nidFrontImage: Optional[str] = None
    nidBackImage: Optional[str] = None
    isNidVerified: bool = False
    nidVerificationStatus: str = "pending"
    nidRejectionReason: Optional[str] = None
    fullName: str
    role: str
    isActive: bool
    isVerified: bool
    isEmailVerified: bool = False
    hasProfile: bool = False


class FirebaseLoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    idToken: str = Field(..., description="Google Firebase ID Token")
    fullName: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name if registering")
    role: Optional[UserRole] = Field(default=UserRole.FARMER, description="Account role if registering")
    nid: Optional[str] = Field(None, description="Bangladeshi National ID")


class FirebaseLoginResponse(BaseModel):
    isNewUser: bool = False
    phone: Optional[str] = None
    tokens: Optional[TokenResponse] = None


class GoogleLoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    idToken: str = Field(..., description="Google ID Token from Firebase/Google Auth")
    role: Optional[UserRole] = Field(default=UserRole.FARMER, description="Account role if registering")
    phone: Optional[str] = Field(None, description="Optional phone number if onboarding")
    nid: Optional[str] = Field(None, description="Optional National ID")


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., pattern=EMAIL_REGEX, description="User's registered email address")


class VerifyEmailOTPRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., pattern=EMAIL_REGEX, description="User email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification OTP code")


class ResetPasswordWithOTPRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., pattern=EMAIL_REGEX, description="User email address")
    resetToken: str = Field(..., min_length=10, description="Single-use reset token from OTP verification")
    newPassword: str = Field(..., min_length=10, description="New password with minimum 10 characters")


class SignupSendEmailOTPRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., pattern=EMAIL_REGEX, description="Email address for signup")


class SignupVerifyEmailOTPRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., pattern=EMAIL_REGEX, description="User email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class SignupVerifyEmailOTPResponse(BaseModel):
    verified: bool
    email: str
    verificationToken: str
    message: str


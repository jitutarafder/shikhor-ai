"""Tests for NID registration, Google login, and Email OTP password reset."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_with_valid_nid(client: AsyncClient):
    """Verifies that registration with a valid 10-digit NID succeeds."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "01722334455",
            "password": "SecurePassword123!",
            "full_name": "আব্দুল কুদ্দুস",
            "nid": "1234567890",
            "role": "farmer",
        },
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert "accessToken" in data

    # Verify NID in /me
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['accessToken']}"},
    )
    assert me_res.status_code == 200
    user_me = me_res.json()
    assert user_me["nid"] == "1234567890"


@pytest.mark.asyncio
async def test_register_with_invalid_nid_rejected(client: AsyncClient):
    """Verifies that registration with an invalid-length NID fails."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "01722334456",
            "password": "SecurePassword123!",
            "full_name": "আব্দুল কুদ্দুস",
            "nid": "12345",  # Invalid length
            "role": "farmer",
        },
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_google_login_flow(client: AsyncClient):
    """Verifies Google sign-in creates an account and logs in."""
    res = await client.post(
        "/api/v1/auth/google-login",
        json={
            "idToken": "mock-google-token:kuddus@gmail.com",
            "role": "farmer",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "accessToken" in data

    # Subsequent login with same Google token succeeds
    res2 = await client.post(
        "/api/v1/auth/google-login",
        json={"idToken": "mock-google-token:kuddus@gmail.com"},
    )
    assert res2.status_code == 200


@pytest.mark.asyncio
async def test_email_otp_password_reset_flow(client: AsyncClient, test_db: AsyncSession):
    """Verifies complete Email OTP password reset lifecycle."""
    email = "farmer.reset@shikhor.ai"
    phone = "01788776655"
    old_pwd = "OldPassword123!"
    new_pwd = "NewPassword123!Secure"

    # 1. Register user
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": phone,
            "email": email,
            "password": old_pwd,
            "full_name": "করিম মিয়া",
            "role": "farmer",
        },
    )
    assert reg.status_code == 201

    # 2. Request OTP
    req_res = await client.post(
        "/api/v1/auth/forgot-password/request",
        json={"email": email},
    )
    assert req_res.status_code == 200
    assert "message" in req_res.json()

    from sqlalchemy import select
    from app.modules.auth.models import PasswordResetOTP
    from app.core.security import hash_token

    # Test invalid OTP rejected
    verify_bad = await client.post(
        "/api/v1/auth/forgot-password/verify",
        json={"email": email, "otp": "000000"},
    )
    assert verify_bad.status_code == 400

    # Retrieve and set known OTP in test DB
    known_otp = "654321"
    record = await test_db.scalar(
        select(PasswordResetOTP).where(PasswordResetOTP.email == email, PasswordResetOTP.is_used == False)
    )
    assert record is not None
    record.otp_hash = hash_token(known_otp)
    await test_db.commit()

    # 3. Verify valid OTP
    verify_ok = await client.post(
        "/api/v1/auth/forgot-password/verify",
        json={"email": email, "otp": known_otp},
    )
    assert verify_ok.status_code == 200
    reset_token = verify_ok.json()["resetToken"]

    # 4. Reset password
    reset_res = await client.post(
        "/api/v1/auth/forgot-password/reset",
        json={
            "email": email,
            "resetToken": reset_token,
            "newPassword": new_pwd,
        },
    )
    assert reset_res.status_code == 200

    # 5. Old password should fail
    login_old = await client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": old_pwd},
    )
    assert login_old.status_code == 401

    # 6. New password should succeed
    login_new = await client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": new_pwd},
    )
    assert login_new.status_code == 200
    assert "accessToken" in login_new.json()


@pytest.mark.asyncio
async def test_signup_email_otp_flow(client: AsyncClient, test_db: AsyncSession):
    """Verifies signup email OTP request, verification, and registration enforcement."""
    from sqlalchemy import select
    from app.modules.auth.models import SignupEmailOTP
    from app.core.security import hash_token

    email = "farmer.verified@gmail.com"
    phone = "01788776655"

    # 1. Request signup email OTP
    req_res = await client.post(
        "/api/v1/auth/signup/send-email-otp",
        json={"email": email},
    )
    assert req_res.status_code == 200
    assert "message" in req_res.json()

    # Set known OTP in test DB
    known_otp = "123456"
    otp_record = await test_db.scalar(
        select(SignupEmailOTP).where(SignupEmailOTP.email == email)
    )
    assert otp_record is not None
    otp_record.otp_hash = hash_token(known_otp)
    await test_db.commit()

    # 2. Invalid OTP is rejected
    bad_res = await client.post(
        "/api/v1/auth/signup/verify-email-otp",
        json={"email": email, "otp": "999999"},
    )
    assert bad_res.status_code == 400
    assert bad_res.json()["error"]["code"] == "INVALID_OTP"

    # 3. Valid OTP succeeds and returns verificationToken
    ok_res = await client.post(
        "/api/v1/auth/signup/verify-email-otp",
        json={"email": email, "otp": known_otp},
    )
    assert ok_res.status_code == 200
    verification_token = ok_res.json()["verificationToken"]
    assert verification_token is not None

    # 4. Registration with fake token is rejected
    fake_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": phone,
            "password": "SecurePassword123!",
            "full_name": "যাচাইকৃত কৃষক",
            "email": email,
            "email_verification_token": "invalid_fake_token_12345",
            "role": "farmer",
        },
    )
    assert fake_reg.status_code == 400
    assert fake_reg.json()["error"]["code"] == "INVALID_VERIFICATION_TOKEN"

    # 5. Registration with real token succeeds and marks isEmailVerified=True
    valid_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": phone,
            "password": "SecurePassword123!",
            "full_name": "যাচাইকৃত কৃষক",
            "email": email,
            "email_verification_token": verification_token,
            "role": "farmer",
        },
    )
    assert valid_reg.status_code == 201
    user_token = valid_reg.json()["accessToken"]

    # Verify profile reflects isEmailVerified == True
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["isEmailVerified"] is True
    assert me_data["email"] == email

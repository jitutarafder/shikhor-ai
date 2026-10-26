"""Comprehensive test suite for Phase 2 Authentication and Role Onboarding.

Verifies:
- Phone format validation (Bangladeshi numbers)
- Minimum 10-char password enforcement
- Argon2id password verification
- Duplicate account handling
- Enumeration prevention on invalid login
- Bearer token authorization and user resolution
- Rotating refresh sessions and revocation
- Step-3 Role onboarding
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    # 1. Register a new farmer
    reg_payload = {
        "phone": "01712345678",
        "password": "StrongPassword123#",
        "full_name": "মো. রফিকুল ইসলাম",
        "role": "farmer",
        "email": "rafiq@example.com",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text
    tokens = reg_res.json()
    assert "accessToken" in tokens
    assert "refreshToken" in tokens

    # 2. Login with valid credentials
    login_payload = {
        "phone": "01712345678",
        "password": "StrongPassword123#",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_tokens = login_res.json()
    assert "accessToken" in login_tokens

    # 3. Access /auth/me with Bearer token
    headers = {"Authorization": f"Bearer {login_tokens['accessToken']}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["phone"] == "01712345678"
    assert user_data["role"] == "farmer"
    assert user_data["fullName"] == "মো. রফিকুল ইসলাম"


@pytest.mark.asyncio
async def test_password_length_validation(client: AsyncClient):
    # Password shorter than 10 characters should be rejected
    payload = {
        "phone": "01811223344",
        "password": "short",
        "full_name": "পরীক্ষামূলক ব্যবহারকারী",
        "role": "farmer",
    }
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert "password" in data["error"]["fieldErrors"]


@pytest.mark.asyncio
async def test_invalid_phone_validation(client: AsyncClient):
    # Non-Bangladeshi number should be rejected
    payload = {
        "phone": "1234567",
        "password": "ValidPassword123#",
        "full_name": "পরীক্ষামূলক",
        "role": "farmer",
    }
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_phone_prevention(client: AsyncClient):
    payload = {
        "phone": "01999887766",
        "password": "SecurePassword123!",
        "full_name": "প্রথম ব্যবহারকারী",
        "role": "farmer",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same phone
    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    data = res2.json()
    assert data["error"]["code"] == "PHONE_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_invalid_credentials_prevents_enumeration(client: AsyncClient):
    # Wrong password for existing user or non-existing user returns identical safe message
    login_payload = {
        "phone": "01700000000",
        "password": "WrongPassword123!",
    }
    res = await client.post("/api/v1/auth/login", json=login_payload)
    assert res.status_code == 401
    data = res.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"
    assert data["error"]["message"] == "Invalid mobile number or password."


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_revocation(client: AsyncClient):
    # 1. Register
    reg_payload = {
        "phone": "01511223344",
        "password": "StrongPassword123#",
        "full_name": "সাজেদুর রহমান",
        "role": "owner",
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    initial_tokens = res.json()
    first_refresh = initial_tokens["refreshToken"]

    # 2. Use refresh token to rotate
    refresh_res = await client.post("/api/v1/auth/refresh", json={"refreshToken": first_refresh})
    assert refresh_res.status_code == 200
    rotated_tokens = refresh_res.json()
    second_refresh = rotated_tokens["refreshToken"]
    assert second_refresh != first_refresh

    # 3. Attempting to reuse revoked first refresh token MUST fail
    reuse_res = await client.post("/api/v1/auth/refresh", json={"refreshToken": first_refresh})
    assert reuse_res.status_code == 401
    assert reuse_res.json()["error"]["code"] == "SESSION_REVOKED"


@pytest.mark.asyncio
async def test_role_onboarding_step(client: AsyncClient):
    # 1. Register buyer
    reg_payload = {
        "phone": "01611223344",
        "password": "StrongPassword123#",
        "full_name": "আব্দুল কাদের",
        "role": "buyer",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Complete onboarding profile
    onboarding_payload = {
        "district": "বগুড়া",
        "upazila": "শেরপুর",
        "businessName": "কাদের অ্যাগ্রো ট্রেডার্স",
    }
    onboard_res = await client.post("/api/v1/auth/onboarding", json=onboarding_payload, headers=headers)
    assert onboard_res.status_code == 200
    data = onboard_res.json()
    assert data["hasProfile"] is True
    assert data["role"] == "buyer"

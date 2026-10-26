"""Unit and integration tests for Firebase Phone Authentication."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_firebase_login_new_user_prompts_profile(client: AsyncClient):
    """Verifies that a verified phone without a name signals isNewUser=True."""
    res = await client.post(
        "/api/v1/auth/firebase-login",
        json={"idToken": "mock-firebase-token:+8801799887766"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["isNewUser"] is True
    assert data["phone"] == "01799887766"
    assert data["tokens"] is None


@pytest.mark.asyncio
async def test_firebase_register_and_subsequent_login(client: AsyncClient):
    """Verifies registering a new user with full name and logging in subsequently."""
    phone = "+8801711224455"
    token_str = f"mock-firebase-token:{phone}"

    # 1. Register with name and role
    reg_res = await client.post(
        "/api/v1/auth/firebase-login",
        json={
            "idToken": token_str,
            "fullName": "মোবারক হোসেন",
            "role": "farmer",
        },
    )
    assert reg_res.status_code == 200, reg_res.text
    reg_data = reg_res.json()
    assert reg_data["isNewUser"] is False
    assert reg_data["tokens"] is not None
    assert "accessToken" in reg_data["tokens"]

    access_token = reg_data["tokens"]["accessToken"]

    # Verify user profile via /me
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    user_me = me_res.json()
    assert user_me["fullName"] == "মোবারক হোসেন"
    assert user_me["phone"] == "01711224455"
    assert user_me["role"] == "farmer"
    assert user_me["isVerified"] is True  # Verified by Firebase

    # 2. Subsequent login with just idToken (without name)
    login_res = await client.post(
        "/api/v1/auth/firebase-login",
        json={"idToken": token_str},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["isNewUser"] is False
    assert login_data["tokens"] is not None
    assert "accessToken" in login_data["tokens"]


@pytest.mark.asyncio
async def test_firebase_invalid_token_rejected(client: AsyncClient):
    """Verifies that malformed or unauthorized tokens return 401."""
    res = await client.post(
        "/api/v1/auth/firebase-login",
        json={"idToken": "completely-invalid-garbage-token"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_FIREBASE_TOKEN"

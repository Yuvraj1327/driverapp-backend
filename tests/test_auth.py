"""
Tests for authentication endpoints: login, refresh, /me.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_login_success(client: AsyncClient, admin_user):
    response = await client.post(
        "/api/v1/auth/login", json={"email": "admin@test.com", "password": "Password@123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_login_invalid_password(client: AsyncClient, admin_user):
    response = await client.post(
        "/api/v1/auth/login", json={"email": "admin@test.com", "password": "wrong-password"}
    )
    assert response.status_code == 422
    assert "Invalid email or password" in response.json()["detail"]


async def test_login_unknown_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@test.com", "password": "whatever123"}
    )
    assert response.status_code == 422


async def test_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user(client: AsyncClient, admin_token: str):
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "admin@test.com"
    assert body["role_name"] == "admin"


async def test_refresh_token_flow(client: AsyncClient, admin_user):
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": "admin@test.com", "password": "Password@123"}
    )
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()

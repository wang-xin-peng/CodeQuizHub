"""Unit tests for user information endpoints."""
import pytest
from httpx import AsyncClient


class TestGetMe:
    """Tests for GET /api/users/me."""

    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient, test_student):
        response = await client.get("/api/users/me", headers=test_student["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["username"] == "teststudent"
        assert data["data"]["email"] == "student@test.com"
        assert data["data"]["role"] == "student"

    @pytest.mark.asyncio
    async def test_get_me_no_token(self, client: AsyncClient):
        response = await client.get("/api/users/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_expired_token(self, client: AsyncClient):
        import jwt
        from datetime import datetime, timedelta, timezone
        from app.config import get_settings

        settings = get_settings()
        expired_payload = {
            "sub": "some-user-id",
            "role": "student",
            "iat": datetime.now(timezone.utc) - timedelta(hours=48),
            "exp": datetime.now(timezone.utc) - timedelta(hours=24),
        }
        expired_token = jwt.encode(
            expired_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "AUTH_TOKEN_EXPIRED"


class TestUpdateProfile:
    """Tests for PUT /api/users/me."""

    @pytest.mark.asyncio
    async def test_update_nickname(self, client: AsyncClient, test_student):
        response = await client.put(
            "/api/users/me",
            headers=test_student["headers"],
            json={"nickname": "Cool Student"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["nickname"] == "Cool Student"

    @pytest.mark.asyncio
    async def test_update_avatar(self, client: AsyncClient, test_student):
        response = await client.put(
            "/api/users/me",
            headers=test_student["headers"],
            json={"avatar_url": "https://example.com/avatar.png"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["avatar_url"] == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_update_both_fields(self, client: AsyncClient, test_student):
        response = await client.put(
            "/api/users/me",
            headers=test_student["headers"],
            json={"nickname": "New Name", "avatar_url": "https://example.com/new.png"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["nickname"] == "New Name"
        assert data["data"]["avatar_url"] == "https://example.com/new.png"

    @pytest.mark.asyncio
    async def test_update_no_auth(self, client: AsyncClient):
        response = await client.put("/api/users/me", json={"nickname": "NoAuth"})
        assert response.status_code == 401


class TestChangePassword:
    """Tests for PUT /api/users/me/password."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient, test_student):
        response = await client.put(
            "/api/users/me/password",
            headers=test_student["headers"],
            json={"old_password": "Test1234", "new_password": "NewPass123"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "密码修改成功"

    @pytest.mark.asyncio
    async def test_change_password_wrong_old(self, client: AsyncClient, test_student):
        response = await client.put(
            "/api/users/me/password",
            headers=test_student["headers"],
            json={"old_password": "WrongOld1", "new_password": "NewPass123"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_too_short(self, client: AsyncClient, test_student):
        response = await client.put(
            "/api/users/me/password",
            headers=test_student["headers"],
            json={"old_password": "Test1234", "new_password": "weak"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_change_password_no_auth(self, client: AsyncClient):
        response = await client.put(
            "/api/users/me/password",
            json={"old_password": "Test1234", "new_password": "NewPass123"},
        )
        assert response.status_code == 401

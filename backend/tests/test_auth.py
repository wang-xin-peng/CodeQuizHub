"""Unit tests for authentication endpoints (register + login)."""
import pytest
from httpx import AsyncClient


class TestRegister:
    """Tests for POST /api/auth/register."""

    @pytest.mark.asyncio
    async def test_register_student_success(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "username": "newstudent",
            "email": "newstudent@example.com",
            "password": "MyPass123",
            "role": "student",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["username"] == "newstudent"
        assert data["data"]["email"] == "newstudent@example.com"
        assert data["data"]["role"] == "student"
        assert data["data"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_register_teacher_success(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "username": "newteacher",
            "email": "newteacher@example.com",
            "password": "MyPass123",
            "role": "teacher",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        # First registration
        await client.post("/api/auth/register", json={
            "username": "dupuser",
            "email": "dup1@example.com",
            "password": "MyPass123",
            "role": "student",
        })
        # Duplicate username
        response = await client.post("/api/auth/register", json={
            "username": "dupuser",
            "email": "dup2@example.com",
            "password": "MyPass123",
            "role": "student",
        })
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "USER_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "user_a",
            "email": "same@example.com",
            "password": "MyPass123",
            "role": "student",
        })
        response = await client.post("/api/auth/register", json={
            "username": "user_b",
            "email": "same@example.com",
            "password": "MyPass123",
            "role": "student",
        })
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_weak_password_no_uppercase(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "username": "weakuser1",
            "email": "weak1@example.com",
            "password": "mypass123",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password_no_lowercase(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "username": "weakuser2",
            "email": "weak2@example.com",
            "password": "MYPASS123",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password_no_digit(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "username": "weakuser3",
            "email": "weak3@example.com",
            "password": "MyPassNoDigit",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_password_too_short(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "username": "shortpw",
            "email": "short@example.com",
            "password": "Ab1",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_username_format(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "username": "bad user!",
            "email": "bad@example.com",
            "password": "MyPass123",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "username": "bademail",
            "email": "not-an-email",
            "password": "MyPass123",
            "role": "student",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_role(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "username": "badrole",
            "email": "role@example.com",
            "password": "MyPass123",
            "role": "admin",
        })
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/auth/login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        # Register first
        await client.post("/api/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "MyPass123",
            "role": "student",
        })
        # Login
        response = await client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "MyPass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["expires_in"] > 0
        assert data["data"]["user"]["email"] == "login@example.com"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "wrongpw",
            "email": "wrongpw@example.com",
            "password": "MyPass123",
            "role": "student",
        })
        response = await client.post("/api/auth/login", json={
            "email": "wrongpw@example.com",
            "password": "WrongPass1",
        })
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "AUTH_INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: AsyncClient):
        response = await client.post("/api/auth/login", json={
            "email": "noexist@example.com",
            "password": "MyPass123",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_disabled_account(self, client: AsyncClient, db_session):
        from app.models.user import User
        from app.core.security import hash_password

        user = User(
            username="disableduser",
            email="disabled@example.com",
            password_hash=hash_password("MyPass123"),
            role="student",
            is_active=False,
        )
        db_session.add(user)
        await db_session.flush()

        response = await client.post("/api/auth/login", json={
            "email": "disabled@example.com",
            "password": "MyPass123",
        })
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "AUTH_ACCOUNT_DISABLED"

    @pytest.mark.asyncio
    async def test_login_returns_valid_jwt(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "jwtuser",
            "email": "jwt@example.com",
            "password": "MyPass123",
            "role": "student",
        })
        login_resp = await client.post("/api/auth/login", json={
            "email": "jwt@example.com",
            "password": "MyPass123",
        })
        token = login_resp.json()["data"]["access_token"]

        # Use token to access protected endpoint
        me_resp = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["data"]["email"] == "jwt@example.com"

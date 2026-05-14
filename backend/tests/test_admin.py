"""Unit tests for admin user management endpoints."""
import pytest
from httpx import AsyncClient


class TestAdminListUsers:
    """Tests for GET /api/users/admin/list."""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, client: AsyncClient, test_admin):
        response = await client.get(
            "/api/users/admin/list",
            headers=test_admin["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert data["data"]["page"] == 1

    @pytest.mark.asyncio
    async def test_list_users_pagination(self, client: AsyncClient, test_admin):
        response = await client.get(
            "/api/users/admin/list?page=1&page_size=5",
            headers=test_admin["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 5

    @pytest.mark.asyncio
    async def test_list_users_filter_by_role(self, client: AsyncClient, test_admin):
        response = await client.get(
            "/api/users/admin/list?role=admin",
            headers=test_admin["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        for user in data["data"]["items"]:
            assert user["role"] == "admin"

    @pytest.mark.asyncio
    async def test_list_users_as_teacher_forbidden(self, client: AsyncClient, test_teacher):
        response = await client.get(
            "/api/users/admin/list",
            headers=test_teacher["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_users_as_student_forbidden(self, client: AsyncClient, test_student):
        response = await client.get(
            "/api/users/admin/list",
            headers=test_student["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_users_no_auth(self, client: AsyncClient):
        response = await client.get("/api/users/admin/list")
        assert response.status_code == 401


class TestAdminUpdateUserStatus:
    """Tests for PUT /api/users/admin/{user_id}/status."""

    @pytest.mark.asyncio
    async def test_disable_user(self, client: AsyncClient, test_admin, test_student):
        user_id = str(test_student["user"].id)
        response = await client.put(
            f"/api/users/admin/{user_id}/status?is_active=false",
            headers=test_admin["headers"],
        )
        assert response.status_code == 200
        assert response.json()["message"] == "操作成功"

    @pytest.mark.asyncio
    async def test_enable_user(self, client: AsyncClient, test_admin, test_student):
        user_id = str(test_student["user"].id)
        response = await client.put(
            f"/api/users/admin/{user_id}/status?is_active=true",
            headers=test_admin["headers"],
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self, client: AsyncClient, test_admin):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.put(
            f"/api/users/admin/{fake_id}/status?is_active=false",
            headers=test_admin["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_status_as_teacher(self, client: AsyncClient, test_teacher, test_student):
        user_id = str(test_student["user"].id)
        response = await client.put(
            f"/api/users/admin/{user_id}/status?is_active=false",
            headers=test_teacher["headers"],
        )
        assert response.status_code == 403


class TestAdminUpdateUserRole:
    """Tests for PUT /api/users/admin/{user_id}/role."""

    @pytest.mark.asyncio
    async def test_change_role_to_teacher(self, client: AsyncClient, test_admin, test_student):
        user_id = str(test_student["user"].id)
        response = await client.put(
            f"/api/users/admin/{user_id}/role?role=teacher",
            headers=test_admin["headers"],
        )
        assert response.status_code == 200
        assert response.json()["message"] == "角色变更成功"

    @pytest.mark.asyncio
    async def test_change_role_invalid(self, client: AsyncClient, test_admin, test_student):
        user_id = str(test_student["user"].id)
        response = await client.put(
            f"/api/users/admin/{user_id}/role?role=superuser",
            headers=test_admin["headers"],
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_change_role_nonexistent_user(self, client: AsyncClient, test_admin):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.put(
            f"/api/users/admin/{fake_id}/role?role=teacher",
            headers=test_admin["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_change_role_as_student(self, client: AsyncClient, test_student):
        response = await client.put(
            f"/api/users/admin/{str(test_student['user'].id)}/role?role=admin",
            headers=test_student["headers"],
        )
        assert response.status_code == 403

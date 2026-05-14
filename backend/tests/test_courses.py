"""Unit tests for course management endpoints."""
import pytest
from httpx import AsyncClient


class TestCreateCourse:
    """Tests for POST /api/courses."""

    @pytest.mark.asyncio
    async def test_create_course_as_teacher(self, client: AsyncClient, test_teacher):
        response = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "Python 编程入门",
            "description": "学习 Python 基础",
            "languages": ["python"],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["name"] == "Python 编程入门"
        assert data["data"]["languages"] == ["python"]
        assert len(data["data"]["invite_code"]) == 8
        assert data["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_course_multiple_languages(self, client: AsyncClient, test_teacher):
        response = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "数据结构与算法",
            "languages": ["python", "java", "c"],
        })
        assert response.status_code == 201
        assert set(response.json()["data"]["languages"]) == {"python", "java", "c"}

    @pytest.mark.asyncio
    async def test_create_course_as_student_forbidden(self, client: AsyncClient, test_student):
        response = await client.post("/api/courses", headers=test_student["headers"], json={
            "name": "Test",
            "languages": ["python"],
        })
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_course_missing_name(self, client: AsyncClient, test_teacher):
        response = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "languages": ["python"],
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_course_empty_languages(self, client: AsyncClient, test_teacher):
        response = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "Test",
            "languages": [],
        })
        assert response.status_code == 422


class TestListCourses:
    """Tests for GET /api/courses."""

    @pytest.mark.asyncio
    async def test_list_courses_teacher(self, client: AsyncClient, test_teacher):
        # Create a course first
        await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "课程A",
            "languages": ["python"],
        })
        response = await client.get("/api/courses", headers=test_teacher["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 1
        assert len(data["data"]["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_courses_student_empty(self, client: AsyncClient, test_student):
        response = await client.get("/api/courses", headers=test_student["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0


class TestGetCourse:
    """Tests for GET /api/courses/:id."""

    @pytest.mark.asyncio
    async def test_get_course_success(self, client: AsyncClient, test_teacher):
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "获取详情测试",
            "languages": ["java"],
        })
        course_id = create_resp.json()["data"]["id"]

        response = await client.get(f"/api/courses/{course_id}", headers=test_teacher["headers"])
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "获取详情测试"

    @pytest.mark.asyncio
    async def test_get_course_not_found(self, client: AsyncClient, test_teacher):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/courses/{fake_id}", headers=test_teacher["headers"])
        assert response.status_code == 404


class TestUpdateCourse:
    """Tests for PUT /api/courses/:id."""

    @pytest.mark.asyncio
    async def test_update_course_name(self, client: AsyncClient, test_teacher):
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "旧名称",
            "languages": ["python"],
        })
        course_id = create_resp.json()["data"]["id"]

        response = await client.put(
            f"/api/courses/{course_id}",
            headers=test_teacher["headers"],
            json={"name": "新名称"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "新名称"

    @pytest.mark.asyncio
    async def test_update_course_archive(self, client: AsyncClient, test_teacher):
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "归档测试",
            "languages": ["python"],
        })
        course_id = create_resp.json()["data"]["id"]

        response = await client.put(
            f"/api/courses/{course_id}",
            headers=test_teacher["headers"],
            json={"status": "archived"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "archived"

    @pytest.mark.asyncio
    async def test_update_course_invalid_status(self, client: AsyncClient, test_teacher):
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "状态测试",
            "languages": ["python"],
        })
        course_id = create_resp.json()["data"]["id"]

        response = await client.put(
            f"/api/courses/{course_id}",
            headers=test_teacher["headers"],
            json={"status": "invalid"},
        )
        assert response.status_code == 400


class TestDeleteCourse:
    """Tests for DELETE /api/courses/:id (archive)."""

    @pytest.mark.asyncio
    async def test_delete_course(self, client: AsyncClient, test_teacher):
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "删除测试",
            "languages": ["python"],
        })
        course_id = create_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/courses/{course_id}",
            headers=test_teacher["headers"],
        )
        assert response.status_code == 200
        assert response.json()["message"] == "课程已归档"


class TestJoinCourse:
    """Tests for POST /api/courses/join."""

    @pytest.mark.asyncio
    async def test_join_course_success(self, client: AsyncClient, test_teacher, test_student):
        # Teacher creates course
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "加入测试",
            "languages": ["python"],
        })
        invite_code = create_resp.json()["data"]["invite_code"]

        # Student joins
        response = await client.post(
            "/api/courses/join",
            headers=test_student["headers"],
            json={"invite_code": invite_code},
        )
        assert response.status_code == 200
        assert response.json()["data"]["course_name"] == "加入测试"

    @pytest.mark.asyncio
    async def test_join_course_invalid_code(self, client: AsyncClient, test_student):
        response = await client.post(
            "/api/courses/join",
            headers=test_student["headers"],
            json={"invite_code": "INVALID1"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_join_course_already_joined(self, client: AsyncClient, test_teacher, test_student):
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "重复加入",
            "languages": ["python"],
        })
        invite_code = create_resp.json()["data"]["invite_code"]

        # Join first time
        await client.post("/api/courses/join", headers=test_student["headers"], json={"invite_code": invite_code})
        # Join second time
        response = await client.post("/api/courses/join", headers=test_student["headers"], json={"invite_code": invite_code})
        assert response.status_code == 400
        assert response.json()["code"] == "COURSE_ALREADY_JOINED"


class TestLeaveCourse:
    """Tests for DELETE /api/courses/:id/leave."""

    @pytest.mark.asyncio
    async def test_leave_course_success(self, client: AsyncClient, test_teacher, test_student):
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "退出测试",
            "languages": ["python"],
        })
        course_id = create_resp.json()["data"]["id"]
        invite_code = create_resp.json()["data"]["invite_code"]

        # Join then leave
        await client.post("/api/courses/join", headers=test_student["headers"], json={"invite_code": invite_code})
        response = await client.delete(f"/api/courses/{course_id}/leave", headers=test_student["headers"])
        assert response.status_code == 200
        assert response.json()["message"] == "已退出课程"

    @pytest.mark.asyncio
    async def test_leave_course_not_member(self, client: AsyncClient, test_teacher, test_student):
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "未加入退出",
            "languages": ["python"],
        })
        course_id = create_resp.json()["data"]["id"]

        response = await client.delete(f"/api/courses/{course_id}/leave", headers=test_student["headers"])
        assert response.status_code == 404


class TestCourseStudents:
    """Tests for course student management."""

    @pytest.mark.asyncio
    async def test_list_students(self, client: AsyncClient, test_teacher, test_student):
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "学生列表",
            "languages": ["python"],
        })
        course_id = create_resp.json()["data"]["id"]
        invite_code = create_resp.json()["data"]["invite_code"]

        # Student joins
        await client.post("/api/courses/join", headers=test_student["headers"], json={"invite_code": invite_code})

        response = await client.get(f"/api/courses/{course_id}/students", headers=test_teacher["headers"])
        assert response.status_code == 200
        assert response.json()["data"]["total"] == 1
        assert response.json()["data"]["items"][0]["username"] == "teststudent"

    @pytest.mark.asyncio
    async def test_remove_student(self, client: AsyncClient, test_teacher, test_student):
        create_resp = await client.post("/api/courses", headers=test_teacher["headers"], json={
            "name": "移除学生",
            "languages": ["python"],
        })
        course_id = create_resp.json()["data"]["id"]
        invite_code = create_resp.json()["data"]["invite_code"]

        await client.post("/api/courses/join", headers=test_student["headers"], json={"invite_code": invite_code})

        student_id = str(test_student["user"].id)
        response = await client.delete(
            f"/api/courses/{course_id}/students/{student_id}",
            headers=test_teacher["headers"],
        )
        assert response.status_code == 200
        assert response.json()["message"] == "已移除学生"

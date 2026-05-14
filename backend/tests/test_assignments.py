"""Tests for assignment management endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.problem import Problem


# Helper: create a course owned by teacher
async def create_test_course(client: AsyncClient, teacher_headers, name="测试课程"):
    resp = await client.post(
        "/api/courses",
        json={"name": name, "languages": ["python"]},
        headers=teacher_headers,
    )
    assert resp.status_code == 201
    return resp.json()["data"]


# Helper: create a problem owned by teacher
async def create_test_problem(client: AsyncClient, teacher_headers, title="测试题目"):
    resp = await client.post(
        "/api/problems",
        json={
            "title": title,
            "description": "测试描述",
            "difficulty": "easy",
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["test"],
            "compare_mode": "exact",
            "signatures": [
                {
                    "language": "python",
                    "function_name": "solve",
                    "parameters": [{"name": "x", "type": "int", "description": "输入"}],
                    "return_type": "int",
                    "code_template": "def solve(x):\n    pass",
                }
            ],
            "test_cases": [
                {
                    "input_params": {"x": 1},
                    "expected_output": 2,
                    "is_public": True,
                    "description": "test",
                }
            ],
        },
        headers=teacher_headers,
    )
    assert resp.status_code == 201
    return resp.json()["data"]


class TestCreateAssignment:
    @pytest.mark.asyncio
    async def test_create_assignment_success(self, client: AsyncClient, test_teacher):
        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        payload = {
            "course_id": course["id"],
            "title": "第一次作业",
            "description": "本次作业包含一道题目",
            "start_time": "2026-06-01T00:00:00",
            "end_time": "2026-06-30T23:59:59",
            "problem_ids": [problem["id"]],
            "score_weights": [100],
        }
        resp = await client.post("/api/assignments", json=payload, headers=test_teacher["headers"])
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == "第一次作业"
        assert data["status"] == "draft"
        assert data["course_id"] == course["id"]

    @pytest.mark.asyncio
    async def test_create_assignment_no_auth(self, client: AsyncClient, test_teacher):
        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        payload = {
            "course_id": course["id"],
            "title": "测试",
            "start_time": "2026-06-01T00:00:00",
            "end_time": "2026-06-30T23:59:59",
            "problem_ids": [problem["id"]],
        }
        resp = await client.post("/api/assignments", json=payload)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_create_assignment_student_forbidden(self, client: AsyncClient, test_teacher, test_student):
        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        payload = {
            "course_id": course["id"],
            "title": "测试",
            "start_time": "2026-06-01T00:00:00",
            "end_time": "2026-06-30T23:59:59",
            "problem_ids": [problem["id"]],
        }
        resp = await client.post("/api/assignments", json=payload, headers=test_student["headers"])
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_create_assignment_not_course_owner(self, client: AsyncClient, test_teacher, db_session):
        """Another teacher cannot create assignment in someone else's course."""
        from app.core.security import create_access_token, hash_password
        from app.models.user import User

        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        # Create another teacher
        other = User(
            username="other_asgn",
            email="other_asgn@test.com",
            password_hash=hash_password("Test1234"),
            role="teacher",
        )
        db_session.add(other)
        await db_session.flush()
        await db_session.refresh(other)
        other_headers = {
            "Authorization": f"Bearer {create_access_token(str(other.id), other.role)}"
        }

        payload = {
            "course_id": course["id"],
            "title": "不该存在",
            "start_time": "2026-06-01T00:00:00",
            "end_time": "2026-06-30T23:59:59",
            "problem_ids": [problem["id"]],
        }
        resp = await client.post("/api/assignments", json=payload, headers=other_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_assignment_invalid_time(self, client: AsyncClient, test_teacher):
        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        payload = {
            "course_id": course["id"],
            "title": "时间错误",
            "start_time": "2026-07-01T00:00:00",
            "end_time": "2026-06-01T00:00:00",  # end before start
            "problem_ids": [problem["id"]],
        }
        resp = await client.post("/api/assignments", json=payload, headers=test_teacher["headers"])
        assert resp.status_code == 400


class TestGetAssignment:
    @pytest.mark.asyncio
    async def test_get_assignment_success(self, client: AsyncClient, test_teacher):
        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        create_resp = await client.post(
            "/api/assignments",
            json={
                "course_id": course["id"],
                "title": "测试作业",
                "start_time": "2026-06-01T00:00:00",
                "end_time": "2026-06-30T23:59:59",
                "problem_ids": [problem["id"]],
            },
            headers=test_teacher["headers"],
        )
        assignment_id = create_resp.json()["data"]["id"]

        resp = await client.get(f"/api/assignments/{assignment_id}", headers=test_teacher["headers"])
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "测试作业"
        assert len(data["problems"]) == 1
        assert data["problems"][0]["problem_id"] == problem["id"]

    @pytest.mark.asyncio
    async def test_get_assignment_not_found(self, client: AsyncClient, test_teacher):
        import uuid
        resp = await client.get(f"/api/assignments/{uuid.uuid4()}", headers=test_teacher["headers"])
        assert resp.status_code == 404


class TestUpdateAssignment:
    @pytest.mark.asyncio
    async def test_update_assignment_status(self, client: AsyncClient, test_teacher):
        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        create_resp = await client.post(
            "/api/assignments",
            json={
                "course_id": course["id"],
                "title": "待发布",
                "start_time": "2026-06-01T00:00:00",
                "end_time": "2026-06-30T23:59:59",
                "problem_ids": [problem["id"]],
            },
            headers=test_teacher["headers"],
        )
        aid = create_resp.json()["data"]["id"]

        # Publish
        resp = await client.put(
            f"/api/assignments/{aid}",
            json={"status": "published"},
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "published"

        # Close
        resp2 = await client.put(
            f"/api/assignments/{aid}",
            json={"status": "closed"},
            headers=test_teacher["headers"],
        )
        assert resp2.status_code == 200
        assert resp2.json()["data"]["status"] == "closed"

    @pytest.mark.asyncio
    async def test_update_assignment_invalid_status(self, client: AsyncClient, test_teacher):
        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        create_resp = await client.post(
            "/api/assignments",
            json={
                "course_id": course["id"],
                "title": "测试",
                "start_time": "2026-06-01T00:00:00",
                "end_time": "2026-06-30T23:59:59",
                "problem_ids": [problem["id"]],
            },
            headers=test_teacher["headers"],
        )
        aid = create_resp.json()["data"]["id"]

        resp = await client.put(
            f"/api/assignments/{aid}",
            json={"status": "unknown_status"},
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 400


class TestListCourseAssignments:
    @pytest.mark.asyncio
    async def test_list_assignments_teacher(self, client: AsyncClient, test_teacher):
        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        # Create draft assignment
        await client.post(
            "/api/assignments",
            json={
                "course_id": course["id"],
                "title": "草稿作业",
                "start_time": "2026-06-01T00:00:00",
                "end_time": "2026-06-30T23:59:59",
                "problem_ids": [problem["id"]],
            },
            headers=test_teacher["headers"],
        )
        # Create published assignment
        create_resp2 = await client.post(
            "/api/assignments",
            json={
                "course_id": course["id"],
                "title": "发布作业",
                "start_time": "2026-06-01T00:00:00",
                "end_time": "2026-06-30T23:59:59",
                "problem_ids": [problem["id"]],
            },
            headers=test_teacher["headers"],
        )
        aid2 = create_resp2.json()["data"]["id"]
        await client.put(
            f"/api/assignments/{aid2}",
            json={"status": "published"},
            headers=test_teacher["headers"],
        )

        # Teacher sees all assignments
        resp = await client.get(
            f"/api/assignments/course/{course['id']}", headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) == 2  # Both draft and published

    @pytest.mark.asyncio
    async def test_list_assignments_student_sees_published_only(self, client: AsyncClient, test_teacher, test_student):
        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        # Create draft
        await client.post(
            "/api/assignments",
            json={
                "course_id": course["id"],
                "title": "草稿作业",
                "start_time": "2026-06-01T00:00:00",
                "end_time": "2026-06-30T23:59:59",
                "problem_ids": [problem["id"]],
            },
            headers=test_teacher["headers"],
        )
        # Create and publish
        create_resp2 = await client.post(
            "/api/assignments",
            json={
                "course_id": course["id"],
                "title": "发布作业",
                "start_time": "2026-06-01T00:00:00",
                "end_time": "2026-06-30T23:59:59",
                "problem_ids": [problem["id"]],
            },
            headers=test_teacher["headers"],
        )
        aid2 = create_resp2.json()["data"]["id"]
        await client.put(
            f"/api/assignments/{aid2}",
            json={"status": "published"},
            headers=test_teacher["headers"],
        )

        # Student needs to join course first
        await client.post(
            "/api/courses/join",
            json={"invite_code": course["invite_code"]},
            headers=test_student["headers"],
        )

        resp = await client.get(
            f"/api/assignments/course/{course['id']}", headers=test_student["headers"]
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        # Student only sees published
        assert len(items) == 1
        assert items[0]["status"] == "published"

    @pytest.mark.asyncio
    async def test_list_assignments_student_not_enrolled(self, client: AsyncClient, test_teacher, test_student):
        course = await create_test_course(client, test_teacher["headers"])
        problem = await create_test_problem(client, test_teacher["headers"])

        resp = await client.get(
            f"/api/assignments/course/{course['id']}", headers=test_student["headers"]
        )
        assert resp.status_code == 404

"""Tests for submission and code execution endpoints."""
import uuid

import pytest
from httpx import AsyncClient

from app.models.assignment import Assignment


# Helper: create course + problem + published assignment for testing
async def setup_assignment(client: AsyncClient, teacher_headers):
    """Create a course, problem, and published assignment. Returns (course, problem, assignment)."""
    # Create course
    course_resp = await client.post(
        "/api/courses",
        json={"name": "测试课程_sub", "languages": ["python"]},
        headers=teacher_headers,
    )
    assert course_resp.status_code == 201
    course = course_resp.json()["data"]

    # Create problem with Python signature
    problem_resp = await client.post(
        "/api/problems",
        json={
            "title": "两数之和_sub",
            "description": "求两数之和",
            "difficulty": "easy",
            "time_limit": 5000,
            "memory_limit": 256,
            "tags": ["test"],
            "compare_mode": "exact",
            "signatures": [
                {
                    "language": "python",
                    "function_name": "twoSum",
                    "parameters": [
                        {"name": "nums", "type": "List[int]", "description": "数组"},
                        {"name": "target", "type": "int", "description": "目标"},
                    ],
                    "return_type": "List[int]",
                    "code_template": "def twoSum(nums, target):\n    pass",
                }
            ],
            "test_cases": [
                {
                    "input_params": {"nums": [2, 7, 11, 15], "target": 9},
                    "expected_output": [0, 1],
                    "is_public": True,
                    "description": "示例1",
                },
                {"input_params": {"nums": [3, 2, 4], "target": 6}, "expected_output": [1, 2], "is_public": False},
            ],
        },
        headers=teacher_headers,
    )
    assert problem_resp.status_code == 201
    problem = problem_resp.json()["data"]

    # Create assignment
    assign_resp = await client.post(
        "/api/assignments",
        json={
            "course_id": course["id"],
            "title": "作业_sub",
            "start_time": "2020-01-01T00:00:00",
            "end_time": "2099-12-31T23:59:59",
            "problem_ids": [problem["id"]],
        },
        headers=teacher_headers,
    )
    assert assign_resp.status_code == 201
    assignment = assign_resp.json()["data"]

    # Publish the assignment
    await client.put(
        f"/api/assignments/{assignment['id']}",
        json={"status": "published"},
        headers=teacher_headers,
    )

    return course, problem, assignment


class TestSubmitCode:
    @pytest.mark.asyncio
    async def test_submit_code_success(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        payload = {
            "assignment_id": assignment["id"],
            "problem_id": problem["id"],
            "language": "python",
            "code": "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i]+nums[j]==target:\n                return [i,j]\n    return []",
        }
        resp = await client.post("/api/submissions", json=payload, headers=test_teacher["headers"])
        assert resp.status_code == 202
        data = resp.json()["data"]
        assert data["status"] == "pending"
        assert data["submission_id"]

    @pytest.mark.asyncio
    async def test_submit_code_no_auth(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])
        payload = {
            "assignment_id": assignment["id"],
            "problem_id": problem["id"],
            "language": "python",
            "code": "def twoSum(nums, target):\n    return [0, 1]",
        }
        resp = await client.post("/api/submissions", json=payload)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_submit_code_assignment_not_found(self, client: AsyncClient, test_teacher):
        problem_resp = await client.post(
            "/api/problems",
            json={
                "title": "test_404",
                "description": "test",
                "difficulty": "easy",
                "signatures": [
                    {
                        "language": "python",
                        "function_name": "f",
                        "parameters": [{"name": "x", "type": "int", "description": ""}],
                        "return_type": "int",
                        "code_template": "def f(x):\n    pass",
                    }
                ],
                "test_cases": [
                    {"input_params": {"x": 1}, "expected_output": 2, "is_public": True}
                ],
            },
            headers=test_teacher["headers"],
        )
        problem = problem_resp.json()["data"]

        payload = {
            "assignment_id": str(uuid.uuid4()),
            "problem_id": problem["id"],
            "language": "python",
            "code": "def f(x):\n    return x+1",
        }
        resp = await client.post("/api/submissions", json=payload, headers=test_teacher["headers"])
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_code_unsupported_language(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        payload = {
            "assignment_id": assignment["id"],
            "problem_id": problem["id"],
            "language": "java",
            "code": "class Solution { public int[] twoSum(int[] nums, int target) { return new int[]{0,1}; } }",
        }
        resp = await client.post("/api/submissions", json=payload, headers=test_teacher["headers"])
        assert resp.status_code == 400


class TestGetSubmission:
    @pytest.mark.asyncio
    async def test_get_submission_success(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        submit_resp = await client.post(
            "/api/submissions",
            json={
                "assignment_id": assignment["id"],
                "problem_id": problem["id"],
                "language": "python",
                "code": "def twoSum(nums, target):\n    return [0, 1]",
            },
            headers=test_teacher["headers"],
        )
        sub_id = submit_resp.json()["data"]["submission_id"]

        resp = await client.get(f"/api/submissions/{sub_id}", headers=test_teacher["headers"])
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["language"] == "python"
        assert data["status"] == "pending"
        assert "results" in data

    @pytest.mark.asyncio
    async def test_get_submission_not_found(self, client: AsyncClient, test_teacher):
        resp = await client.get(f"/api/submissions/{uuid.uuid4()}", headers=test_teacher["headers"])
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_submission_student_cant_see_others(self, client: AsyncClient, test_teacher, test_student):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        submit_resp = await client.post(
            "/api/submissions",
            json={
                "assignment_id": assignment["id"],
                "problem_id": problem["id"],
                "language": "python",
                "code": "def twoSum(nums, target):\n    return [0, 1]",
            },
            headers=test_teacher["headers"],
        )
        sub_id = submit_resp.json()["data"]["submission_id"]

        resp = await client.get(f"/api/submissions/{sub_id}", headers=test_student["headers"])
        assert resp.status_code == 404


class TestListSubmissions:
    @pytest.mark.asyncio
    async def test_list_assignment_submissions(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        await client.post(
            "/api/submissions",
            json={
                "assignment_id": assignment["id"],
                "problem_id": problem["id"],
                "language": "python",
                "code": "def twoSum(nums, target):\n    return [0, 1]",
            },
            headers=test_teacher["headers"],
        )

        resp = await client.get(
            f"/api/submissions/assignment/{assignment['id']}", headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_list_submissions_student_only_own(self, client: AsyncClient, test_teacher, test_student):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        await client.post(
            "/api/submissions",
            json={
                "assignment_id": assignment["id"],
                "problem_id": problem["id"],
                "language": "python",
                "code": "def twoSum(nums, target):\n    return [0, 1]",
            },
            headers=test_teacher["headers"],
        )

        resp = await client.get(
            f"/api/submissions/assignment/{assignment['id']}", headers=test_student["headers"]
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        # Student sees 0 because teacher's submissions aren't theirs
        assert len(items) == 0


class TestCodeDraft:
    @pytest.mark.asyncio
    async def test_save_and_get_draft(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        # Save draft
        resp = await client.put(
            "/api/submissions/drafts",
            params={
                "problem_id": problem["id"],
                "assignment_id": assignment["id"],
                "language": "python",
                "code": "def twoSum(nums, target):\n    # draft\n    return [0, 1]",
            },
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200

        # Get draft
        resp2 = await client.get(
            f"/api/submissions/drafts/{problem['id']}",
            params={"assignment_id": assignment["id"], "language": "python"},
            headers=test_teacher["headers"],
        )
        assert resp2.status_code == 200
        data = resp2.json()["data"]
        assert "draft" in data["code"]

    @pytest.mark.asyncio
    async def test_get_draft_not_found(self, client: AsyncClient, test_teacher):
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/submissions/drafts/{fake_id}",
            params={"assignment_id": str(uuid.uuid4()), "language": "python"},
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["code"] is None

    @pytest.mark.asyncio
    async def test_save_draft_updates_existing(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        # Save first draft
        await client.put(
            "/api/submissions/drafts",
            params={
                "problem_id": problem["id"],
                "assignment_id": assignment["id"],
                "language": "python",
                "code": "version 1",
            },
            headers=test_teacher["headers"],
        )

        # Save second draft (update)
        await client.put(
            "/api/submissions/drafts",
            params={
                "problem_id": problem["id"],
                "assignment_id": assignment["id"],
                "language": "python",
                "code": "version 2",
            },
            headers=test_teacher["headers"],
        )

        # Verify it's updated
        resp = await client.get(
            f"/api/submissions/drafts/{problem['id']}",
            params={"assignment_id": assignment["id"], "language": "python"},
            headers=test_teacher["headers"],
        )
        assert "version 2" in resp.json()["data"]["code"]


class TestRunCode:
    @pytest.mark.asyncio
    async def test_run_code_python_accepted(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        payload = {
            "language": "python",
            "code": "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i]+nums[j]==target:\n                return [i,j]\n    return []",
            "assignment_id": assignment["id"],
        }
        resp = await client.post(
            f"/api/problems/{problem['id']}/run", json=payload, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["compile_error"] is None
        assert len(data["results"]) >= 1
        # First (and only public) test case should pass
        assert data["results"][0]["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_run_code_python_wrong_answer(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        payload = {
            "language": "python",
            "code": "def twoSum(nums, target):\n    return [0, 0]",
            "assignment_id": assignment["id"],
        }
        resp = await client.post(
            f"/api/problems/{problem['id']}/run", json=payload, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["results"][0]["status"] == "wrong_answer"

    @pytest.mark.asyncio
    async def test_run_code_python_syntax_error(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        payload = {
            "language": "python",
            "code": "def twoSum(nums target):  # missing comma\n    return [0, 1]",
            "assignment_id": assignment["id"],
        }
        resp = await client.post(
            f"/api/problems/{problem['id']}/run", json=payload, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Should have a compile error
        assert data["compile_error"] is not None

    @pytest.mark.asyncio
    async def test_run_code_unsupported_language(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        payload = {
            "language": "java",
            "code": "class Solution {}",
            "assignment_id": assignment["id"],
        }
        resp = await client.post(
            f"/api/problems/{problem['id']}/run", json=payload, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "full judge service" in data["compile_error"] or not data["results"]

    @pytest.mark.asyncio
    async def test_run_custom_code(self, client: AsyncClient, test_teacher):
        course, problem, assignment = await setup_assignment(client, test_teacher["headers"])

        payload = {
            "language": "python",
            "code": "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i]+nums[j]==target:\n                return [i,j]\n    return []",
            "assignment_id": assignment["id"],
            "custom_input": {"nums": [1, 2, 3, 4], "target": 7},
        }
        resp = await client.post(
            f"/api/problems/{problem['id']}/run-custom", json=payload, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["output"] is not None

"""Tests for problem management endpoints."""
import pytest
from httpx import AsyncClient


# Helper: build a valid problem creation payload
def make_problem_payload(**overrides):
    payload = {
        "title": "两数之和",
        "description": "给定一个整数数组 nums 和一个整数目标值 target...",
        "difficulty": "easy",
        "time_limit": 1000,
        "memory_limit": 256,
        "tags": ["array", "hash-table"],
        "compare_mode": "exact",
        "signatures": [
            {
                "language": "python",
                "function_name": "twoSum",
                "parameters": [
                    {"name": "nums", "type": "List[int]", "description": "整数数组"},
                    {"name": "target", "type": "int", "description": "目标值"},
                ],
                "return_type": "List[int]",
                "code_template": "def twoSum(nums, target):\n    pass",
                "prelude_code": None,
                "driver_template": None,
            }
        ],
        "test_cases": [
            {
                "input_params": {"nums": [2, 7, 11, 15], "target": 9},
                "expected_output": [0, 1],
                "is_public": True,
                "description": "示例1",
            },
            {
                "input_params": {"nums": [3, 2, 4], "target": 6},
                "expected_output": [1, 2],
                "is_public": False,
                "description": "隐藏用例",
            },
        ],
    }
    payload.update(overrides)
    return payload


class TestCreateProblem:
    @pytest.mark.asyncio
    async def test_create_problem_success(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload()
        resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == "两数之和"
        assert data["difficulty"] == "easy"
        assert data["tags"] == ["array", "hash-table"]
        assert data["teacher_id"] == str(test_teacher["user"].id)

    @pytest.mark.asyncio
    async def test_create_problem_no_auth(self, client: AsyncClient):
        payload = make_problem_payload()
        resp = await client.post("/api/problems", json=payload)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_create_problem_student_forbidden(self, client: AsyncClient, test_student):
        payload = make_problem_payload()
        resp = await client.post("/api/problems", json=payload, headers=test_student["headers"])
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_create_problem_missing_signatures(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload(signatures=[])
        resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_problem_missing_test_cases(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload(test_cases=[])
        resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        assert resp.status_code == 422


class TestListProblems:
    @pytest.mark.asyncio
    async def test_list_problems_teacher(self, client: AsyncClient, test_teacher):
        # Create a problem first
        payload = make_problem_payload()
        await client.post("/api/problems", json=payload, headers=test_teacher["headers"])

        resp = await client.get("/api/problems", headers=test_teacher["headers"])
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_problems_filter_difficulty(self, client: AsyncClient, test_teacher):
        # Create problems with different difficulties
        await client.post(
            "/api/problems",
            json=make_problem_payload(title="Easy Problem", difficulty="easy"),
            headers=test_teacher["headers"],
        )
        await client.post(
            "/api/problems",
            json=make_problem_payload(title="Hard Problem", difficulty="hard"),
            headers=test_teacher["headers"],
        )

        resp = await client.get(
            "/api/problems", params={"difficulty": "hard"}, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        for item in items:
            assert item["difficulty"] == "hard"

    @pytest.mark.asyncio
    async def test_list_problems_filter_language(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload(title="Python Problem")
        await client.post("/api/problems", json=payload, headers=test_teacher["headers"])

        resp = await client.get(
            "/api/problems", params={"language": "python"}, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_problems_filter_tag(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload(title="Tagged Problem", tags=["dp", "greedy"])
        await client.post("/api/problems", json=payload, headers=test_teacher["headers"])

        resp = await client.get(
            "/api/problems", params={"tag": "dp"}, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1
        for item in items:
            assert "dp" in item["tags"]

    @pytest.mark.asyncio
    async def test_list_problems_student_sees_all(self, client: AsyncClient, test_teacher, test_student):
        # Teacher creates a problem
        await client.post(
            "/api/problems",
            json=make_problem_payload(title="Student Visible"),
            headers=test_teacher["headers"],
        )
        # Student can list all problems (not filtered by teacher_id)
        resp = await client.get("/api/problems", headers=test_student["headers"])
        assert resp.status_code == 200


class TestGetProblem:
    @pytest.mark.asyncio
    async def test_get_problem_teacher_sees_all_testcases(self, client: AsyncClient, test_teacher):
        # Create problem with both public and hidden test cases
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        resp = await client.get(f"/api/problems/{problem_id}", headers=test_teacher["headers"])
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "signatures" in data
        assert len(data["signatures"]) == 1
        assert len(data["test_cases"]) == 2  # Teacher sees all

    @pytest.mark.asyncio
    async def test_get_problem_student_sees_public_only(self, client: AsyncClient, test_teacher, test_student):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        resp = await client.get(f"/api/problems/{problem_id}", headers=test_student["headers"])
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Student should only see public test cases
        assert all(tc["is_public"] for tc in data["test_cases"])
        assert len(data["test_cases"]) == 1

    @pytest.mark.asyncio
    async def test_get_problem_not_found(self, client: AsyncClient, test_teacher):
        import uuid
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/api/problems/{fake_id}", headers=test_teacher["headers"])
        assert resp.status_code == 404


class TestUpdateProblem:
    @pytest.mark.asyncio
    async def test_update_problem_success(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        update_data = {"title": "两数之和（改）", "difficulty": "medium", "tags": ["array"]}
        resp = await client.put(
            f"/api/problems/{problem_id}", json=update_data, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "两数之和（改）"
        assert data["difficulty"] == "medium"
        assert data["tags"] == ["array"]

    @pytest.mark.asyncio
    async def test_update_problem_not_owner(self, client: AsyncClient, test_teacher, db_session):
        """Another teacher cannot update someone else's problem."""
        from app.core.security import create_access_token, hash_password
        from app.models.user import User

        # Create another teacher
        other_teacher = User(
            username="otherteacher",
            email="other@test.com",
            password_hash=hash_password("Test1234"),
            role="teacher",
        )
        db_session.add(other_teacher)
        await db_session.flush()
        await db_session.refresh(other_teacher)
        other_token = create_access_token(str(other_teacher.id), other_teacher.role)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Create problem with original teacher
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        # Other teacher tries to update
        resp = await client.put(
            f"/api/problems/{problem_id}",
            json={"title": "Hacked"},
            headers=other_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_problem_student_forbidden(self, client: AsyncClient, test_teacher, test_student):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        resp = await client.put(
            f"/api/problems/{problem_id}",
            json={"title": "Nope"},
            headers=test_student["headers"],
        )
        assert resp.status_code == 403


class TestDeleteProblem:
    @pytest.mark.asyncio
    async def test_delete_problem_success(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        resp = await client.delete(f"/api/problems/{problem_id}", headers=test_teacher["headers"])
        assert resp.status_code == 200

        # Verify deleted
        resp2 = await client.get(f"/api/problems/{problem_id}", headers=test_teacher["headers"])
        assert resp2.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_problem_not_owner(self, client: AsyncClient, test_teacher, db_session):
        from app.core.security import create_access_token, hash_password
        from app.models.user import User

        other_teacher = User(
            username="delteacher",
            email="delteacher@test.com",
            password_hash=hash_password("Test1234"),
            role="teacher",
        )
        db_session.add(other_teacher)
        await db_session.flush()
        await db_session.refresh(other_teacher)
        other_token = create_access_token(str(other_teacher.id), other_teacher.role)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        resp = await client.delete(f"/api/problems/{problem_id}", headers=other_headers)
        assert resp.status_code == 404


class TestSignatureManagement:
    @pytest.mark.asyncio
    async def test_upsert_signature_create(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        # Add Java signature
        sig_data = {
            "language": "java",
            "function_name": "twoSum",
            "parameters": [
                {"name": "nums", "type": "int[]", "description": "整数数组"},
                {"name": "target", "type": "int", "description": "目标值"},
            ],
            "return_type": "int[]",
            "code_template": "public int[] twoSum(int[] nums, int target) {\n    return null;\n}",
        }
        resp = await client.post(
            f"/api/problems/{problem_id}/signatures", json=sig_data, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200

        # Verify signature exists
        resp2 = await client.get(
            f"/api/problems/{problem_id}/signatures/java", headers=test_teacher["headers"]
        )
        assert resp2.status_code == 200
        assert resp2.json()["data"]["function_name"] == "twoSum"
        assert resp2.json()["data"]["language"] == "java"

    @pytest.mark.asyncio
    async def test_upsert_signature_update(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        # Update existing python signature
        sig_data = {
            "language": "python",
            "function_name": "two_sum",
            "parameters": [
                {"name": "nums", "type": "List[int]", "description": "数组"},
                {"name": "target", "type": "int", "description": "目标"},
            ],
            "return_type": "List[int]",
            "code_template": "def two_sum(nums, target):\n    pass",
        }
        resp = await client.post(
            f"/api/problems/{problem_id}/signatures", json=sig_data, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200

        # Verify updated
        resp2 = await client.get(
            f"/api/problems/{problem_id}/signatures/python", headers=test_teacher["headers"]
        )
        assert resp2.status_code == 200
        assert resp2.json()["data"]["function_name"] == "two_sum"

    @pytest.mark.asyncio
    async def test_get_signature_not_found(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        resp = await client.get(
            f"/api/problems/{problem_id}/signatures/rust", headers=test_teacher["headers"]
        )
        assert resp.status_code == 404


class TestTestCaseManagement:
    @pytest.mark.asyncio
    async def test_add_test_case(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        tc_data = {
            "input_params": {"nums": [1, 2, 3, 4], "target": 5},
            "expected_output": [0, 3],
            "is_public": True,
            "description": "新增用例",
        }
        resp = await client.post(
            f"/api/problems/{problem_id}/testcases", json=tc_data, headers=test_teacher["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["order"] == 2  # Already 2 test cases (order 0,1), new one gets 2
        assert data["is_public"] is True

    @pytest.mark.asyncio
    async def test_update_test_case(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        # Get test cases
        detail_resp = await client.get(f"/api/problems/{problem_id}", headers=test_teacher["headers"])
        tc_id = detail_resp.json()["data"]["test_cases"][0]["id"]

        # Update it
        update_data = {
            "input_params": {"nums": [1, 1], "target": 2},
            "expected_output": [0, 1],
            "is_public": False,
            "description": "修改后的用例",
        }
        resp = await client.put(
            f"/api/problems/{problem_id}/testcases/{tc_id}",
            json=update_data,
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_test_case(self, client: AsyncClient, test_teacher):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        # Get test cases
        detail_resp = await client.get(f"/api/problems/{problem_id}", headers=test_teacher["headers"])
        tc_id = detail_resp.json()["data"]["test_cases"][0]["id"]

        # Delete it
        resp = await client.delete(
            f"/api/problems/{problem_id}/testcases/{tc_id}", headers=test_teacher["headers"]
        )
        assert resp.status_code == 200

        # Verify deleted (check count)
        detail_resp2 = await client.get(f"/api/problems/{problem_id}", headers=test_teacher["headers"])
        assert len(detail_resp2.json()["data"]["test_cases"]) == 1

    @pytest.mark.asyncio
    async def test_add_test_case_student_forbidden(self, client: AsyncClient, test_teacher, test_student):
        payload = make_problem_payload()
        create_resp = await client.post("/api/problems", json=payload, headers=test_teacher["headers"])
        problem_id = create_resp.json()["data"]["id"]

        tc_data = {
            "input_params": {"nums": [1, 2], "target": 3},
            "expected_output": [0, 1],
            "is_public": True,
        }
        resp = await client.post(
            f"/api/problems/{problem_id}/testcases", json=tc_data, headers=test_student["headers"]
        )
        assert resp.status_code == 403

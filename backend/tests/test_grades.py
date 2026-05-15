"""Tests for grade management endpoints."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment, AssignmentProblem
from app.models.course import CourseStudent
from app.models.submission import Submission


# ─── Helpers ──────────────────────────────────────────────────────────

async def create_course_with_students(
    client: AsyncClient, teacher_headers: dict, db_session: AsyncSession,
    student_headers_list: list[dict],
) -> dict:
    """Create a course and enroll given students. Returns the course dict."""
    resp = await client.post(
        "/api/courses",
        json={"name": "成绩测试课程", "languages": ["python"]},
        headers=teacher_headers,
    )
    assert resp.status_code == 201
    course = resp.json()["data"]

    # Each student joins via invite code
    for sh in student_headers_list:
        join_resp = await client.post(
            "/api/courses/join",
            json={"invite_code": course["invite_code"]},
            headers=sh["headers"],
        )
        assert join_resp.status_code == 200

    return course


async def create_problem_with_testcase(
    client: AsyncClient, teacher_headers: dict, title: str,
    func_name: str = "solve",
) -> dict:
    """Create a problem with a simple Python signature and one public test case."""
    resp = await client.post(
        "/api/problems",
        json={
            "title": title,
            "description": "测试",
            "difficulty": "easy",
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["test"],
            "compare_mode": "exact",
            "signatures": [
                {
                    "language": "python",
                    "function_name": func_name,
                    "parameters": [{"name": "x", "type": "int", "description": "输入"}],
                    "return_type": "int",
                    "code_template": f"def {func_name}(x):\n    pass",
                }
            ],
            "test_cases": [
                {
                    "input_params": {"x": 1},
                    "expected_output": 1,
                    "is_public": True,
                    "description": "示例1",
                }
            ],
        },
        headers=teacher_headers,
    )
    assert resp.status_code == 201
    return resp.json()["data"]


async def create_published_assignment(
    client: AsyncClient, teacher_headers: dict,
    course_id: str, problem_ids: list[str],
    title: str = "测试作业",
    score_weights: list[int] | None = None,
) -> dict:
    """Create and publish an assignment with given problems."""
    if score_weights is None:
        score_weights = [100] * len(problem_ids)

    resp = await client.post(
        "/api/assignments",
        json={
            "course_id": course_id,
            "title": title,
            "description": "测试作业描述",
            "start_time": "2026-01-01T00:00:00",
            "end_time": "2026-12-31T23:59:59",
            "problem_ids": problem_ids,
            "score_weights": score_weights,
        },
        headers=teacher_headers,
    )
    assert resp.status_code == 201
    assignment = resp.json()["data"]

    # Publish it
    pub_resp = await client.put(
        f"/api/assignments/{assignment['id']}",
        json={"status": "published"},
        headers=teacher_headers,
    )
    assert pub_resp.status_code == 200
    return assignment


async def create_submission(
    client: AsyncClient, student_headers: dict,
    problem_id: str, assignment_id: str,
    code: str = "def solve(x):\n    return x",
    language: str = "python",
) -> dict:
    """Submit code for a problem (the submission status will be 'pending')."""
    resp = await client.post(
        f"/api/problems/{problem_id}/run",
        json={
            "code": code,
            "language": language,
            "assignment_id": assignment_id,
        },
        headers=student_headers,
    )
    # We don't care if the run succeeds or not – we will set score directly in DB
    return resp.json() if resp.status_code < 500 else {}


async def seed_submission_score(
    db_session: AsyncSession,
    student_id: str | uuid.UUID,
    assignment_id: str,
    problem_id: str,
    score: int,
    status: str = "accepted",
) -> str:
    """Directly insert a submission with a known score."""
    sub = Submission(
        student_id=uuid.UUID(student_id) if isinstance(student_id, str) else student_id,
        assignment_id=uuid.UUID(assignment_id),
        problem_id=uuid.UUID(problem_id),
        language="python",
        code="def solve(x): return x",
        status=status,
        score=score,
    )
    db_session.add(sub)
    await db_session.flush()
    await db_session.refresh(sub)
    return str(sub.id)


# ─── Tests ─────────────────────────────────────────────────────────────

class TestGetCourseGrades:
    """GET /api/grades/courses/{course_id}"""

    @pytest.mark.asyncio
    async def test_teacher_view_all_grades(
        self, client: AsyncClient, test_teacher: dict, test_student: dict,
        db_session: AsyncSession,
    ):
        """Teacher can view grades for all students in a course."""
        course = await create_course_with_students(
            client, test_teacher["headers"], db_session,
            [test_student],
        )
        problem = await create_problem_with_testcase(client, test_teacher["headers"], "P1")
        assignment = await create_published_assignment(
            client, test_teacher["headers"], course["id"], [problem["id"]],
        )

        # Seed a submission for the student
        await seed_submission_score(
            db_session, test_student["user"].id, assignment["id"],
            problem["id"], score=90,
        )

        resp = await client.get(
            f"/api/grades/courses/{course['id']}",
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        grades = data["data"]["grades"]
        assert len(grades) == 1
        assert grades[0]["student_id"] == str(test_student["user"].id)
        assert grades[0]["total_score"] == 90.0
        assert data["data"]["statistics"]["student_count"] == 1

    @pytest.mark.asyncio
    async def test_student_sees_only_own_grade(
        self, client: AsyncClient, test_teacher: dict,
        test_student: dict, db_session: AsyncSession,
    ):
        """Student should only see their own grade, not other students'."""
        # Create a second student
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        other_user = User(
            username="otherstudent",
            email="other@test.com",
            password_hash=hash_password("Test1234"),
            role="student",
        )
        db_session.add(other_user)
        await db_session.flush()
        await db_session.refresh(other_user)
        other_headers = {
            "Authorization": f"Bearer {create_access_token(str(other_user.id), 'student')}",
        }

        course = await create_course_with_students(
            client, test_teacher["headers"], db_session,
            [test_student, {"user": other_user, "headers": other_headers}],
        )
        problem = await create_problem_with_testcase(client, test_teacher["headers"], "P1")
        assignment = await create_published_assignment(
            client, test_teacher["headers"], course["id"], [problem["id"]],
        )

        await seed_submission_score(
            db_session, test_student["user"].id, assignment["id"],
            problem["id"], score=95,
        )
        await seed_submission_score(
            db_session, other_user.id, assignment["id"],
            problem["id"], score=80,
        )

        # Student requests grades
        resp = await client.get(
            f"/api/grades/courses/{course['id']}",
            headers=test_student["headers"],
        )
        assert resp.status_code == 200
        grades = resp.json()["data"]["grades"]
        assert len(grades) == 1
        assert grades[0]["student_id"] == str(test_student["user"].id)
        assert grades[0]["total_score"] == 95.0

    @pytest.mark.asyncio
    async def test_unauthorized_access(
        self, client: AsyncClient, test_teacher: dict, test_student: dict,
        db_session: AsyncSession,
    ):
        """Unauthenticated request should be rejected."""
        course = await create_course_with_students(
            client, test_teacher["headers"], db_session,
            [test_student],
        )
        resp = await client.get(f"/api/grades/courses/{course['id']}")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_nonexistent_course(
        self, client: AsyncClient, test_teacher: dict,
    ):
        """Requesting grades for a non-existent course should return 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/grades/courses/{fake_id}",
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_empty_course_no_students(
        self, client: AsyncClient, test_teacher: dict,
        db_session: AsyncSession,
    ):
        """A course with no enrolled students returns empty grades list."""
        resp = await client.post(
            "/api/courses",
            json={"name": "空课程", "languages": ["python"]},
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 201
        course = resp.json()["data"]

        resp = await client.get(
            f"/api/grades/courses/{course['id']}",
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["grades"] == []
        assert data["statistics"] == {}

    @pytest.mark.asyncio
    async def test_weighted_score_calculation(
        self, client: AsyncClient, test_teacher: dict,
        test_student: dict, db_session: AsyncSession,
    ):
        """Grade calculation should respect score_weights."""
        course = await create_course_with_students(
            client, test_teacher["headers"], db_session,
            [test_student],
        )
        p1 = await create_problem_with_testcase(client, test_teacher["headers"], "P1", func_name="solve")
        p2 = await create_problem_with_testcase(client, test_teacher["headers"], "P2", func_name="add")

        # P1 weight=60, P2 weight=40
        assignment = await create_published_assignment(
            client, test_teacher["headers"], course["id"],
            [p1["id"], p2["id"]],
            title="加权测试",
            score_weights=[60, 40],
        )

        await seed_submission_score(
            db_session, test_student["user"].id, assignment["id"],
            p1["id"], score=100,
        )
        await seed_submission_score(
            db_session, test_student["user"].id, assignment["id"],
            p2["id"], score=50,
        )

        resp = await client.get(
            f"/api/grades/courses/{course['id']}",
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200
        grade = resp.json()["data"]["grades"][0]
        # 100 * 60/100 + 50 * 40/100 = 60 + 20 = 80
        assert grade["total_score"] == 80.0
        assignments = grade["assignments"]
        assign_id = str(assignment["id"])
        assert assign_id in assignments
        # 100*60/100 + 50*40/100 = 80
        assert assignments[assign_id]["score"] == 80.0

    @pytest.mark.asyncio
    async def test_best_submission_used(
        self, client: AsyncClient, test_teacher: dict,
        test_student: dict, db_session: AsyncSession,
    ):
        """Only the best accepted submission score should be used."""
        course = await create_course_with_students(
            client, test_teacher["headers"], db_session,
            [test_student],
        )
        problem = await create_problem_with_testcase(client, test_teacher["headers"], "P1")
        assignment = await create_published_assignment(
            client, test_teacher["headers"], course["id"], [problem["id"]],
        )

        # Add two submissions: one with lower score, one with higher
        await seed_submission_score(
            db_session, test_student["user"].id, assignment["id"],
            problem["id"], score=40,
        )
        await seed_submission_score(
            db_session, test_student["user"].id, assignment["id"],
            problem["id"], score=85,
        )

        resp = await client.get(
            f"/api/grades/courses/{course['id']}",
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200
        grade = resp.json()["data"]["grades"][0]
        assert grade["total_score"] == 85.0  # best score

    @pytest.mark.asyncio
    async def test_only_accepted_submissions_count(
        self, client: AsyncClient, test_teacher: dict,
        test_student: dict, db_session: AsyncSession,
    ):
        """Non-accepted submissions should not contribute to the grade."""
        course = await create_course_with_students(
            client, test_teacher["headers"], db_session,
            [test_student],
        )
        problem = await create_problem_with_testcase(client, test_teacher["headers"], "P1")
        assignment = await create_published_assignment(
            client, test_teacher["headers"], course["id"], [problem["id"]],
        )

        # Only a rejected submission
        await seed_submission_score(
            db_session, test_student["user"].id, assignment["id"],
            problem["id"], score=100, status="rejected",
        )

        resp = await client.get(
            f"/api/grades/courses/{course['id']}",
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200
        grade = resp.json()["data"]["grades"][0]
        # No accepted submission → score should be 0
        assert grade["total_score"] == 0.0


class TestExportGrades:
    """GET /api/grades/courses/{course_id}/export"""

    @pytest.mark.asyncio
    async def test_export_xlsx(
        self, client: AsyncClient, test_teacher: dict,
        test_student: dict, db_session: AsyncSession,
    ):
        """Teacher can export grades as XLSX."""
        course = await create_course_with_students(
            client, test_teacher["headers"], db_session,
            [test_student],
        )
        problem = await create_problem_with_testcase(client, test_teacher["headers"], "P1")
        assignment = await create_published_assignment(
            client, test_teacher["headers"], course["id"], [problem["id"]],
        )
        await seed_submission_score(
            db_session, test_student["user"].id, assignment["id"],
            problem["id"], score=90,
        )

        resp = await client.get(
            f"/api/grades/courses/{course['id']}/export?format=xlsx",
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert "grades" in resp.headers.get("content-disposition", "").lower()

    @pytest.mark.asyncio
    async def test_export_csv(
        self, client: AsyncClient, test_teacher: dict,
        test_student: dict, db_session: AsyncSession,
    ):
        """Teacher can export grades as CSV."""
        course = await create_course_with_students(
            client, test_teacher["headers"], db_session,
            [test_student],
        )
        problem = await create_problem_with_testcase(client, test_teacher["headers"], "P1")
        assignment = await create_published_assignment(
            client, test_teacher["headers"], course["id"], [problem["id"]],
        )
        await seed_submission_score(
            db_session, test_student["user"].id, assignment["id"],
            problem["id"], score=90,
        )

        resp = await client.get(
            f"/api/grades/courses/{course['id']}/export?format=csv",
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("text/csv")
        assert "grades" in resp.headers.get("content-disposition", "").lower()

    @pytest.mark.asyncio
    async def test_export_requires_teacher(
        self, client: AsyncClient, test_teacher: dict,
        test_student: dict, db_session: AsyncSession,
    ):
        """Students cannot export grades."""
        course = await create_course_with_students(
            client, test_teacher["headers"], db_session,
            [test_student],
        )
        resp = await client.get(
            f"/api/grades/courses/{course['id']}/export?format=xlsx",
            headers=test_student["headers"],
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_export_nonexistent_course(
        self, client: AsyncClient, test_teacher: dict,
    ):
        """Exporting grades for a non-existent course should return 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/grades/courses/{fake_id}/export?format=xlsx",
            headers=test_teacher["headers"],
        )
        assert resp.status_code == 404

import uuid as uuid_mod
from collections import defaultdict
from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_get, cache_set
from app.core.errors import ForbiddenError, NotFoundError
from app.database import get_db
from app.dependencies import get_current_user, require_teacher
from app.models.assignment import Assignment, AssignmentProblem
from app.models.course import Course, CourseStudent
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.user import User
from app.schemas.response import success_response

router = APIRouter()


@router.get("/courses/{course_id}")
async def get_course_grades(
    course_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course_id_uuid = uuid_mod.UUID(course_id)

    # Try cache first (only for non-student roles, since student data is filtered per-user)
    if user.role != "student":
        cache_key = f"grades:course:{course_id}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return success_response(cached)

    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id_uuid))
    course = course_result.scalar_one_or_none()
    if not course:
        raise NotFoundError("course", course_id)

    # Get all assignments for this course
    assignments_result = await db.execute(
        select(Assignment)
        .where(Assignment.course_id == course_id_uuid)
        .order_by(Assignment.created_at)
    )
    assignments = assignments_result.scalars().all()
    assignment_ids = [a.id for a in assignments]

    # Get all students in the course
    students_result = await db.execute(
        select(User)
        .join(CourseStudent, CourseStudent.student_id == User.id)
        .where(CourseStudent.course_id == course_id_uuid)
    )
    students = students_result.scalars().all()
    student_ids = [s.id for s in students]

    # ── Batch 1: Load all AssignmentProblems for all assignments ──
    aps_result = await db.execute(
        select(AssignmentProblem).where(
            AssignmentProblem.assignment_id.in_(assignment_ids)
        )
    )
    all_aps = aps_result.scalars().all()

    # Build map: assignment_id -> list of AssignmentProblem
    assignment_problems_map: dict[uuid_mod.UUID, list[AssignmentProblem]] = defaultdict(list)
    problem_ids = set()
    for ap in all_aps:
        assignment_problems_map[ap.assignment_id].append(ap)
        problem_ids.add(ap.problem_id)
    problem_ids_list = list(problem_ids)

    # ── Batch 2: Load best submission scores for ALL students in one query ──
    # Best = max score where status == "accepted"
    best_score_map: dict[tuple[uuid_mod.UUID, uuid_mod.UUID, uuid_mod.UUID], int] = {}
    if student_ids and problem_ids_list:
        best_scores_result = await db.execute(
            select(
                Submission.student_id,
                Submission.assignment_id,
                Submission.problem_id,
                func.max(Submission.score).label("best_score"),
            )
            .where(
                Submission.student_id.in_(student_ids),
                Submission.assignment_id.in_(assignment_ids),
                Submission.problem_id.in_(problem_ids_list),
                Submission.status == "accepted",
            )
            .group_by(
                Submission.student_id,
                Submission.assignment_id,
                Submission.problem_id,
            )
        )
        for row in best_scores_result.all():
            best_score_map[(row.student_id, row.assignment_id, row.problem_id)] = (
                row.best_score or 0
            )

    # ── Compute grades in Python memory ──
    grade_data = []
    for student in students:
        student_grades = {
            "student_id": str(student.id),
            "username": student.username,
            "nickname": student.nickname,
            "assignments": {},
            "total_score": 0,
        }

        for assignment in assignments:
            aps = assignment_problems_map.get(assignment.id, [])
            assignment_score = 0
            for ap in aps:
                best_score = best_score_map.get(
                    (student.id, assignment.id, ap.problem_id), 0
                )
                assignment_score += best_score * ap.score_weight / 100

            student_grades["assignments"][str(assignment.id)] = {
                "title": assignment.title,
                "score": round(assignment_score, 1),
            }
            student_grades["total_score"] += assignment_score

        student_grades["total_score"] = round(student_grades["total_score"], 1)
        grade_data.append(student_grades)

    # Calculate statistics
    scores = [g["total_score"] for g in grade_data]
    stats = {}
    if scores:
        stats = {
            "average": round(sum(scores) / len(scores), 1),
            "max": max(scores),
            "min": min(scores),
            "student_count": len(scores),
        }

    # ── Batch 3: Calculate assignment-level pass rates in batch ──
    assignment_pass_rates = []
    if assignment_ids and problem_ids_list and students:
        # Get problem_ids per assignment (reuse the map)
        assignment_problem_ids_map = {
            aid: [ap.problem_id for ap in aps]
            for aid, aps in assignment_problems_map.items()
        }

        # Query: passed student count per assignment
        passed_counts_result = await db.execute(
            select(
                Submission.assignment_id,
                func.count(func.distinct(Submission.student_id)).label("passed_count"),
            )
            .where(
                Submission.assignment_id.in_(assignment_ids),
                Submission.problem_id.in_(problem_ids_list),
                Submission.status == "accepted",
                Submission.score > 0,
            )
            .group_by(Submission.assignment_id)
        )
        passed_counts = {
            row.assignment_id: row.passed_count
            for row in passed_counts_result.all()
        }

        # Query: average score per assignment
        avg_scores_result = await db.execute(
            select(
                Submission.assignment_id,
                func.avg(Submission.score).label("avg_score"),
            )
            .where(
                Submission.assignment_id.in_(assignment_ids),
                Submission.problem_id.in_(problem_ids_list),
                Submission.status == "accepted",
            )
            .group_by(Submission.assignment_id)
        )
        avg_scores = {
            row.assignment_id: round(row.avg_score, 1) if row.avg_score is not None else 0.0
            for row in avg_scores_result.all()
        }

        for assignment in assignments:
            prob_ids = assignment_problem_ids_map.get(assignment.id, [])
            if not prob_ids:
                assignment_pass_rates.append({
                    "assignment_id": str(assignment.id),
                    "assignment_title": assignment.title,
                    "pass_rate": 0.0,
                    "avg_score": 0.0,
                })
                continue

            passed_students = passed_counts.get(assignment.id, 0)
            avg_score = avg_scores.get(assignment.id, 0.0)
            pass_rate_val = round(passed_students / len(students) * 100, 1)

            assignment_pass_rates.append({
                "assignment_id": str(assignment.id),
                "assignment_title": assignment.title,
                "pass_rate": pass_rate_val,
                "avg_score": avg_score,
            })
    else:
        for assignment in assignments:
            assignment_pass_rates.append({
                "assignment_id": str(assignment.id),
                "assignment_title": assignment.title,
                "pass_rate": 0.0,
                "avg_score": 0.0,
            })

    # If student, filter to only their own data
    if user.role == "student":
        grade_data = [g for g in grade_data if g["student_id"] == str(user.id)]

    response_data = {
        "course_id": str(course.id),
        "course_name": course.name,
        "grades": grade_data,
        "statistics": stats,
        "assignment_pass_rates": assignment_pass_rates,
    }

    # Cache the grade overview for 60 seconds (only for teachers, as student data is filtered per-user)
    if user.role != "student":
        cache_key = f"grades:course:{course_id}"
        await cache_set(cache_key, response_data, ttl=60)

    return success_response(response_data)


@router.get("/courses/{course_id}/students/{student_id}")
async def get_student_grade_detail(
    course_id: str,
    student_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed grade breakdown for a specific student in a course."""
    course_id_uuid = uuid_mod.UUID(course_id)
    student_id_uuid = uuid_mod.UUID(student_id)

    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id_uuid))
    course = course_result.scalar_one_or_none()
    if not course:
        raise NotFoundError("course", course_id)

    # Check authorization: teacher of course, admin, or the student themselves
    is_teacher = course.teacher_id == user.id
    is_admin = user.role == "admin"
    is_self = user.id == student_id_uuid
    if not (is_teacher or is_admin or is_self):
        raise ForbiddenError("无权查看该学生的成绩")

    # Verify student exists and is in the course
    enrollment_result = await db.execute(
        select(CourseStudent).where(
            CourseStudent.course_id == course_id_uuid,
            CourseStudent.student_id == student_id_uuid,
        )
    )
    if not enrollment_result.scalar_one_or_none():
        raise NotFoundError("student", student_id)

    # Get student info
    student_result = await db.execute(select(User).where(User.id == student_id_uuid))
    student = student_result.scalar_one_or_none()
    if not student:
        raise NotFoundError("student", student_id)

    # Get all assignments for this course
    assignments_result = await db.execute(
        select(Assignment)
        .where(Assignment.course_id == course_id_uuid)
        .order_by(Assignment.created_at)
    )
    assignments = assignments_result.scalars().all()
    assignment_ids = [a.id for a in assignments]

    # ── Batch 1: Load all AssignmentProblems for all assignments ──
    aps_result = await db.execute(
        select(AssignmentProblem)
        .where(AssignmentProblem.assignment_id.in_(assignment_ids))
        .order_by(AssignmentProblem.order)
    )
    all_aps = aps_result.scalars().all()

    # Group by assignment
    assignment_aps_map: dict[uuid_mod.UUID, list[AssignmentProblem]] = defaultdict(list)
    problem_ids = set()
    for ap in all_aps:
        assignment_aps_map[ap.assignment_id].append(ap)
        problem_ids.add(ap.problem_id)
    problem_ids_list = list(problem_ids)

    # ── Batch 2: Load all problems ──
    problems_map: dict[uuid_mod.UUID, Problem] = {}
    if problem_ids_list:
        problems_result = await db.execute(
            select(Problem).where(Problem.id.in_(problem_ids_list))
        )
        for p in problems_result.scalars().all():
            problems_map[p.id] = p

    # ── Batch 3: Load ALL submissions for this student in this course ──
    # Process in Python: best submission = highest score, then most recent
    best_sub_map: dict[tuple[uuid_mod.UUID, uuid_mod.UUID], Submission] = {}
    if assignment_ids:
        submissions_result = await db.execute(
            select(Submission).where(
                Submission.student_id == student_id_uuid,
                Submission.assignment_id.in_(assignment_ids),
            )
        )
        for sub in submissions_result.scalars().all():
            key = (sub.assignment_id, sub.problem_id)
            existing = best_sub_map.get(key)
            if existing is None:
                best_sub_map[key] = sub
            else:
                # Higher score wins, then more recent
                if sub.score > existing.score or (
                    sub.score == existing.score
                    and sub.submitted_at > existing.submitted_at
                ):
                    best_sub_map[key] = sub

    # ── Build response in Python memory ──
    assignments_data = []
    total_score = 0.0
    max_total_score = 0.0

    for assignment in assignments:
        aps = assignment_aps_map.get(assignment.id, [])
        assignment_score = 0.0
        assignment_max_score = sum(ap.score_weight for ap in aps)
        problems_data = []

        for ap in aps:
            problem = problems_map.get(ap.problem_id)
            if not problem:
                continue

            best_sub = best_sub_map.get((assignment.id, ap.problem_id))
            problem_score = best_sub.score if best_sub else 0
            problem_status = best_sub.status if best_sub else "none"
            submitted_at = best_sub.submitted_at.isoformat() if best_sub else None
            time_used = best_sub.time_used if best_sub else None

            problems_data.append({
                "problem_id": str(problem.id),
                "title": problem.title,
                "difficulty": problem.difficulty,
                "score": problem_score,
                "max_score": ap.score_weight,
                "status": problem_status,
                "submitted_at": submitted_at,
                "time_used": time_used,
            })

            assignment_score += problem_score * ap.score_weight / 100

        assignments_data.append({
            "assignment_id": str(assignment.id),
            "title": assignment.title,
            "status": assignment.status,
            "deadline": assignment.end_time.isoformat(),
            "score": round(assignment_score, 1),
            "max_score": assignment_max_score,
            "problems": problems_data,
        })

        total_score += assignment_score
        max_total_score += assignment_max_score

    return success_response({
        "course_id": str(course.id),
        "course_name": course.name,
        "student_id": str(student.id),
        "username": student.username,
        "nickname": student.nickname,
        "assignments": assignments_data,
        "total_score": round(total_score, 1),
        "max_total_score": round(max_total_score, 1),
    })


@router.get("/courses/{course_id}/export")
async def export_grades(
    course_id: str,
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    _teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    course_id_uuid = uuid_mod.UUID(course_id)

    # Verify course
    course_result = await db.execute(select(Course).where(Course.id == course_id_uuid))
    course = course_result.scalar_one_or_none()
    if not course:
        raise NotFoundError("course", course_id)

    # Get assignments
    assignments_result = await db.execute(
        select(Assignment)
        .where(Assignment.course_id == course_id_uuid)
        .order_by(Assignment.created_at)
    )
    assignments = assignments_result.scalars().all()
    assignment_ids = [a.id for a in assignments]

    # Get students
    students_result = await db.execute(
        select(User)
        .join(CourseStudent, CourseStudent.student_id == User.id)
        .where(CourseStudent.course_id == course_id_uuid)
        .order_by(User.username)
    )
    students = students_result.scalars().all()
    student_ids = [s.id for s in students]

    # ── Batch load all AssignmentProblems ──
    aps_result = await db.execute(
        select(AssignmentProblem).where(
            AssignmentProblem.assignment_id.in_(assignment_ids)
        )
    )
    all_aps = aps_result.scalars().all()

    # Build maps
    assignment_problems_map: dict[uuid_mod.UUID, list[AssignmentProblem]] = defaultdict(list)
    problem_ids = set()
    for ap in all_aps:
        assignment_problems_map[ap.assignment_id].append(ap)
        problem_ids.add(ap.problem_id)
    problem_ids_list = list(problem_ids)

    # ── Batch load best scores for ALL students ──
    best_score_map: dict[tuple[uuid_mod.UUID, uuid_mod.UUID, uuid_mod.UUID], int] = {}
    if student_ids and problem_ids_list:
        best_scores_result = await db.execute(
            select(
                Submission.student_id,
                Submission.assignment_id,
                Submission.problem_id,
                func.max(Submission.score).label("best_score"),
            )
            .where(
                Submission.student_id.in_(student_ids),
                Submission.assignment_id.in_(assignment_ids),
                Submission.problem_id.in_(problem_ids_list),
                Submission.status == "accepted",
            )
            .group_by(
                Submission.student_id,
                Submission.assignment_id,
                Submission.problem_id,
            )
        )
        for row in best_scores_result.all():
            best_score_map[(row.student_id, row.assignment_id, row.problem_id)] = (
                row.best_score or 0
            )

    def compute_student_row(student):
        row = [student.username, student.nickname or student.username]
        total = 0.0
        for assignment in assignments:
            aps = assignment_problems_map.get(assignment.id, [])
            assignment_score = 0.0
            for ap in aps:
                best_score = best_score_map.get(
                    (student.id, assignment.id, ap.problem_id), 0
                )
                assignment_score += best_score * ap.score_weight / 100
            row.append(round(assignment_score, 1))
            total += assignment_score
        row.append(round(total, 1))
        return row

    if format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = "成绩表"

        # Header
        headers = ["学号", "姓名"] + [a.title for a in assignments] + ["总分"]
        ws.append(headers)

        for student in students:
            ws.append(compute_student_row(student))

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{quote(course.name)}_grades.xlsx"'
            },
        )
    else:
        # CSV format
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        headers = ["学号", "姓名"] + [a.title for a in assignments] + ["总分"]
        writer.writerow(headers)

        for student in students:
            writer.writerow(compute_student_row(student))

        csv_content = output.getvalue().encode("utf-8-sig")
        buffer = BytesIO(csv_content)

        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{quote(course.name)}_grades.csv"'
            },
        )


@router.get("/problems/{problem_id}/stats")
async def get_problem_stats(
    problem_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pass rate statistics for a specific problem."""
    problem_id_uuid = uuid_mod.UUID(problem_id)

    # Verify problem exists
    problem_result = await db.execute(
        select(Problem).where(Problem.id == problem_id_uuid)
    )
    problem = problem_result.scalar_one_or_none()
    if not problem:
        raise NotFoundError("problem", problem_id)

    # Total submissions
    total_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.problem_id == problem_id_uuid
        )
    )
    total_submissions = total_result.scalar() or 0

    # Accepted submissions
    accepted_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.problem_id == problem_id_uuid,
            Submission.status == "accepted",
        )
    )
    accepted_submissions = accepted_result.scalar() or 0

    # Unique students who submitted
    unique_students_result = await db.execute(
        select(func.count(func.distinct(Submission.student_id))).where(
            Submission.problem_id == problem_id_uuid
        )
    )
    unique_students = unique_students_result.scalar() or 0

    # Unique students who got accepted
    unique_accepted_result = await db.execute(
        select(func.count(func.distinct(Submission.student_id))).where(
            Submission.problem_id == problem_id_uuid,
            Submission.status == "accepted",
        )
    )
    unique_accepted = unique_accepted_result.scalar() or 0

    # Calculate rates
    pass_rate = (
        round(accepted_submissions / total_submissions * 100, 1)
        if total_submissions > 0
        else 0.0
    )
    student_pass_rate = (
        round(unique_accepted / unique_students * 100, 1)
        if unique_students > 0
        else 0.0
    )

    return success_response({
        "problem_id": problem_id,
        "total_submissions": total_submissions,
        "accepted_submissions": accepted_submissions,
        "pass_rate": pass_rate,
        "unique_students": unique_students,
        "unique_accepted": unique_accepted,
        "student_pass_rate": student_pass_rate,
    })

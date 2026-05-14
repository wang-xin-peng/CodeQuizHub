from io import BytesIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
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
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise NotFoundError("course", course_id)

    # Get all assignments for this course
    assignments_result = await db.execute(
        select(Assignment)
        .where(Assignment.course_id == course_id)
        .order_by(Assignment.created_at)
    )
    assignments = assignments_result.scalars().all()

    # Get all students in the course
    students_result = await db.execute(
        select(User)
        .join(CourseStudent, CourseStudent.student_id == User.id)
        .where(CourseStudent.course_id == course_id)
    )
    students = students_result.scalars().all()

    # For each student, get best submission score per assignment
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
            # Get all problems in this assignment
            ap_result = await db.execute(
                select(AssignmentProblem).where(
                    AssignmentProblem.assignment_id == assignment.id
                )
            )
            aps = ap_result.scalars().all()

            assignment_score = 0
            for ap in aps:
                # Get best submission for this student/problem/assignment
                best_result = await db.execute(
                    select(func.max(Submission.score)).where(
                        Submission.student_id == student.id,
                        Submission.assignment_id == assignment.id,
                        Submission.problem_id == ap.problem_id,
                        Submission.status == "accepted",
                    )
                )
                best_score = best_result.scalar() or 0
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

    # If student, filter to only their own data
    if user.role == "student":
        grade_data = [g for g in grade_data if g["student_id"] == str(user.id)]

    return success_response({
        "course_id": str(course.id),
        "course_name": course.name,
        "grades": grade_data,
        "statistics": stats,
    })


@router.get("/courses/{course_id}/export")
async def export_grades(
    course_id: str,
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    _teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    # Verify course
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise NotFoundError("course", course_id)

    # Get assignments
    assignments_result = await db.execute(
        select(Assignment)
        .where(Assignment.course_id == course_id)
        .order_by(Assignment.created_at)
    )
    assignments = assignments_result.scalars().all()

    # Get students
    students_result = await db.execute(
        select(User)
        .join(CourseStudent, CourseStudent.student_id == User.id)
        .where(CourseStudent.course_id == course_id)
        .order_by(User.username)
    )
    students = students_result.scalars().all()

    if format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = "成绩表"

        # Header
        headers = ["学号", "姓名"] + [a.title for a in assignments] + ["总分"]
        ws.append(headers)

        for student in students:
            row = [student.username, student.nickname or student.username]
            total = 0.0

            for assignment in assignments:
                ap_result = await db.execute(
                    select(AssignmentProblem).where(
                        AssignmentProblem.assignment_id == assignment.id
                    )
                )
                aps = ap_result.scalars().all()

                assignment_score = 0.0
                for ap in aps:
                    best_result = await db.execute(
                        select(func.max(Submission.score)).where(
                            Submission.student_id == student.id,
                            Submission.assignment_id == assignment.id,
                            Submission.problem_id == ap.problem_id,
                            Submission.status == "accepted",
                        )
                    )
                    best_score = best_result.scalar() or 0
                    assignment_score += best_score * ap.score_weight / 100

                row.append(round(assignment_score, 1))
                total += assignment_score

            row.append(round(total, 1))
            ws.append(row)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{course.name}_grades.xlsx"'
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
            row = [student.username, student.nickname or student.username]
            total = 0.0

            for assignment in assignments:
                ap_result = await db.execute(
                    select(AssignmentProblem).where(
                        AssignmentProblem.assignment_id == assignment.id
                    )
                )
                aps = ap_result.scalars().all()

                assignment_score = 0.0
                for ap in aps:
                    best_result = await db.execute(
                        select(func.max(Submission.score)).where(
                            Submission.student_id == student.id,
                            Submission.assignment_id == assignment.id,
                            Submission.problem_id == ap.problem_id,
                            Submission.status == "accepted",
                        )
                    )
                    best_score = best_result.scalar() or 0
                    assignment_score += best_score * ap.score_weight / 100

                row.append(round(assignment_score, 1))
                total += assignment_score

            row.append(round(total, 1))
            writer.writerow(row)

        csv_content = output.getvalue().encode("utf-8-sig")
        buffer = BytesIO(csv_content)

        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{course.name}_grades.csv"'
            },
        )

import uuid as uuid_mod
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.errors import BusinessError, NotFoundError
from app.database import get_db
from app.dependencies import get_current_user, require_teacher
from app.models.assignment import Assignment, AssignmentProblem
from app.models.course import Course, CourseStudent
from app.models.user import User
from app.schemas.assignment import AssignmentCreateRequest, AssignmentUpdateRequest
from app.schemas.response import paginated_response, success_response

router = APIRouter()


def serialize_assignment(a: Assignment) -> dict:
    return {
        "id": str(a.id),
        "course_id": str(a.course_id),
        "title": a.title,
        "description": a.description,
        "start_time": a.start_time.isoformat(),
        "end_time": a.end_time.isoformat(),
        "status": a.status,
        "created_at": a.created_at.isoformat(),
    }


@router.post("", status_code=201)
async def create_assignment(
    body: AssignmentCreateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    cid = uuid_mod.UUID(body.course_id)
    # Verify course ownership
    course_result = await db.execute(
        select(Course).where(Course.id == cid, Course.teacher_id == teacher.id)
    )
    if not course_result.scalar_one_or_none():
        raise NotFoundError("course", body.course_id)

    # Convert to UTC, then strip tzinfo for TIMESTAMP WITHOUT TIME ZONE columns
    start_time = body.start_time.astimezone(timezone.utc).replace(tzinfo=None) if body.start_time.tzinfo else body.start_time
    end_time = body.end_time.astimezone(timezone.utc).replace(tzinfo=None) if body.end_time.tzinfo else body.end_time

    if end_time <= start_time:
        raise BusinessError(ErrorCode.VALIDATION_INVALID_FORMAT, "结束时间必须晚于开始时间")

    assignment = Assignment(
        course_id=cid,
        title=body.title,
        description=body.description,
        start_time=start_time,
        end_time=end_time,
        status="draft",
    )
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)

    # Add problems to assignment
    weights = body.score_weights or [100] * len(body.problem_ids)
    for idx, (pid_str, weight) in enumerate(zip(body.problem_ids, weights)):
        ap = AssignmentProblem(
            assignment_id=assignment.id,
            problem_id=uuid_mod.UUID(pid_str),
            score_weight=weight,
            order=idx,
        )
        db.add(ap)

    await db.flush()

    return success_response(serialize_assignment(assignment))


@router.get("/{assignment_id}")
async def get_assignment(
    assignment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    aid = uuid_mod.UUID(assignment_id)
    result = await db.execute(select(Assignment).where(Assignment.id == aid))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("assignment", assignment_id)

    data = serialize_assignment(assignment)

    # Load problems in this assignment
    ap_result = await db.execute(
        select(AssignmentProblem)
        .where(AssignmentProblem.assignment_id == aid)
        .order_by(AssignmentProblem.order)
    )
    aps = ap_result.scalars().all()
    data["problems"] = [
        {
            "problem_id": str(ap.problem_id),
            "score_weight": ap.score_weight,
            "order": ap.order,
        }
        for ap in aps
    ]

    return success_response(data)


@router.put("/{assignment_id}")
async def update_assignment(
    assignment_id: str,
    body: AssignmentUpdateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    aid = uuid_mod.UUID(assignment_id)
    result = await db.execute(select(Assignment).where(Assignment.id == aid))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("assignment", assignment_id)

    # Verify course ownership
    course_result = await db.execute(
        select(Course).where(Course.id == assignment.course_id, Course.teacher_id == teacher.id)
    )
    if not course_result.scalar_one_or_none():
        raise NotFoundError("assignment", assignment_id)

    if body.title is not None:
        assignment.title = body.title
    if body.description is not None:
        assignment.description = body.description
    if body.start_time is not None:
        assignment.start_time = body.start_time.astimezone(timezone.utc).replace(tzinfo=None) if body.start_time.tzinfo else body.start_time
    if body.end_time is not None:
        assignment.end_time = body.end_time.astimezone(timezone.utc).replace(tzinfo=None) if body.end_time.tzinfo else body.end_time
    if body.status is not None:
        if body.status not in ("draft", "not_started", "ongoing", "closed", "published"):
            raise BusinessError(ErrorCode.VALIDATION_INVALID_FORMAT, "无效的作业状态")
        assignment.status = body.status

    # Update problems if provided
    if body.problem_ids is not None:
        # Remove existing problem relations
        old_aps = await db.execute(
            select(AssignmentProblem).where(AssignmentProblem.assignment_id == aid)
        )
        for ap in old_aps.scalars().all():
            await db.delete(ap)

        # Add new problem relations
        weights = body.score_weights or [100] * len(body.problem_ids)
        for idx, (pid_str, weight) in enumerate(zip(body.problem_ids, weights)):
            ap = AssignmentProblem(
                assignment_id=aid,
                problem_id=uuid_mod.UUID(pid_str),
                score_weight=weight,
                order=idx,
            )
            db.add(ap)

    # Auto-calculate status based on current time
    # Run when times are updated (even for closed assignments), or for active assignments
    if body.start_time is not None or body.end_time is not None or assignment.status not in ("draft", "closed"):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if now < assignment.start_time:
            assignment.status = "not_started"
        elif now > assignment.end_time:
            assignment.status = "closed"
        else:
            assignment.status = "ongoing"

    await db.flush()
    await db.refresh(assignment)

    return success_response(serialize_assignment(assignment))


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: str,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    aid = uuid_mod.UUID(assignment_id)
    result = await db.execute(select(Assignment).where(Assignment.id == aid))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("assignment", assignment_id)

    # Verify course ownership
    course_result = await db.execute(
        select(Course).where(Course.id == assignment.course_id, Course.teacher_id == teacher.id)
    )
    if not course_result.scalar_one_or_none():
        raise NotFoundError("assignment", assignment_id)

    await db.delete(assignment)
    await db.flush()

    return success_response(message="作业已删除")


@router.get("/course/{course_id}")
async def list_course_assignments(
    course_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cid = uuid_mod.UUID(course_id)
    # Verify access
    if user.role == "student":
        member_result = await db.execute(
            select(CourseStudent).where(
                CourseStudent.course_id == cid,
                CourseStudent.student_id == user.id,
            )
        )
        if not member_result.scalar_one_or_none():
            raise NotFoundError("course", course_id)

    query = select(Assignment).where(Assignment.course_id == cid)
    count_query = (
        select(func.count())
        .select_from(Assignment)
        .where(Assignment.course_id == cid)
    )

    # Students only see active/closed assignments (exclude draft)
    if user.role == "student":
        query = query.where(Assignment.status.in_(["published", "not_started", "ongoing", "closed"]))
        count_query = count_query.where(Assignment.status.in_(["published", "not_started", "ongoing", "closed"]))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Assignment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    assignments = result.scalars().all()

    items = [serialize_assignment(a) for a in assignments]

    return paginated_response(items, total, page, page_size)

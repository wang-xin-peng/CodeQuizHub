import secrets
import string

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.errors import BusinessError, NotFoundError
from app.database import get_db
from app.dependencies import get_current_user, require_teacher
from app.models.course import Course, CourseStudent
from app.models.user import User
from app.schemas.course import CourseCreateRequest, CourseUpdateRequest, JoinCourseRequest
from app.schemas.response import paginated_response, success_response

router = APIRouter()


def generate_invite_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.post("", status_code=201)
async def create_course(
    body: CourseCreateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    invite_code = generate_invite_code()
    # Ensure uniqueness
    while True:
        existing = await db.execute(
            select(Course).where(Course.invite_code == invite_code)
        )
        if not existing.scalar_one_or_none():
            break
        invite_code = generate_invite_code()

    course = Course(
        name=body.name,
        description=body.description,
        languages=body.languages,
        invite_code=invite_code,
        teacher_id=teacher.id,
    )
    db.add(course)
    await db.flush()
    await db.refresh(course)

    return success_response({
        "id": str(course.id),
        "name": course.name,
        "description": course.description,
        "languages": course.languages,
        "invite_code": course.invite_code,
        "status": course.status,
        "teacher_id": str(course.teacher_id),
        "created_at": course.created_at.isoformat(),
        "updated_at": course.updated_at.isoformat(),
    })


@router.get("")
async def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role in ("teacher", "admin"):
        query = select(Course).where(Course.teacher_id == user.id)
        count_query = select(func.count()).select_from(Course).where(Course.teacher_id == user.id)
    else:
        # Student: courses they joined
        query = (
            select(Course)
            .join(CourseStudent, CourseStudent.course_id == Course.id)
            .where(CourseStudent.student_id == user.id)
        )
        count_query = (
            select(func.count())
            .select_from(CourseStudent)
            .where(CourseStudent.student_id == user.id)
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Course.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    courses = result.scalars().all()

    items = [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "languages": c.languages,
            "invite_code": c.invite_code,
            "status": c.status,
            "teacher_id": str(c.teacher_id),
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in courses
    ]

    return paginated_response(items, total, page, page_size)


@router.get("/{course_id}")
async def get_course(
    course_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundError("course", course_id)

    return success_response({
        "id": str(course.id),
        "name": course.name,
        "description": course.description,
        "languages": course.languages,
        "invite_code": course.invite_code,
        "status": course.status,
        "teacher_id": str(course.teacher_id),
        "created_at": course.created_at.isoformat(),
        "updated_at": course.updated_at.isoformat(),
    })


@router.put("/{course_id}")
async def update_course(
    course_id: str,
    body: CourseUpdateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Course).where(Course.id == course_id, Course.teacher_id == teacher.id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundError("course", course_id)

    if body.name is not None:
        course.name = body.name
    if body.description is not None:
        course.description = body.description
    if body.status is not None:
        if body.status not in ("active", "archived"):
            raise BusinessError(ErrorCode.VALIDATION_INVALID_FORMAT, "无效的课程状态")
        course.status = body.status

    await db.flush()
    await db.refresh(course)

    return success_response({
        "id": str(course.id),
        "name": course.name,
        "description": course.description,
        "languages": course.languages,
        "invite_code": course.invite_code,
        "status": course.status,
        "teacher_id": str(course.teacher_id),
        "created_at": course.created_at.isoformat(),
        "updated_at": course.updated_at.isoformat(),
    })


@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Course).where(Course.id == course_id, Course.teacher_id == teacher.id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundError("course", course_id)

    course.status = "archived"
    await db.flush()

    return success_response(message="课程已归档")


@router.post("/join")
async def join_course(
    body: JoinCourseRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Course).where(Course.invite_code == body.invite_code)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise BusinessError(ErrorCode.COURSE_NOT_FOUND, "邀请码无效", 404)

    if course.status == "archived":
        raise BusinessError(ErrorCode.COURSE_ARCHIVED, "课程已归档")

    # Check if already joined
    existing = await db.execute(
        select(CourseStudent).where(
            CourseStudent.course_id == course.id,
            CourseStudent.student_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise BusinessError(ErrorCode.COURSE_ALREADY_JOINED, "已加入该课程")

    cs = CourseStudent(course_id=course.id, student_id=user.id)
    db.add(cs)
    await db.flush()

    return success_response({
        "course_id": str(course.id),
        "course_name": course.name,
        "message": "成功加入课程",
    })


@router.get("/{course_id}/students")
async def list_course_students(
    course_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if not course_result.scalar_one_or_none():
        raise NotFoundError("course", course_id)

    count_query = (
        select(func.count())
        .select_from(CourseStudent)
        .where(CourseStudent.course_id == course_id)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        select(User)
        .join(CourseStudent, CourseStudent.student_id == User.id)
        .where(CourseStudent.course_id == course_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    students = result.scalars().all()

    items = [
        {
            "id": str(s.id),
            "username": s.username,
            "email": s.email,
            "nickname": s.nickname,
        }
        for s in students
    ]

    return paginated_response(items, total, page, page_size)


@router.delete("/{course_id}/students/{student_id}")
async def remove_student(
    course_id: str,
    student_id: str,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    # Verify course belongs to teacher
    course_result = await db.execute(
        select(Course).where(Course.id == course_id, Course.teacher_id == teacher.id)
    )
    if not course_result.scalar_one_or_none():
        raise NotFoundError("course", course_id)

    result = await db.execute(
        select(CourseStudent).where(
            CourseStudent.course_id == course_id,
            CourseStudent.student_id == student_id,
        )
    )
    cs = result.scalar_one_or_none()
    if not cs:
        raise BusinessError(ErrorCode.COURSE_NOT_MEMBER, "该学生不在课程中", 404)

    await db.delete(cs)
    await db.flush()

    return success_response(message="已移除学生")


@router.delete("/{course_id}/leave")
async def leave_course(
    course_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CourseStudent).where(
            CourseStudent.course_id == course_id,
            CourseStudent.student_id == user.id,
        )
    )
    cs = result.scalar_one_or_none()
    if not cs:
        raise BusinessError(ErrorCode.COURSE_NOT_MEMBER, "未加入该课程", 404)

    await db.delete(cs)
    await db.flush()

    return success_response(message="已退出课程")

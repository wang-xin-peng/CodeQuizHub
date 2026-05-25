import asyncio
import json
import logging
import uuid as uuid_mod
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.cache import cache_delete
from app.core.error_codes import ErrorCode
from app.core.errors import BusinessError, NotFoundError
from app.database import get_db
from app.dependencies import get_current_user
from app.models.assignment import Assignment
from app.models.code_draft import CodeDraft
from app.models.problem import Problem, ProblemFunctionSignature, TestCase
from app.models.submission import Submission, SubmissionResult
from app.models.user import User
from app.schemas.response import paginated_response, success_response
from app.schemas.submission import SubmitCodeRequest

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter()


async def _invalidate_grade_cache(course_id: str):
    """Invalidate grade overview cache for a course."""
    await cache_delete(f"grades:course:{course_id}")


async def get_redis():
    try:
        return aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        logger.warning("Redis connection failed, judge queue unavailable")
        return None


async def push_to_judge_queue(submission_id: str, problem_id: str, language: str, code: str, time_limit: int, memory_limit: int):
    """Push submission to Redis judge queue. Gracefully handles Redis unavailability."""
    r = await get_redis()
    if r is None:
        logger.warning(f"Redis unavailable, submission {submission_id} will not be judged")
        return
    try:
        task = {
            "submission_id": submission_id,
            "problem_id": problem_id,
            "language": language,
            "code": code,
            "time_limit": time_limit,
            "memory_limit": memory_limit,
        }
        await r.lpush("judge_queue", json.dumps(task))
    except Exception:
        logger.exception(f"Failed to push submission {submission_id} to judge queue")
    finally:
        await r.aclose()


@router.post("", status_code=202)
async def submit_code(
    body: SubmitCodeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    aid = uuid_mod.UUID(body.assignment_id)
    pid = uuid_mod.UUID(body.problem_id)

    # Verify assignment exists and is active
    assignment_result = await db.execute(
        select(Assignment).where(Assignment.id == aid)
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("assignment", body.assignment_id)

    now = datetime.now(timezone.utc)
    if assignment.status not in ("ongoing", "published"):
        raise BusinessError(ErrorCode.ASSIGNMENT_NOT_STARTED, "作业未发布")
    if now < assignment.start_time.replace(tzinfo=timezone.utc):
        raise BusinessError(ErrorCode.ASSIGNMENT_NOT_STARTED, "作业未开始")
    if now > assignment.end_time.replace(tzinfo=timezone.utc):
        raise BusinessError(ErrorCode.ASSIGNMENT_EXPIRED, "作业已截止")

    # Verify problem exists
    problem_result = await db.execute(
        select(Problem).where(Problem.id == pid)
    )
    problem = problem_result.scalar_one_or_none()
    if not problem:
        raise NotFoundError("problem", body.problem_id)

    # Verify language is supported
    sig_result = await db.execute(
        select(ProblemFunctionSignature).where(
            ProblemFunctionSignature.problem_id == pid,
            ProblemFunctionSignature.language == body.language,
        )
    )
    if not sig_result.scalar_one_or_none():
        raise BusinessError(ErrorCode.PROBLEM_LANG_NOT_SUPPORTED, "该语言不支持")

    # Create submission
    submission = Submission(
        student_id=user.id,
        assignment_id=aid,
        problem_id=pid,
        language=body.language,
        code=body.code,
        status="pending",
    )
    db.add(submission)
    await db.flush()
    await db.refresh(submission)

    # Invalidate grade cache for this course (fire-and-forget)
    course_id = assignment.course_id
    asyncio.create_task(_invalidate_grade_cache(str(course_id)))

    # Push to Redis judge queue (fire-and-forget)
    asyncio.create_task(
        push_to_judge_queue(
            str(submission.id),
            str(pid),
            body.language,
            body.code,
            problem.time_limit,
            problem.memory_limit,
        )
    )

    return success_response({
        "submission_id": str(submission.id),
        "status": "pending",
    })


@router.get("/{submission_id}")
async def get_submission(
    submission_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sid = uuid_mod.UUID(submission_id)
    result = await db.execute(
        select(Submission).where(Submission.id == sid)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise NotFoundError("submission", submission_id)

    # Only the submitter or teacher/admin can view
    if user.role == "student" and submission.student_id != user.id:
        raise NotFoundError("submission", submission_id)

    data = {
        "id": str(submission.id),
        "student_id": str(submission.student_id),
        "problem_id": str(submission.problem_id),
        "assignment_id": str(submission.assignment_id),
        "language": submission.language,
        "code": submission.code,
        "status": submission.status,
        "score": submission.score,
        "time_used": submission.time_used,
        "memory_used": submission.memory_used,
        "error_message": submission.error_message,
        "submitted_at": submission.submitted_at.isoformat(),
    }

    # Load per-testcase results
    sr_result = await db.execute(
        select(SubmissionResult).where(SubmissionResult.submission_id == sid)
    )
    results = sr_result.scalars().all()

    # Load test cases for order and public info
    tc_result = await db.execute(
        select(TestCase)
        .where(TestCase.problem_id == submission.problem_id)
        .order_by(TestCase.order)
    )
    test_cases = tc_result.scalars().all()
    tc_map = {str(tc.id): tc for tc in test_cases}

    result_items = []
    for sr in results:
        tc = tc_map.get(str(sr.test_case_id))
        item = {
            "test_case_order": tc.order if tc else 0,
            "status": sr.status,
            "is_public": tc.is_public if tc else False,
            "time_used": sr.time_used,
            "memory_used": sr.memory_used,
        }
        # Only show input/output for public test cases
        if tc and tc.is_public:
            item["input"] = tc.input_params_json
            item["expected"] = tc.expected_output_json
            item["actual"] = sr.actual_output
        else:
            item["input"] = None
            item["expected"] = None
            item["actual"] = None
        result_items.append(item)

    result_items.sort(key=lambda x: x["test_case_order"])
    data["results"] = result_items

    return success_response(data)


@router.get("/assignment/{assignment_id}")
async def list_assignment_submissions(
    assignment_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    aid = uuid_mod.UUID(assignment_id)
    query = select(Submission).where(Submission.assignment_id == aid)

    # Students only see their own submissions
    if user.role == "student":
        query = query.where(Submission.student_id == user.id)

    count_query = select(func.count()).select_from(Submission).where(Submission.assignment_id == aid)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Submission.submitted_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    submissions = result.scalars().all()

    items = [
        {
            "id": str(s.id),
            "student_id": str(s.student_id),
            "problem_id": str(s.problem_id),
            "language": s.language,
            "status": s.status,
            "score": s.score,
            "submitted_at": s.submitted_at.isoformat(),
        }
        for s in submissions
    ]

    return paginated_response(items, total, page, page_size)


# WebSocket for real-time submission status
@router.websocket("/ws/{submission_id}")
async def submission_websocket(websocket: WebSocket, submission_id: str):
    await websocket.accept()
    r = await get_redis()

    if r is None:
        await websocket.send_json({"status": "pending", "error": "Judge service unavailable"})
        await websocket.close()
        return

    try:
        terminal_statuses = {
            "accepted", "wrong_answer", "time_limit_exceeded",
            "memory_limit_exceeded", "runtime_error", "compilation_error",
        }

        while True:
            status = await r.get(f"submission:{submission_id}:status")
            if status:
                await websocket.send_json({"status": status})
                if status in terminal_statuses:
                    break
            else:
                await websocket.send_json({"status": "pending"})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception(f"WebSocket error for submission {submission_id}")
    finally:
        await r.aclose()
        await websocket.close()


# Code draft (auto-save)
@router.put("/drafts")
async def save_draft(
    problem_id: str = Query(...),
    assignment_id: str = Query(...),
    language: str = Query(...),
    code: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pid = uuid_mod.UUID(problem_id)
    aid = uuid_mod.UUID(assignment_id)

    result = await db.execute(
        select(CodeDraft).where(
            CodeDraft.student_id == user.id,
            CodeDraft.problem_id == pid,
            CodeDraft.assignment_id == aid,
            CodeDraft.language == language,
        )
    )
    draft = result.scalar_one_or_none()

    if draft:
        draft.code = code
    else:
        draft = CodeDraft(
            student_id=user.id,
            problem_id=pid,
            assignment_id=aid,
            language=language,
            code=code,
        )
        db.add(draft)

    await db.flush()
    return success_response(message="草稿已保存")


@router.get("/drafts/{problem_id}")
async def get_draft(
    problem_id: str,
    assignment_id: str = Query(...),
    language: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pid = uuid_mod.UUID(problem_id)
    aid = uuid_mod.UUID(assignment_id)

    result = await db.execute(
        select(CodeDraft).where(
            CodeDraft.student_id == user.id,
            CodeDraft.problem_id == pid,
            CodeDraft.assignment_id == aid,
            CodeDraft.language == language,
        )
    )
    draft = result.scalar_one_or_none()

    if not draft:
        return success_response({"code": None})

    return success_response({"code": draft.code})

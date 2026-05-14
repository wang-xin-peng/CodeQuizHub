from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.database import get_db
from app.dependencies import get_current_user, require_teacher
from app.models.problem import Problem, ProblemFunctionSignature, TestCase
from app.models.user import User
from app.schemas.problem import (
    ProblemCreateRequest,
    ProblemUpdateRequest,
    SignatureCreateRequest,
    TestCaseCreateRequest,
)
from app.schemas.response import paginated_response, success_response

router = APIRouter()


def serialize_problem(p: Problem) -> dict:
    return {
        "id": str(p.id),
        "title": p.title,
        "description": p.description,
        "difficulty": p.difficulty,
        "time_limit": p.time_limit,
        "memory_limit": p.memory_limit,
        "tags": p.tags or [],
        "compare_mode": p.compare_mode,
        "teacher_id": str(p.teacher_id),
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@router.post("", status_code=201)
async def create_problem(
    body: ProblemCreateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    problem = Problem(
        title=body.title,
        description=body.description,
        difficulty=body.difficulty,
        time_limit=body.time_limit,
        memory_limit=body.memory_limit,
        tags=body.tags,
        compare_mode=body.compare_mode,
        teacher_id=teacher.id,
    )
    db.add(problem)
    await db.flush()
    await db.refresh(problem)

    # Create function signatures
    for idx, sig in enumerate(body.signatures):
        signature = ProblemFunctionSignature(
            problem_id=problem.id,
            language=sig.language,
            function_name=sig.function_name,
            parameters_json=[p.model_dump() for p in sig.parameters],
            return_type=sig.return_type,
            code_template=sig.code_template,
            prelude_code=sig.prelude_code,
            driver_template=sig.driver_template,
        )
        db.add(signature)

    # Create test cases
    for idx, tc in enumerate(body.test_cases):
        test_case = TestCase(
            problem_id=problem.id,
            input_params_json=tc.input_params,
            expected_output_json=tc.expected_output,
            is_public=tc.is_public,
            order=idx,
            description=tc.description,
        )
        db.add(test_case)

    await db.flush()

    return success_response(serialize_problem(problem))


@router.get("")
async def list_problems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    difficulty: str | None = None,
    language: str | None = None,
    tag: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Problem)
    count_query = select(func.count()).select_from(Problem)

    # Teachers only see their own problems
    if user.role == "teacher":
        query = query.where(Problem.teacher_id == user.id)
        count_query = count_query.where(Problem.teacher_id == user.id)

    if difficulty:
        query = query.where(Problem.difficulty == difficulty)
        count_query = count_query.where(Problem.difficulty == difficulty)

    if tag:
        query = query.where(Problem.tags.contains([tag]))
        count_query = count_query.where(Problem.tags.contains([tag]))

    if language:
        # Filter problems that have a signature for the given language
        query = query.where(
            Problem.id.in_(
                select(ProblemFunctionSignature.problem_id).where(
                    ProblemFunctionSignature.language == language
                )
            )
        )
        count_query = count_query.where(
            Problem.id.in_(
                select(ProblemFunctionSignature.problem_id).where(
                    ProblemFunctionSignature.language == language
                )
            )
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Problem.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    problems = result.scalars().all()

    items = [serialize_problem(p) for p in problems]

    return paginated_response(items, total, page, page_size)


@router.get("/{problem_id}")
async def get_problem(
    problem_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()
    if not problem:
        raise NotFoundError("problem", problem_id)

    data = serialize_problem(problem)

    # Load signatures
    sig_result = await db.execute(
        select(ProblemFunctionSignature).where(
            ProblemFunctionSignature.problem_id == problem_id
        )
    )
    signatures = sig_result.scalars().all()
    data["signatures"] = [
        {
            "id": str(s.id),
            "language": s.language,
            "function_name": s.function_name,
            "parameters_json": s.parameters_json,
            "return_type": s.return_type,
            "code_template": s.code_template,
            "prelude_code": s.prelude_code,
        }
        for s in signatures
    ]

    # Load test cases
    tc_result = await db.execute(
        select(TestCase)
        .where(TestCase.problem_id == problem_id)
        .order_by(TestCase.order)
    )
    test_cases = tc_result.scalars().all()

    if user.role in ("teacher", "admin"):
        # Teachers see all test cases
        data["test_cases"] = [
            {
                "id": str(tc.id),
                "input_params_json": tc.input_params_json,
                "expected_output_json": tc.expected_output_json,
                "is_public": tc.is_public,
                "order": tc.order,
                "description": tc.description,
            }
            for tc in test_cases
        ]
    else:
        # Students only see public test cases
        data["test_cases"] = [
            {
                "id": str(tc.id),
                "input_params_json": tc.input_params_json,
                "expected_output_json": tc.expected_output_json,
                "is_public": tc.is_public,
                "order": tc.order,
                "description": tc.description,
            }
            for tc in test_cases
            if tc.is_public
        ]

    return success_response(data)


@router.put("/{problem_id}")
async def update_problem(
    problem_id: str,
    body: ProblemUpdateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id, Problem.teacher_id == teacher.id)
    )
    problem = result.scalar_one_or_none()
    if not problem:
        raise NotFoundError("problem", problem_id)

    if body.title is not None:
        problem.title = body.title
    if body.description is not None:
        problem.description = body.description
    if body.difficulty is not None:
        problem.difficulty = body.difficulty
    if body.time_limit is not None:
        problem.time_limit = body.time_limit
    if body.memory_limit is not None:
        problem.memory_limit = body.memory_limit
    if body.tags is not None:
        problem.tags = body.tags
    if body.compare_mode is not None:
        problem.compare_mode = body.compare_mode

    await db.flush()
    await db.refresh(problem)

    return success_response(serialize_problem(problem))


@router.delete("/{problem_id}")
async def delete_problem(
    problem_id: str,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id, Problem.teacher_id == teacher.id)
    )
    problem = result.scalar_one_or_none()
    if not problem:
        raise NotFoundError("problem", problem_id)

    await db.delete(problem)
    await db.flush()

    return success_response(message="题目已删除")


# Signature management
@router.post("/{problem_id}/signatures")
async def upsert_signature(
    problem_id: str,
    body: SignatureCreateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    # Verify problem ownership
    problem_result = await db.execute(
        select(Problem).where(Problem.id == problem_id, Problem.teacher_id == teacher.id)
    )
    if not problem_result.scalar_one_or_none():
        raise NotFoundError("problem", problem_id)

    # Check if signature for this language exists
    existing_result = await db.execute(
        select(ProblemFunctionSignature).where(
            ProblemFunctionSignature.problem_id == problem_id,
            ProblemFunctionSignature.language == body.language,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.function_name = body.function_name
        existing.parameters_json = [p.model_dump() for p in body.parameters]
        existing.return_type = body.return_type
        existing.code_template = body.code_template
        existing.prelude_code = body.prelude_code
        existing.driver_template = body.driver_template
    else:
        sig = ProblemFunctionSignature(
            problem_id=problem_id,
            language=body.language,
            function_name=body.function_name,
            parameters_json=[p.model_dump() for p in body.parameters],
            return_type=body.return_type,
            code_template=body.code_template,
            prelude_code=body.prelude_code,
            driver_template=body.driver_template,
        )
        db.add(sig)

    await db.flush()
    return success_response(message="函数签名已保存")


@router.get("/{problem_id}/signatures/{language}")
async def get_signature(
    problem_id: str,
    language: str,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProblemFunctionSignature).where(
            ProblemFunctionSignature.problem_id == problem_id,
            ProblemFunctionSignature.language == language,
        )
    )
    sig = result.scalar_one_or_none()
    if not sig:
        raise NotFoundError("signature", f"{problem_id}/{language}")

    return success_response({
        "id": str(sig.id),
        "language": sig.language,
        "function_name": sig.function_name,
        "parameters_json": sig.parameters_json,
        "return_type": sig.return_type,
        "code_template": sig.code_template,
        "prelude_code": sig.prelude_code,
    })


# Test case management
@router.post("/{problem_id}/testcases")
async def add_test_case(
    problem_id: str,
    body: TestCaseCreateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    problem_result = await db.execute(
        select(Problem).where(Problem.id == problem_id, Problem.teacher_id == teacher.id)
    )
    if not problem_result.scalar_one_or_none():
        raise NotFoundError("problem", problem_id)

    # Get next order
    max_order_result = await db.execute(
        select(func.max(TestCase.order)).where(TestCase.problem_id == problem_id)
    )
    max_order = max_order_result.scalar() or -1

    tc = TestCase(
        problem_id=problem_id,
        input_params_json=body.input_params,
        expected_output_json=body.expected_output,
        is_public=body.is_public,
        order=max_order + 1,
        description=body.description,
    )
    db.add(tc)
    await db.flush()
    await db.refresh(tc)

    return success_response({
        "id": str(tc.id),
        "order": tc.order,
        "is_public": tc.is_public,
    })


@router.put("/{problem_id}/testcases/{tc_id}")
async def update_test_case(
    problem_id: str,
    tc_id: str,
    body: TestCaseCreateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    problem_result = await db.execute(
        select(Problem).where(Problem.id == problem_id, Problem.teacher_id == teacher.id)
    )
    if not problem_result.scalar_one_or_none():
        raise NotFoundError("problem", problem_id)

    tc_result = await db.execute(select(TestCase).where(TestCase.id == tc_id))
    tc = tc_result.scalar_one_or_none()
    if not tc:
        raise NotFoundError("test_case", tc_id)

    tc.input_params_json = body.input_params
    tc.expected_output_json = body.expected_output
    tc.is_public = body.is_public
    tc.description = body.description
    await db.flush()

    return success_response(message="测试用例已更新")


@router.delete("/{problem_id}/testcases/{tc_id}")
async def delete_test_case(
    problem_id: str,
    tc_id: str,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    problem_result = await db.execute(
        select(Problem).where(Problem.id == problem_id, Problem.teacher_id == teacher.id)
    )
    if not problem_result.scalar_one_or_none():
        raise NotFoundError("problem", problem_id)

    tc_result = await db.execute(select(TestCase).where(TestCase.id == tc_id))
    tc = tc_result.scalar_one_or_none()
    if not tc:
        raise NotFoundError("test_case", tc_id)

    await db.delete(tc)
    await db.flush()

    return success_response(message="测试用例已删除")

import uuid as uuid_mod

from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.errors import BusinessError, NotFoundError
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
from app.utils.code_template import generate_code_template

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
    for sig in body.signatures:
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
    page_size: int = Query(20, ge=1, le=1000),
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
        # Use string cast + contains for cross-database compatibility (SQLite + PostgreSQL)
        tag_filter = cast(Problem.tags, String).contains(f'"{tag}"')
        query = query.where(tag_filter)
        count_query = count_query.where(tag_filter)

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
    pid = uuid_mod.UUID(problem_id)
    result = await db.execute(select(Problem).where(Problem.id == pid))
    problem = result.scalar_one_or_none()
    if not problem:
        raise NotFoundError("problem", problem_id)

    data = serialize_problem(problem)

    # Load signatures
    sig_result = await db.execute(
        select(ProblemFunctionSignature).where(
            ProblemFunctionSignature.problem_id == pid
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
        .where(TestCase.problem_id == pid)
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
    pid = uuid_mod.UUID(problem_id)
    result = await db.execute(
        select(Problem).where(Problem.id == pid, Problem.teacher_id == teacher.id)
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
    pid = uuid_mod.UUID(problem_id)
    result = await db.execute(
        select(Problem).where(Problem.id == pid, Problem.teacher_id == teacher.id)
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
    pid = uuid_mod.UUID(problem_id)
    # Verify problem ownership
    problem_result = await db.execute(
        select(Problem).where(Problem.id == pid, Problem.teacher_id == teacher.id)
    )
    if not problem_result.scalar_one_or_none():
        raise NotFoundError("problem", problem_id)

    # Check if signature for this language exists
    existing_result = await db.execute(
        select(ProblemFunctionSignature).where(
            ProblemFunctionSignature.problem_id == pid,
            ProblemFunctionSignature.language == body.language,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.function_name = body.function_name
        existing.parameters_json = [p.model_dump() for p in body.parameters]
        existing.return_type = body.return_type
        existing.code_template = body.code_template or generate_code_template(
            language=body.language,
            function_name=body.function_name,
            parameters=[p.model_dump() for p in body.parameters],
            return_type=body.return_type,
        )
        existing.prelude_code = body.prelude_code
        existing.driver_template = body.driver_template
    else:
        sig = ProblemFunctionSignature(
            problem_id=pid,
            language=body.language,
            function_name=body.function_name,
            parameters_json=[p.model_dump() for p in body.parameters],
            return_type=body.return_type,
            code_template=body.code_template or generate_code_template(
                language=body.language,
                function_name=body.function_name,
                parameters=[p.model_dump() for p in body.parameters],
                return_type=body.return_type,
            ),
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
    pid = uuid_mod.UUID(problem_id)
    result = await db.execute(
        select(ProblemFunctionSignature).where(
            ProblemFunctionSignature.problem_id == pid,
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
    pid = uuid_mod.UUID(problem_id)
    problem_result = await db.execute(
        select(Problem).where(Problem.id == pid, Problem.teacher_id == teacher.id)
    )
    if not problem_result.scalar_one_or_none():
        raise NotFoundError("problem", problem_id)

    # Get next order
    max_order_result = await db.execute(
        select(func.max(TestCase.order)).where(TestCase.problem_id == pid)
    )
    max_order = max_order_result.scalar() or -1

    tc = TestCase(
        problem_id=pid,
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
    pid = uuid_mod.UUID(problem_id)
    tid = uuid_mod.UUID(tc_id)
    problem_result = await db.execute(
        select(Problem).where(Problem.id == pid, Problem.teacher_id == teacher.id)
    )
    if not problem_result.scalar_one_or_none():
        raise NotFoundError("problem", problem_id)

    tc_result = await db.execute(select(TestCase).where(TestCase.id == tid))
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
    pid = uuid_mod.UUID(problem_id)
    tid = uuid_mod.UUID(tc_id)
    problem_result = await db.execute(
        select(Problem).where(Problem.id == pid, Problem.teacher_id == teacher.id)
    )
    if not problem_result.scalar_one_or_none():
        raise NotFoundError("problem", problem_id)

    tc_result = await db.execute(select(TestCase).where(TestCase.id == tid))
    tc = tc_result.scalar_one_or_none()
    if not tc:
        raise NotFoundError("test_case", tc_id)

    await db.delete(tc)
    await db.flush()

    return success_response(message="测试用例已删除")


# Code execution
import asyncio
import json as json_mod
import subprocess
import traceback

from pydantic import BaseModel, Field


class RunCodeRequest(BaseModel):
    language: str = Field(..., max_length=20)
    code: str = Field(..., min_length=1)
    assignment_id: str


class RunCustomRequest(BaseModel):
    language: str = Field(..., max_length=20)
    code: str = Field(..., min_length=1)
    assignment_id: str
    custom_input: dict


def _build_python_driver(function_name: str, parameters: list[dict], code: str, input_data: dict) -> str:
    """Build a complete Python script with test harness."""
    param_names = [p["name"] for p in parameters]
    args = ", ".join(f'"{k}": __input["{k}"]' for k in input_data)
    driver = f'''
import json
import sys

{code}

if __name__ == "__main__":
    __input = json.loads(sys.stdin.read())
    __result = {function_name}(**{{ {args} }})
    print(json.dumps(__result))
'''
    return driver


async def _run_python_async(code: str, input_str: str, time_limit_ms: int) -> tuple[str | None, str | None, int]:
    """Execute Python code using subprocess in thread pool (async-safe)."""
    loop = asyncio.get_running_loop()
    timeout = time_limit_ms / 1000.0 + 2

    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "python", "-c", code,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=5,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(input=input_str.encode()),
            timeout=timeout,
        )
        return stdout_bytes.decode().strip(), stderr_bytes.decode().strip(), proc.returncode or 0
    except asyncio.TimeoutError:
        return None, "Time limit exceeded", -1
    except Exception:
        return None, traceback.format_exc(), -1


@router.post("/{problem_id}/run")
async def run_code(
    problem_id: str,
    body: RunCodeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pid = uuid_mod.UUID(problem_id)
    problem_result = await db.execute(select(Problem).where(Problem.id == pid))
    problem = problem_result.scalar_one_or_none()
    if not problem:
        raise NotFoundError("problem", problem_id)

    if body.language != "python":
        return success_response({
            "results": [],
            "compile_error": f"Language '{body.language}' requires full judge service. Only Python is supported for lightweight execution.",
        })

    sig_result = await db.execute(
        select(ProblemFunctionSignature).where(
            ProblemFunctionSignature.problem_id == pid,
            ProblemFunctionSignature.language == body.language,
        )
    )
    sig = sig_result.scalar_one_or_none()
    if not sig:
        raise BusinessError(ErrorCode.PROBLEM_LANG_NOT_SUPPORTED, "该语言不支持")

    tc_result = await db.execute(
        select(TestCase)
        .where(TestCase.problem_id == pid, TestCase.is_public == True)
        .order_by(TestCase.order)
    )
    test_cases = tc_result.scalars().all()

    results = []
    compile_error = None
    full_code = _build_python_driver(
        sig.function_name,
        sig.parameters_json if isinstance(sig.parameters_json, list) else [],
        body.code,
        test_cases[0].input_params_json if test_cases else {},
    )

    for tc in test_cases:
        input_json = json_mod.dumps(tc.input_params_json)
        stdout, stderr, exit_code = await _run_python_async(full_code, input_json, problem.time_limit)

        if exit_code != 0 and stderr:
            compile_error = stderr
            break

        result = {
            "test_case_order": tc.order,
            "status": "accepted",
            "is_public": tc.is_public,
            "input": tc.input_params_json,
            "expected": tc.expected_output_json,
            "actual": None,
            "time_used": 0,
            "memory_used": 0,
        }

        if exit_code != 0:
            result["status"] = "runtime_error"
        elif stdout is not None:
            try:
                actual = json_mod.loads(stdout)
            except json_mod.JSONDecodeError:
                actual = stdout
            result["actual"] = actual
            expected = tc.expected_output_json
            if actual != expected:
                result["status"] = "wrong_answer"
        else:
            result["status"] = "time_limit_exceeded"

        results.append(result)

    return success_response({"results": results, "compile_error": compile_error})


@router.post("/{problem_id}/run-custom")
async def run_custom_code(
    problem_id: str,
    body: RunCustomRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pid = uuid_mod.UUID(problem_id)
    problem_result = await db.execute(select(Problem).where(Problem.id == pid))
    problem = problem_result.scalar_one_or_none()
    if not problem:
        raise NotFoundError("problem", problem_id)

    sig_result = await db.execute(
        select(ProblemFunctionSignature).where(
            ProblemFunctionSignature.problem_id == pid,
            ProblemFunctionSignature.language == body.language,
        )
    )
    sig = sig_result.scalar_one_or_none()
    if not sig:
        raise BusinessError(ErrorCode.PROBLEM_LANG_NOT_SUPPORTED, "该语言不支持")

    if body.language != "python":
        return success_response({
            "output": "Language not supported for custom run. Only Python is available.",
            "error": None,
        })

    full_code = _build_python_driver(
        sig.function_name,
        sig.parameters_json if isinstance(sig.parameters_json, list) else [],
        body.code,
        body.custom_input,
    )
    input_json = json_mod.dumps(body.custom_input)
    stdout, stderr, exit_code = await _run_python_async(full_code, input_json, problem.time_limit)

    return success_response({
        "output": stdout,
        "error": stderr if exit_code != 0 else None,
    })

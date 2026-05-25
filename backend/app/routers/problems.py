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
    languages: str | None = Query(None, description="Comma-separated language codes"),
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

    if languages:
        # Filter problems that have a signature for ANY of the given languages
        lang_list = [l.strip() for l in languages.split(",") if l.strip()]
        if lang_list:
            query = query.where(
                Problem.id.in_(
                    select(ProblemFunctionSignature.problem_id).where(
                        ProblemFunctionSignature.language.in_(lang_list)
                    )
                )
            )
            count_query = count_query.where(
                Problem.id.in_(
                    select(ProblemFunctionSignature.problem_id).where(
                        ProblemFunctionSignature.language.in_(lang_list)
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
            "driver_template": s.driver_template,
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

    # Replace signatures if provided
    if body.signatures is not None:
        old_sigs = await db.execute(
            select(ProblemFunctionSignature).where(
                ProblemFunctionSignature.problem_id == pid
            )
        )
        for s in old_sigs.scalars().all():
            await db.delete(s)

        for sig in body.signatures:
            new_sig = ProblemFunctionSignature(
                problem_id=pid,
                language=sig.language,
                function_name=sig.function_name,
                parameters_json=[p.model_dump() for p in sig.parameters],
                return_type=sig.return_type,
                code_template=sig.code_template or (
                    generate_code_template(
                        language=sig.language,
                        function_name=sig.function_name,
                        parameters=[p.model_dump() for p in sig.parameters],
                        return_type=sig.return_type,
                    ) if sig.language else ""
                ),
                prelude_code=sig.prelude_code,
                driver_template=sig.driver_template,
            )
            db.add(new_sig)

    # Replace test cases if provided
    if body.test_cases is not None:
        old_tcs = await db.execute(
            select(TestCase).where(TestCase.problem_id == pid)
        )
        for tc in old_tcs.scalars().all():
            await db.delete(tc)

        for idx, tc in enumerate(body.test_cases):
            new_tc = TestCase(
                problem_id=pid,
                input_params_json=tc.input_params,
                expected_output_json=tc.expected_output,
                is_public=tc.is_public,
                order=idx,
                description=tc.description,
            )
            db.add(new_tc)

    await db.flush()
    await db.refresh(problem)

    # Build full response with signatures and test cases
    data = serialize_problem(problem)

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
            "driver_template": s.driver_template,
        }
        for s in signatures
    ]

    tc_result = await db.execute(
        select(TestCase)
        .where(TestCase.problem_id == pid)
        .order_by(TestCase.order)
    )
    test_cases = tc_result.scalars().all()
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

    return success_response(data)


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
        existing.code_template = body.code_template or (
            generate_code_template(
                language=body.language,
                function_name=body.function_name,
                parameters=[p.model_dump() for p in body.parameters],
                return_type=body.return_type,
            ) if body.language else ""
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
            code_template=body.code_template or (
                generate_code_template(
                    language=body.language,
                    function_name=body.function_name,
                    parameters=[p.model_dump() for p in body.parameters],
                    return_type=body.return_type,
                ) if body.language else ""
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
import io
import json as json_mod
import os
import subprocess
import tarfile
import time
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


# ── Docker execution config per language ──

_DOCKER_IMAGE_MAP = {
    "python": "codequizhub-sandbox-python",
    "java": "codequizhub-sandbox-java",
    "c": "codequizhub-sandbox-c",
    "cpp": "codequizhub-sandbox-cpp",
}

_DOCKER_COMPILE_MAP = {
    "python": None,
    "java": "javac -cp .:json.jar Solution.java",
    "c": "gcc -o solution solution.c -I/usr/include/cjson -lcjson -lm",
    "cpp": "g++ -o solution solution.cpp -std=c++17 -O2",
}

_DOCKER_RUN_MAP = {
    "python": "python3 solution.py",
    "java": "java -cp .:json.jar Main",
    "c": "./solution",
    "cpp": "./solution",
}

_DOCKER_SOURCE_MAP = {
    "python": "solution.py",
    "java": "Solution.java",
    "c": "solution.c",
    "cpp": "solution.cpp",
}


def _generate_driver(language: str, function_name: str, parameters: list[dict], input_data: dict, user_code: str, return_type: str = "int", prelude_code: str = "") -> str:
    """Generate a complete runnable program for the given language."""
    param_names = [p["name"] for p in parameters]
    prelude_block = f"\n// === Prelude ===\n{prelude_code}\n" if prelude_code else ""

    if language == "python":
        full_code = user_code
        if prelude_code:
            full_code = f"# === Prelude ===\n{prelude_code}\n\n{user_code}"
        return _build_python_driver(function_name, parameters, full_code, input_data)

    elif language == "cpp":
        # Build argument-reading expressions for each parameter
        reads = []
        call_args = []
        for p in parameters:
            name = p["name"]
            raw_type = p.get("type", "int")
            # Strip reference (&), const, and pointer (*) qualifiers for type matching
            ptype = raw_type.replace("&", "").replace("const", "").replace("*", "").replace(" ", "")
            if ptype == "int":
                reads.append(f'    int {name} = input["{name}"];')
                call_args.append(name)
            elif ptype in ("int[]", "vector<int>"):
                reads.append(f'    vector<int> {name} = input["{name}"].get<vector<int>>();')
                call_args.append(name)
            elif ptype == "string" or ptype == "String":
                reads.append(f'    string {name} = input["{name}"];')
                call_args.append(name)
            elif ptype == "vector<vector<int>>":
                reads.append(f'    auto {name} = input["{name}"].get<vector<vector<int>>>();')
                call_args.append(name)
            else:
                reads.append(f'    auto {name} = input["{name}"];')
                call_args.append(name)

        read_block = "\n".join(reads)
        args_str = ", ".join(call_args)

        # Auto-detect whether user code wraps the solution in `class Solution { ... }`.
        # If it does, call via `Solution sol; sol.functionName(args)`.
        # Otherwise, call the standalone function directly (backward compat).
        has_class_solution = "class Solution" in user_code
        if has_class_solution:
            call_line = f'    Solution sol;\n    auto result = sol.{function_name}({args_str});'
        else:
            call_line = f'    auto result = {function_name}({args_str});'

        return f'''#include <iostream>
#include <string>
#include <vector>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using namespace std;
{prelude_block}
{user_code}

int main(int argc, char* argv[]) {{
    if (argc < 2) return 1;
    json input = json::parse(argv[1]);

{read_block}

{call_line}
    cout << json(result).dump() << endl;
    return 0;
}}
'''

    elif language == "java":
        parse_lines = []
        call_args = []
        for p in parameters:
            name = p["name"]
            ptype = p.get("type", "int")
            if ptype == "int":
                parse_lines.append(f'        int {name} = input.getInt("{name}");')
                call_args.append(name)
            elif ptype in ("int[]", "vector<int>"):
                parse_lines.append(f'        org.json.JSONArray arr_{name} = input.getJSONArray("{name}");')
                parse_lines.append(f'        int[] {name} = new int[arr_{name}.length()];')
                parse_lines.append(f'        for(int i=0;i<arr_{name}.length();i++) {name}[i]=arr_{name}.getInt(i);')
                call_args.append(name)
            elif ptype == "String":
                parse_lines.append(f'        String {name} = input.getString("{name}");')
                call_args.append(name)
            else:
                parse_lines.append(f'        // TODO: parse {name} of type {ptype}')
                call_args.append(name)

        args_str = ", ".join(call_args)
        parse_block = "\n".join(parse_lines)

        return f'''import org.json.*;
import java.util.*;
{prelude_block}
class Main {{
    public static void main(String[] args) throws Exception {{
        JSONObject input = new JSONObject(args[0]);
{parse_block}
        Solution sol = new Solution();
        Object result = sol.{function_name}({args_str});
        if (result instanceof int[]) {{
            System.out.println(new JSONArray((int[])result).toString());
        }} else {{
            System.out.println(new JSONObject().put("result", result).get("result"));
        }}
    }}
}}

{user_code}
'''

    elif language == "c":
        reads = []
        call_args = []
        cleanup = []
        output_size_var = None

        for p in parameters:
            name = p["name"]
            raw_type = (p.get("type") or "int").strip()

            if raw_type == "int":
                if name in input_data:
                    reads.append(f'    int {name} = cJSON_GetObjectItem(input, "{name}")->valueint;')
                else:
                    # Derived param (e.g., numsSize from array nums in input_data)
                    found = False
                    for ap in parameters:
                        if ap["name"] != name and ap["name"] in input_data and ap.get("type", "").strip() in ("int*", "int[]"):
                            base = ap["name"]
                            if name in (base + "Size", base + "_size", base + "Len", base + "_len"):
                                reads.append(f'    int {name} = {base}_size;')
                                found = True
                                break
                    if not found:
                        reads.append(f'    int {name} = 0; /* unhandled */')
                call_args.append(name)

            elif raw_type in ("int*", "int[]"):
                if name in input_data:
                    reads.append(f'    cJSON *{name}_json = cJSON_GetObjectItem(input, "{name}");')
                    reads.append(f'    int {name}_size = cJSON_GetArraySize({name}_json);')
                    reads.append(f'    int* {name} = (int*)malloc({name}_size * sizeof(int));')
                    reads.append(f'    for (int i = 0; i < {name}_size; i++) {{')
                    reads.append(f'        {name}[i] = cJSON_GetArrayItem({name}_json, i)->valueint;')
                    reads.append(f'    }}')
                    call_args.append(name)
                    cleanup.append(f'    free({name});')
                else:
                    # Output parameter (e.g., int* returnSize)
                    reads.append(f'    int {name}_val;')
                    call_args.append(f'&{name}_val')
                    output_size_var = f'{name}_val'

            elif raw_type in ("char*", "char[]", "String", "str"):
                reads.append(f'    char* {name} = cJSON_GetObjectItem(input, "{name}")->valuestring;')
                call_args.append(name)

            elif raw_type in ("int**", "int[][]"):
                reads.append(f'    cJSON *{name}_json = cJSON_GetObjectItem(input, "{name}");')
                reads.append(f'    int {name}_rows = cJSON_GetArraySize({name}_json);')
                reads.append(f'    int** {name} = (int**)malloc({name}_rows * sizeof(int*));')
                reads.append(f'    for (int i = 0; i < {name}_rows; i++) {{')
                reads.append(f'        cJSON *row = cJSON_GetArrayItem({name}_json, i);')
                reads.append(f'        int cols = cJSON_GetArraySize(row);')
                reads.append(f'        {name}[i] = (int*)malloc(cols * sizeof(int));')
                reads.append(f'        for (int j = 0; j < cols; j++) {{')
                reads.append(f'            {name}[i][j] = cJSON_GetArrayItem(row, j)->valueint;')
                reads.append(f'        }}')
                reads.append(f'    }}')
                call_args.append(name)
                cleanup.append(f'    for (int i = 0; i < {name}_rows; i++) free({name}[i]);')
                cleanup.append(f'    free({name});')

            elif raw_type in ("float", "double"):
                reads.append(f'    {raw_type} {name} = cJSON_GetObjectItem(input, "{name}")->valuedouble;')
                call_args.append(name)

            elif raw_type == "bool":
                reads.append(f'    int {name} = cJSON_GetObjectItem(input, "{name}")->valueint;')
                call_args.append(name)

            else:
                reads.append(f'    // TODO: parse {name} of type {raw_type}')
                call_args.append(name)

        read_block = "\n".join(reads)
        args_str = ", ".join(call_args)

        ret = (return_type or "int").strip()

        if ret == "void":
            output_block = f'    {function_name}({args_str});'
        elif ret == "int":
            output_block = f'''    int result = {function_name}({args_str});
    printf("%d", result);'''
        elif ret == "bool":
            output_block = f'''    int result = {function_name}({args_str});
    printf("%s", result ? "true" : "false");'''
        elif ret in ("int*", "int[]"):
            if output_size_var:
                output_block = f'''    int* result = {function_name}({args_str});
    if (result != NULL && {output_size_var} > 0) {{
        printf("[");
        for (int i = 0; i < {output_size_var}; i++) {{
            printf("%d%s", result[i], i < {output_size_var} - 1 ? "," : "");
        }}
        printf("]");
    }} else {{
        printf("[]");
    }}'''
                cleanup.append('    if (result) free(result);')
            else:
                output_block = f'''    int* result = {function_name}({args_str});
    if (result != NULL) {{
        fprintf(stderr, "ERROR: int* return type requires a returnSize parameter in the function signature for proper array output");
        free(result);
        return 1;
    }} else {{
        printf("[]");
    }}'''
        elif ret in ("char*", "char[]"):
            output_block = f'''    char* result = {function_name}({args_str});
    printf("%s", result != NULL ? result : "null");'''
        elif ret in ("float", "double"):
            output_block = f'''    {ret} result = {function_name}({args_str});
    printf("%g", result);'''
        elif ret in ("int**", "int[][]"):
            output_block = f'''    // TODO: 2D array return printing
    int** result = {function_name}({args_str});
    printf("[]");
    free(result);'''
        else:
            output_block = f'''    // TODO: handle return type {ret}
    {function_name}({args_str});'''

        cleanup_block = "\n".join(cleanup) if cleanup else "    /* no cleanup */"

        return f'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cJSON.h"
{prelude_block}
{user_code}

int main(int argc, char *argv[]) {{
    if (argc < 2) return 1;
    cJSON *input = cJSON_Parse(argv[1]);
    if (!input) return 1;

{read_block}

{output_block}

{cleanup_block}

    cJSON_Delete(input);
    return 0;
}}
'''

    raise ValueError(f"Unsupported language: {language}")


# ── Inline Python execution (fast path) ──

def _build_python_driver(function_name: str, parameters: list[dict], code: str, input_data: dict) -> str:
    """Build a complete Python script with test harness."""
    param_names = [p["name"] for p in parameters]
    args = ", ".join(f'"{k}": __input["{k}"]' for k in input_data)

    # Auto-detect calling convention
    has_class_solution = "class Solution" in (code or "")
    if has_class_solution:
        call_line = f'sol = Solution()\n    __result = sol.{function_name}(**{{ {args} }})'
    else:
        call_line = f'__result = {function_name}(**{{ {args} }})'

    driver = f'''
import json
import sys

{code}

if __name__ == "__main__":
    __input = json.loads(sys.stdin.read())
    {call_line}
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


# ── Docker execution for non-Python languages ──

async def _run_code_in_docker(
    language: str,
    code: str,
    input_str: str,
    time_limit_ms: int,
    memory_limit_mb: int = 256,
) -> tuple[str | None, str | None, int]:
    """Execute code in a Docker sandbox container. Supports compiled and interpreted languages."""
    import docker
    from docker.errors import ImageNotFound

    client = docker.from_env()
    image = _DOCKER_IMAGE_MAP.get(language, "codequizhub-sandbox-python")
    source_file = _DOCKER_SOURCE_MAP.get(language, "solution.py")
    compile_cmd = _DOCKER_COMPILE_MAP.get(language)
    run_cmd = _DOCKER_RUN_MAP.get(language, "python3 solution.py")
    input_file = "input.json"

    # Ensure image exists
    try:
        client.images.get(image)
    except ImageNotFound:
        try:
            client.images.pull(image)
        except Exception:
            return None, (
                f"Docker image '{image}' not found. "
                f"Please build it with: docker compose --profile sandbox build sandbox-{language}"
            ), -1

    loop = asyncio.get_running_loop()

    def _execute() -> tuple[str | None, str | None, int]:
        # Create tar with source and input
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            code_bytes = code.encode('utf-8')
            info = tarfile.TarInfo(name=source_file)
            info.size = len(code_bytes)
            tar.addfile(info, io.BytesIO(code_bytes))

            input_bytes = input_str.encode('utf-8')
            info2 = tarfile.TarInfo(name=input_file)
            info2.size = len(input_bytes)
            tar.addfile(info2, io.BytesIO(input_bytes))
        tar_stream.seek(0)

        container = client.containers.create(
            image=image,
            command="sleep 30",
            mem_limit=f"{memory_limit_mb}m",
            nano_cpus=1_000_000_000,
            network_disabled=True,
            read_only=False,
            user="nobody",
            working_dir="/workspace",
            detach=True,
        )
        try:
            container.start()
            container.put_archive("/workspace", tar_stream)

            # Compile step (if needed) — not timed
            if compile_cmd:
                compile_result = container.exec_run(
                    f"sh -c 'cd /workspace && {compile_cmd}'",
                    demux=True,
                )
                if compile_result.exit_code != 0:
                    compile_stderr = compile_result.output[1].decode('utf-8', errors='replace').strip() if compile_result.output[1] else ""
                    compile_stdout = compile_result.output[0].decode('utf-8', errors='replace').strip() if compile_result.output[0] else ""
                    return None, compile_stderr or compile_stdout or "Compilation error", compile_result.exit_code

            # Run step — timed
            start = time.time()
            run_result = container.exec_run(
                f"sh -c 'cd /workspace && {run_cmd} \"$(cat {input_file})\"'",
                demux=True,
            )
            elapsed = int((time.time() - start) * 1000)

            stdout, stderr = run_result.output
            stdout_str = stdout.decode('utf-8', errors='replace').strip() if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='replace').strip() if stderr else ""
            exit_code = run_result.exit_code or 0

            if elapsed > time_limit_ms:
                return None, "Time limit exceeded", -1

            return stdout_str, stderr_str, exit_code
        except Exception as e:
            return None, str(e)[:500], -1
        finally:
            try:
                container.remove(force=True)
            except Exception:
                pass

    return await loop.run_in_executor(None, _execute)


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

    # Build per-test-case results
    results = []
    compile_error = None

    params = sig.parameters_json if isinstance(sig.parameters_json, list) else []

    for tc in test_cases:
        input_json = json_mod.dumps(tc.input_params_json)

        if body.language == "python":
            # Fast inline Python execution
            user_code = body.code
            if sig.prelude_code:
                user_code = f"# === Prelude ===\n{sig.prelude_code}\n\n{body.code}"
            full_code = _build_python_driver(
                sig.function_name, params, user_code, tc.input_params_json,
            )
            stdout, stderr, exit_code = await _run_python_async(
                full_code, input_json, problem.time_limit,
            )
        else:
            # Docker-based execution for non-Python languages
            try:
                if sig.driver_template:
                    prelude = f"\n// === Prelude ===\n{sig.prelude_code}\n" if sig.prelude_code else ""
                    full_code = f"#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\n{prelude}{body.code}\n\n{sig.driver_template}"
                else:
                    full_code = _generate_driver(
                        body.language, sig.function_name, params, tc.input_params_json, body.code, sig.return_type, prelude_code=sig.prelude_code or "",
                    )
            except ValueError as e:
                return success_response({
                    "results": [],
                    "compile_error": str(e),
                })
            stdout, stderr, exit_code = await _run_code_in_docker(
                body.language, full_code, input_json, problem.time_limit,
            )

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

    params = sig.parameters_json if isinstance(sig.parameters_json, list) else []
    input_json = json_mod.dumps(body.custom_input)

    if body.language == "python":
        user_code = body.code
        if sig.prelude_code:
            user_code = f"# === Prelude ===\n{sig.prelude_code}\n\n{body.code}"
        full_code = _build_python_driver(
            sig.function_name, params, user_code, body.custom_input,
        )
        stdout, stderr, exit_code = await _run_python_async(
            full_code, input_json, problem.time_limit,
        )
    else:
        try:
            if sig.driver_template:
                prelude = f"\n// === Prelude ===\n{sig.prelude_code}\n" if sig.prelude_code else ""
                full_code = f"#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\n{prelude}{body.code}\n\n{sig.driver_template}"
            else:
                full_code = _generate_driver(
                    body.language, sig.function_name, params, body.custom_input, body.code, sig.return_type, prelude_code=sig.prelude_code or "",
                )
        except ValueError as e:
            return success_response({"output": None, "error": str(e)})
        stdout, stderr, exit_code = await _run_code_in_docker(
            body.language, full_code, input_json, problem.time_limit,
        )

    return success_response({
        "output": stdout,
        "error": stderr if exit_code != 0 else None,
    })

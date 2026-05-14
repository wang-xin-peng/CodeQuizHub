"""
CodeQuizHub Judge Worker
Consumes tasks from Redis queue, assembles code, executes in Docker sandbox,
compares results, and updates the database.
"""

import asyncio
import json
import logging
import signal
import sys

import asyncpg
import redis.asyncio as aioredis

from assembler import CodeAssembler
from comparator import ResultComparator
from executor import DockerExecutor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("judge_worker")

# Configuration from environment
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://codequizhub:codequizhub@localhost:5432/codequizhub")
QUEUE_NAME = "judge_queue"

shutdown_event = asyncio.Event()


def handle_shutdown(signum, frame):
    logger.info("Received shutdown signal, gracefully stopping...")
    shutdown_event.set()


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


async def get_db_pool():
    """Create asyncpg connection pool."""
    # Convert async SQLAlchemy URL to asyncpg format
    db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.create_pool(db_url, min_size=2, max_size=10)


async def update_submission_status(pool, submission_id: str, status: str, score: int = 0,
                                    time_used: int | None = None, memory_used: int | None = None,
                                    error_message: str | None = None):
    """Update submission status in database."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE submissions
            SET status = $1, score = $2, time_used = $3, memory_used = $4, error_message = $5
            WHERE id = $6::uuid
            """,
            status, score, time_used, memory_used, error_message, submission_id,
        )


async def save_submission_result(pool, submission_id: str, test_case_id: str,
                                  status: str, actual_output: str | None,
                                  time_used: int | None, memory_used: int | None):
    """Save per-testcase result."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO submission_results (id, submission_id, test_case_id, status, actual_output, time_used, memory_used)
            VALUES (gen_random_uuid(), $1::uuid, $2::uuid, $3, $4, $5, $6)
            ON CONFLICT (submission_id, test_case_id) DO UPDATE
            SET status = $3, actual_output = $4, time_used = $5, memory_used = $6
            """,
            submission_id, test_case_id, status, actual_output, time_used, memory_used,
        )


async def get_problem_data(pool, problem_id: str) -> dict:
    """Fetch problem data including signatures and test cases."""
    async with pool.acquire() as conn:
        problem = await conn.fetchrow(
            "SELECT * FROM problems WHERE id = $1::uuid", problem_id
        )
        signatures = await conn.fetch(
            "SELECT * FROM problem_function_signatures WHERE problem_id = $1::uuid", problem_id
        )
        test_cases = await conn.fetch(
            'SELECT * FROM test_cases WHERE problem_id = $1::uuid ORDER BY "order"', problem_id
        )

    return {
        "problem": dict(problem) if problem else None,
        "signatures": [dict(s) for s in signatures],
        "test_cases": [dict(tc) for tc in test_cases],
    }


async def process_submission(task: dict, pool, redis_client):
    """Process a single judge task."""
    submission_id = task["submission_id"]
    problem_id = task["problem_id"]
    language = task["language"]
    user_code = task["code"]
    time_limit = task.get("time_limit", 1000)
    memory_limit = task.get("memory_limit", 256)

    logger.info(f"Processing submission {submission_id} (lang={language})")

    # Update status to judging
    await update_submission_status(pool, submission_id, "judging")
    await redis_client.set(f"submission:{submission_id}:status", "judging", ex=300)

    try:
        # Fetch problem data
        problem_data = await get_problem_data(pool, problem_id)
        if not problem_data["problem"]:
            await update_submission_status(pool, submission_id, "runtime_error", error_message="题目不存在")
            return

        # Find signature for this language
        sig = next((s for s in problem_data["signatures"] if s["language"] == language), None)
        if not sig:
            await update_submission_status(pool, submission_id, "runtime_error", error_message="不支持该语言")
            return

        test_cases = problem_data["test_cases"]
        compare_mode = problem_data["problem"]["compare_mode"]

        # Assemble full code
        assembler = CodeAssembler(language)
        executor = DockerExecutor(language, time_limit_ms=time_limit, memory_limit_mb=memory_limit)
        comparator = ResultComparator(compare_mode)

        prelude = sig.get("prelude_code") or ""
        driver_template = sig.get("driver_template") or ""

        total_passed = 0
        total_cases = len(test_cases)
        max_time = 0
        max_memory = 0
        final_status = "accepted"

        for tc in test_cases:
            tc_id = str(tc["id"])
            input_params = tc["input_params_json"]
            expected_output = tc["expected_output_json"]

            # Assemble code with test case input
            full_code = assembler.assemble(
                prelude_code=prelude,
                user_code=user_code,
                driver_template=driver_template,
                function_name=sig["function_name"],
                input_params=input_params,
                parameters_json=sig["parameters_json"],
            )

            # Execute in Docker sandbox
            result = await executor.execute(full_code, json.dumps(input_params))

            tc_time = result.get("time_used", 0)
            tc_memory = result.get("memory_used", 0)
            max_time = max(max_time, tc_time)
            max_memory = max(max_memory, tc_memory)

            if result["status"] == "compilation_error":
                await save_submission_result(pool, submission_id, tc_id, "compilation_error", result.get("error"), tc_time, tc_memory)
                final_status = "compilation_error"
                await update_submission_status(
                    pool, submission_id, "compilation_error",
                    error_message=result.get("error", ""),
                    time_used=max_time, memory_used=max_memory,
                )
                await redis_client.set(f"submission:{submission_id}:status", "compilation_error", ex=300)
                return

            if result["status"] == "timeout":
                await save_submission_result(pool, submission_id, tc_id, "time_limit_exceeded", None, tc_time, tc_memory)
                final_status = "time_limit_exceeded"
                break

            if result["status"] == "memory_exceeded":
                await save_submission_result(pool, submission_id, tc_id, "memory_limit_exceeded", None, tc_time, tc_memory)
                final_status = "memory_limit_exceeded"
                break

            if result["status"] == "runtime_error":
                await save_submission_result(pool, submission_id, tc_id, "runtime_error", result.get("error"), tc_time, tc_memory)
                final_status = "runtime_error"
                break

            # Compare output
            actual_output = result.get("output", "").strip()
            is_correct = comparator.compare(actual_output, json.dumps(expected_output))

            if is_correct:
                total_passed += 1
                await save_submission_result(pool, submission_id, tc_id, "accepted", actual_output, tc_time, tc_memory)
            else:
                await save_submission_result(pool, submission_id, tc_id, "wrong_answer", actual_output, tc_time, tc_memory)
                if final_status == "accepted":
                    final_status = "wrong_answer"

        # Calculate score
        score = int((total_passed / total_cases) * 100) if total_cases > 0 else 0

        await update_submission_status(
            pool, submission_id, final_status,
            score=score, time_used=max_time, memory_used=max_memory,
        )
        await redis_client.set(f"submission:{submission_id}:status", final_status, ex=300)

        logger.info(f"Submission {submission_id}: {final_status} (score={score})")

    except Exception as e:
        logger.error(f"Error processing submission {submission_id}: {e}", exc_info=True)
        await update_submission_status(
            pool, submission_id, "runtime_error",
            error_message=f"判题服务内部错误: {str(e)}",
        )
        await redis_client.set(f"submission:{submission_id}:status", "runtime_error", ex=300)


async def main():
    logger.info("Judge Worker starting...")

    pool = await get_db_pool()
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

    logger.info("Connected to database and Redis. Waiting for tasks...")

    try:
        while not shutdown_event.is_set():
            # Blocking pop with 5s timeout so we can check shutdown_event
            result = await redis_client.brpop(QUEUE_NAME, timeout=5)
            if result is None:
                continue

            _, task_json = result
            try:
                task = json.loads(task_json)
                await process_submission(task, pool, redis_client)
            except json.JSONDecodeError:
                logger.error(f"Invalid task JSON: {task_json}")
            except Exception as e:
                logger.error(f"Error processing task: {e}", exc_info=True)
    finally:
        await redis_client.close()
        await pool.close()
        logger.info("Judge Worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())

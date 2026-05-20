"""Integration tests for the complete judging pipeline.

Tests the end-to-end flow: code assembly → execution → result comparison → score calculation.
Uses mocked executor and database to test the core judging logic without external dependencies.
"""
import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add judge directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assembler import CodeAssembler
from comparator import ResultComparator


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_problem_data():
    """Sample problem data as fetched from the database."""
    return {
        "problem": {
            "id": "00000000-0000-0000-0000-000000000001",
            "compare_mode": "exact",
            "time_limit": 1000,
            "memory_limit": 256,
        },
        "signatures": [
            {
                "id": "00000000-0000-0000-0000-000000000010",
                "language": "python",
                "function_name": "add",
                "parameters_json": [
                    {"name": "a", "type": "int", "description": "first number"},
                    {"name": "b", "type": "int", "description": "second number"},
                ],
                "return_type": "int",
                "code_template": "def add(a: int, b: int) -> int:\n    pass",
                "prelude_code": "",
                "driver_template": "",
            }
        ],
        "test_cases": [
            {
                "id": "00000000-0000-0000-0000-000000000020",
                "input_params_json": {"a": 1, "b": 2},
                "expected_output_json": 3,
                "is_public": True,
                "order": 0,
            },
            {
                "id": "00000000-0000-0000-0000-000000000021",
                "input_params_json": {"a": -5, "b": 10},
                "expected_output_json": 5,
                "is_public": True,
                "order": 1,
            },
            {
                "id": "00000000-0000-0000-0000-000000000022",
                "input_params_json": {"a": 0, "b": 0},
                "expected_output_json": 0,
                "is_public": False,
                "order": 2,
            },
        ],
    }


@pytest.fixture
def mock_executor():
    """Create a mock for DockerExecutor.execute()."""
    async def _mock_execute(full_code: str, input_json: str):
        """Execute Python code locally for testing purposes."""
        import tempfile
        import subprocess

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
            f.write(full_code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path, input_json],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "SyntaxError" in stderr or "IndentationError" in stderr:
                    return {"status": "compilation_error", "error": stderr, "time_used": 0, "memory_used": 0}
                return {"status": "runtime_error", "error": stderr, "time_used": 10, "memory_used": 1}
            return {"status": "completed", "output": result.stdout, "time_used": 10, "memory_used": 1}
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Time limit exceeded", "time_used": 1000, "memory_used": 0}
        finally:
            os.unlink(tmp_path)

    mock = AsyncMock(side_effect=_mock_execute)
    return mock


# ─── Full Pipeline: Assemble → Execute → Compare ────────────────────────────

class TestFullPipelinePython:
    """Integration tests for the full Python judging pipeline."""

    @pytest.mark.asyncio
    async def test_all_cases_accepted(self, sample_problem_data, mock_executor):
        """All test cases pass -> final status should be 'accepted'."""
        problem_data = sample_problem_data
        sig = problem_data["signatures"][0]
        test_cases = problem_data["test_cases"]
        compare_mode = problem_data["problem"]["compare_mode"]

        user_code = "class Solution:\n    def add(self, a, b):\n        return a + b"
        assembler = CodeAssembler("python")
        comparator = ResultComparator(compare_mode)

        total_passed = 0
        total_cases = len(test_cases)
        max_time = 0
        max_memory = 0
        final_status = "accepted"

        for tc in test_cases:
            input_params = tc["input_params_json"]
            expected_output = tc["expected_output_json"]

            full_code = assembler.assemble(
                prelude_code=sig.get("prelude_code") or "",
                user_code=user_code,
                driver_template=sig.get("driver_template") or "",
                function_name=sig["function_name"],
                input_params=input_params,
                parameters_json=sig["parameters_json"],
            )

            result = await mock_executor(full_code, json.dumps(input_params))
            max_time = max(max_time, result.get("time_used", 0))
            max_memory = max(max_memory, result.get("memory_used", 0))

            if result["status"] == "compilation_error":
                final_status = "compilation_error"
                break
            if result["status"] == "runtime_error":
                final_status = "runtime_error"
                break
            if result["status"] == "timeout":
                final_status = "time_limit_exceeded"
                break

            actual_output = result.get("output", "").strip()
            is_correct = comparator.compare(actual_output, json.dumps(expected_output))
            if is_correct:
                total_passed += 1
            elif final_status == "accepted":
                final_status = "wrong_answer"

        score = int((total_passed / total_cases) * 100) if total_cases > 0 else 0

        assert final_status == "accepted"
        assert total_passed == 3
        assert score == 100

    @pytest.mark.asyncio
    async def test_wrong_answer_detected(self, sample_problem_data, mock_executor):
        """Incorrect code -> 'wrong_answer' final status and partial score."""
        problem_data = sample_problem_data
        sig = problem_data["signatures"][0]
        test_cases = problem_data["test_cases"]
        compare_mode = problem_data["problem"]["compare_mode"]

        # Buggy code: adds 1 extra
        user_code = "class Solution:\n    def add(self, a, b):\n        return a + b + 1"
        assembler = CodeAssembler("python")
        comparator = ResultComparator(compare_mode)

        total_passed = 0
        final_status = "accepted"

        for tc in test_cases:
            input_params = tc["input_params_json"]
            expected_output = tc["expected_output_json"]

            full_code = assembler.assemble(
                prelude_code="", user_code=user_code, driver_template="",
                function_name=sig["function_name"],
                input_params=input_params, parameters_json=sig["parameters_json"],
            )

            result = await mock_executor(full_code, json.dumps(input_params))
            if result["status"] in ("compilation_error", "runtime_error", "timeout"):
                final_status = result["status"]
                break

            actual_output = result.get("output", "").strip()
            is_correct = comparator.compare(actual_output, json.dumps(expected_output))
            if is_correct:
                total_passed += 1
            elif final_status == "accepted":
                final_status = "wrong_answer"

        assert final_status == "wrong_answer"
        assert total_passed == 0  # a+b+1 makes all 3 cases wrong

    @pytest.mark.asyncio
    async def test_syntax_error_compilation_failure(self, sample_problem_data, mock_executor):
        """Syntax error in user code -> 'compilation_error'."""
        problem_data = sample_problem_data
        sig = problem_data["signatures"][0]
        test_cases = problem_data["test_cases"]

        user_code = "def add(a, b):\n    return a +\n    b"  # SyntaxError: invalid syntax
        assembler = CodeAssembler("python")
        final_status = "accepted"

        for tc in test_cases[:1]:  # Just first case
            input_params = tc["input_params_json"]

            full_code = assembler.assemble(
                prelude_code="", user_code=user_code, driver_template="",
                function_name=sig["function_name"],
                input_params=input_params, parameters_json=sig["parameters_json"],
            )

            result = await mock_executor(full_code, json.dumps(input_params))
            if result["status"] == "compilation_error":
                final_status = "compilation_error"
                break
            if result["status"] == "runtime_error":
                final_status = "runtime_error"
                break

        assert final_status == "runtime_error" or final_status == "compilation_error"

    @pytest.mark.asyncio
    async def test_runtime_error_detected(self, sample_problem_data, mock_executor):
        """Runtime error (e.g., ZeroDivisionError) -> 'runtime_error'."""
        problem_data = sample_problem_data
        sig = problem_data["signatures"][0]
        test_cases = [
            {
                "id": "00000000-0000-0000-0000-000000000030",
                "input_params_json": {"a": 1, "b": 0},
                "expected_output_json": None,
                "is_public": True,
                "order": 0,
            }
        ]

        # Code that divides by b (would crash when b=0)
        user_code = "class Solution:\n    def add(self, a, b):\n        return a // b"
        assembler = CodeAssembler("python")
        final_status = "accepted"

        for tc in test_cases:
            input_params = tc["input_params_json"]
            full_code = assembler.assemble(
                prelude_code="", user_code=user_code, driver_template="",
                function_name=sig["function_name"],
                input_params=input_params, parameters_json=sig["parameters_json"],
            )
            result = await mock_executor(full_code, json.dumps(input_params))
            if result["status"] == "runtime_error":
                final_status = "runtime_error"
                assert "division by zero" in result.get("error", "").lower() or "ZeroDivisionError" in result.get("error", "")
                break

        assert final_status == "runtime_error"

    @pytest.mark.asyncio
    async def test_score_calculation_partial(self, sample_problem_data, mock_executor):
        """Partial pass: 2/3 correct -> score = 66."""
        problem_data = sample_problem_data
        sig = problem_data["signatures"][0]
        test_cases = problem_data["test_cases"]
        compare_mode = problem_data["problem"]["compare_mode"]

        # Only handles positive numbers correctly
        user_code = "class Solution:\n    def add(self, a, b):\n        if a < 0:\n            return 0\n        return a + b"
        assembler = CodeAssembler("python")
        comparator = ResultComparator(compare_mode)

        total_passed = 0
        final_status = "accepted"

        for tc in test_cases:
            input_params = tc["input_params_json"]
            expected_output = tc["expected_output_json"]
            full_code = assembler.assemble(
                prelude_code="", user_code=user_code, driver_template="",
                function_name=sig["function_name"],
                input_params=input_params, parameters_json=sig["parameters_json"],
            )
            result = await mock_executor(full_code, json.dumps(input_params))
            if result["status"] in ("compilation_error", "runtime_error", "timeout"):
                final_status = result["status"]
                break

            actual_output = result.get("output", "").strip()
            if comparator.compare(actual_output, json.dumps(expected_output)):
                total_passed += 1
            elif final_status == "accepted":
                final_status = "wrong_answer"

        score = int((total_passed / len(test_cases)) * 100) if len(test_cases) > 0 else 0
        assert total_passed == 2
        assert score == 66

    @pytest.mark.asyncio
    async def test_pipeline_with_java_fallback(self, sample_problem_data, mock_executor):
        """Pipeline should handle Java language configuration correctly."""
        problem_data = sample_problem_data
        sig = problem_data["signatures"][0]
        test_cases = problem_data["test_cases"][:1]

        # Even for Java, assembly + comparison logic should work
        assembler = CodeAssembler("java")
        assert assembler.language == "java"

        user_code = "class Solution {\n    public int add(int a, int b) {\n        return a + b;\n    }\n}"
        full_code = assembler.assemble(
            prelude_code="", user_code=user_code, driver_template="",
            function_name=sig["function_name"],
            input_params=test_cases[0]["input_params_json"],
            parameters_json=sig["parameters_json"],
        )
        assert "// === Solution ===" in full_code
        assert user_code in full_code


class TestComparatorIntegration:
    """Integration tests: comparator used in pipeline context."""

    def test_compare_modes_affect_pipeline_result(self):
        """Different compare modes should correctly classify outputs."""
        c_exact = ResultComparator("exact")
        c_unordered = ResultComparator("unordered")
        c_float = ResultComparator("float")

        # Exact comparison: order matters
        assert c_exact.compare("[1, 2, 3]", "[3, 2, 1]") is False
        assert c_unordered.compare("[1, 2, 3]", "[3, 2, 1]") is True

        # Float comparison: precision tolerance
        assert c_exact.compare("0.1 + 0.2", "0.3") is False  # JSON won't eval, but strings differ
        assert c_float.compare("0.30000000000000004", "0.3") is True

    def test_comparison_edge_cases_in_pipeline(self):
        """Edge cases that occur in the pipeline."""
        c = ResultComparator("exact")

        # Empty output
        assert c.compare("", "") is True
        assert c.compare("", "null") is False

        # Whitespace handling
        assert c.compare(" 42 ", "42") is True

        # Null vs None
        assert c.compare("null", "null") is True

        # Boolean values
        assert c.compare("true", "true") is True
        assert c.compare("false", "true") is False


class TestScoringAndStatus:
    """Test scoring calculation and final status determination."""

    def test_all_passed_100_score(self):
        """All cases pass -> 100 score."""
        passed, total = 5, 5
        score = int((passed / total) * 100)
        assert score == 100

    def test_half_passed_50_score(self):
        """Half pass -> 50 score."""
        passed, total = 3, 6
        score = int((passed / total) * 100)
        assert score == 50

    def test_none_passed_0_score(self):
        """None pass -> 0 score."""
        passed, total = 0, 4
        score = int((passed / total) * 100) if total > 0 else 0
        assert score == 0

    def test_empty_test_cases_zero_score(self):
        """No test cases -> 0 score."""
        passed, total = 0, 0
        score = int((passed / total) * 100) if total > 0 else 0
        assert score == 0

    def test_score_rounding_down(self):
        """Score should truncate (not round)."""
        passed, total = 1, 3
        score = int((passed / total) * 100)
        assert score == 33  # 33.33 -> 33

    def test_score_rounding_up(self):
        """Score edge case near 100."""
        passed, total = 2, 3
        score = int((passed / total) * 100)
        assert score == 66  # 66.66 -> 66

    def test_final_status_priority(self):
        """Status should follow priority: compilation_error > runtime_error > tle > wa > accepted."""
        # Simulate the status logic from process_submission
        def determine_final(test_results):
            if "compilation_error" in test_results:
                return "compilation_error"
            if "runtime_error" in test_results:
                return "runtime_error"
            if "time_limit_exceeded" in test_results:
                return "time_limit_exceeded"
            if "wrong_answer" in test_results:
                return "wrong_answer"
            return "accepted"

        assert determine_final(["accepted", "accepted"]) == "accepted"
        assert determine_final(["accepted", "wrong_answer"]) == "wrong_answer"
        assert determine_final(["accepted", "time_limit_exceeded"]) == "time_limit_exceeded"
        assert determine_final(["accepted", "runtime_error"]) == "runtime_error"
        assert determine_final(["accepted", "compilation_error"]) == "compilation_error"

    def test_final_status_maintains_accepted_after_wa(self):
        """Once final_status becomes wrong_answer, it shouldn't revert to accepted."""
        status = "accepted"
        results = ["accepted", "wrong_answer", "accepted"]

        for r in results:
            if r == "wrong_answer" and status == "accepted":
                status = "wrong_answer"
            elif r == "accepted":
                pass  # Don't revert

        assert status == "wrong_answer"

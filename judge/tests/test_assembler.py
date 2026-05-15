"""Tests for the CodeAssembler."""
import json
import sys
import os
import tempfile
import subprocess
from pathlib import Path

import pytest

# Add judge directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assembler import CodeAssembler


class TestCodeAssembler:
    """Tests for code assembly across all languages."""

    def test_assembler_init_python(self):
        """Test initializing assembler with python language."""
        assembler = CodeAssembler("python")
        assert assembler.language == "python"
        assert assembler.config["name"] == "python"

    def test_assembler_init_java(self):
        """Test initializing assembler with java language."""
        assembler = CodeAssembler("java")
        assert assembler.language == "java"
        assert assembler.config["name"] == "java"

    def test_assembler_init_unsupported(self):
        """Test initializing assembler with unsupported language."""
        with pytest.raises(ValueError, match="Unsupported language"):
            CodeAssembler("rust")

    def test_assemble_python_with_driver_template(self):
        """Test assembling Python code with a custom driver template."""
        assembler = CodeAssembler("python")
        prelude = ""
        user_code = "class Solution:\n    def add(self, a, b):\n        return a + b"
        driver = "print(Solution().add(1, 2))"
        result = assembler.assemble(prelude, user_code, driver, "add", {}, [])

        assert "# === Prelude ===" not in result
        assert "# === Solution ===" in result
        assert user_code in result
        assert "# === Driver ===" in result
        assert driver in result
        assert result.strip().startswith("# === Solution ===")

    def test_assemble_python_with_prelude(self):
        """Test assembling Python code with a prelude."""
        assembler = CodeAssembler("python")
        prelude = "from typing import List"
        user_code = "class Solution:\n    def add(self, a, b):\n        return a + b"
        driver = "print(Solution().add(1, 2))"
        result = assembler.assemble(prelude, user_code, driver, "add", {}, [])

        assert "# === Prelude ===" in result
        assert prelude in result
        assert "# === Solution ===" in result
        assert "# === Driver ===" in result

    def test_assemble_java(self):
        """Test assembling Java code."""
        assembler = CodeAssembler("java")
        prelude = ""
        user_code = "class Solution {\n    public int add(int a, int b) {\n        return a + b;\n    }\n}"
        driver = "// driver"
        result = assembler.assemble(prelude, user_code, driver, "add", {}, [])

        assert "// === Solution ===" in result
        assert user_code in result
        assert "// === Driver ===" in result

    def test_assemble_c(self):
        """Test assembling C code."""
        assembler = CodeAssembler("c")
        prelude = "#include <stdio.h>"
        user_code = "int add(int a, int b) { return a + b; }"
        driver = "// driver"
        result = assembler.assemble(prelude, user_code, driver, "add", {}, [])

        assert "/* === Prelude ===" in result
        assert prelude in result
        assert "/* === Solution ===" in result
        assert user_code in result
        assert "/* === Driver ===" in result

    def test_assemble_cpp(self):
        """Test assembling C++ code."""
        assembler = CodeAssembler("cpp")
        prelude = "#include <vector>"
        user_code = "int add(int a, int b) { return a + b; }"
        driver = "// driver"
        result = assembler.assemble(prelude, user_code, driver, "add", {}, [])

        assert "// === Prelude ===" in result
        assert prelude in result
        assert "// === Solution ===" in result
        assert "// === Driver ===" in result

    def test_assemble_generates_python_driver(self):
        """Test that assembler generates a default Python driver when no driver template."""
        assembler = CodeAssembler("python")
        prelude = ""
        user_code = "class Solution:\n    def twoSum(self, nums, target):\n        pass"
        parameters = [
            {"name": "nums", "type": "List[int]"},
            {"name": "target", "type": "int"},
        ]
        result = assembler.assemble(prelude, user_code, "", "twoSum", {"nums": [1, 2, 3], "target": 5}, parameters)

        assert "def main():" in result
        assert 'input_data = json.loads(sys.argv[1])' in result
        assert "sol = Solution()" in result
        assert 'sol.twoSum(' in result
        assert 'input_data["nums"]' in result
        assert 'input_data["target"]' in result
        assert 'print(json.dumps(result))' in result

    def test_python_assembled_code_executes_successfully(self):
        """Test that assembled Python code actually runs and produces correct output."""
        assembler = CodeAssembler("python")
        prelude = ""
        user_code = "class Solution:\n    def add(self, a, b):\n        return a + b"
        parameters = [
            {"name": "a", "type": "int"},
            {"name": "b", "type": "int"},
        ]
        code = assembler.assemble(prelude, user_code, "", "add", {"a": 3, "b": 7}, parameters)

        # Write to temp file and execute
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path, json.dumps({"a": 3, "b": 7})],
                capture_output=True, text=True, timeout=5
            )
            assert result.returncode == 0
            assert json.loads(result.stdout.strip()) == 10
        finally:
            os.unlink(tmp_path)

    def test_python_assembled_code_with_more_complex_function(self):
        """Test assembled code with a more complex function (string concatenation)."""
        assembler = CodeAssembler("python")
        prelude = ""
        user_code = "class Solution:\n    def greet(self, name, greeting):\n        return f'{greeting}, {name}!'"
        parameters = [
            {"name": "name", "type": "str"},
            {"name": "greeting", "type": "str"},
        ]
        code = assembler.assemble(prelude, user_code, "", "greet", {"name": "World", "greeting": "Hello"}, parameters)

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path, json.dumps({"name": "World", "greeting": "Hello"})],
                capture_output=True, text=True, timeout=5
            )
            assert result.returncode == 0
            assert json.loads(result.stdout.strip()) == "Hello, World!"
        finally:
            os.unlink(tmp_path)

    def test_python_assembled_code_runtime_error(self):
        """Test that assembly still works even if the code would have a runtime error."""
        assembler = CodeAssembler("python")
        user_code = "class Solution:\n    def divide(self, a, b):\n        return a // b"
        parameters = [
            {"name": "a", "type": "int"},
            {"name": "b", "type": "int"},
        ]
        code = assembler.assemble("", user_code, "", "divide", {"a": 1, "b": 0}, parameters)

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path, json.dumps({"a": 1, "b": 0})],
                capture_output=True, text=True, timeout=5
            )
            assert result.returncode != 0  # ZeroDivisionError
        finally:
            os.unlink(tmp_path)

    def test_assemble_with_multiple_params_no_prelude(self):
        """Test assembling with multiple parameters and no prelude."""
        assembler = CodeAssembler("python")
        user_code = "class Solution:\n    def concat(self, *args):\n        return ''.join(args)"
        parameters = [
            {"name": "a", "type": "str"},
            {"name": "b", "type": "str"},
            {"name": "c", "type": "str"},
        ]
        result = assembler.assemble("", user_code, "", "concat", {"a": "x", "b": "y", "c": "z"}, parameters)

        assert 'sol.concat(' in result
        assert 'input_data["a"]' in result
        assert 'input_data["b"]' in result
        assert 'input_data["c"]' in result

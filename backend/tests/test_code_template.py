"""Tests for code template auto-generation logic."""

import pytest
from app.utils.code_template import generate_code_template


class TestGenerateCodeTemplate:
    """Test code template generation for all supported languages."""

    def test_python_simple_function(self):
        """Python: simple function with basic types."""
        template = generate_code_template(
            language="python",
            function_name="add",
            parameters=[{"name": "a", "type": "int"}, {"name": "b", "type": "int"}],
            return_type="int",
        )
        assert "def add(a: int, b: int) -> int:" in template
        assert "return 0" in template

    def test_python_list_param(self):
        """Python: function with list parameters."""
        template = generate_code_template(
            language="python",
            function_name="twoSum",
            parameters=[
                {"name": "nums", "type": "int[]"},
                {"name": "target", "type": "int"},
            ],
            return_type="int[]",
        )
        assert "def twoSum(nums: list[int], target: int) -> list[int]:" in template

    def test_python_string_param(self):
        """Python: function with string parameters."""
        template = generate_code_template(
            language="python",
            function_name="greet",
            parameters=[{"name": "name", "type": "str"}],
            return_type="str",
        )
        assert "def greet(name: str) -> str:" in template
        assert 'return ""' in template

    def test_python_void_return(self):
        """Python: function with void return."""
        template = generate_code_template(
            language="python",
            function_name="printHello",
            parameters=[],
            return_type="void",
        )
        assert "def printHello() -> None:" in template
        assert "pass" in template

    def test_java_simple_function(self):
        """Java: simple function with basic types."""
        template = generate_code_template(
            language="java",
            function_name="add",
            parameters=[{"name": "a", "type": "int"}, {"name": "b", "type": "int"}],
            return_type="int",
        )
        assert "class Solution {" in template
        assert "public int add(int a, int b)" in template

    def test_java_string_param(self):
        """Java: function with String parameter."""
        template = generate_code_template(
            language="java",
            function_name="greet",
            parameters=[{"name": "name", "type": "String"}],
            return_type="String",
        )
        assert "class Solution {" in template
        assert "public String greet(String name)" in template
        assert 'return "";' in template

    def test_java_array_param(self):
        """Java: function with array parameter."""
        template = generate_code_template(
            language="java",
            function_name="twoSum",
            parameters=[
                {"name": "nums", "type": "int[]"},
                {"name": "target", "type": "int"},
            ],
            return_type="int[]",
        )
        assert "public int[] twoSum(int[] nums, int target)" in template
        assert "return null;" in template

    def test_java_boolean_return(self):
        """Java: function with boolean return."""
        template = generate_code_template(
            language="java",
            function_name="isValid",
            parameters=[{"name": "s", "type": "String"}],
            return_type="bool",
        )
        assert "public boolean isValid(String s)" in template
        assert "return false;" in template

    def test_cpp_simple_function(self):
        """C++: simple function with basic types."""
        template = generate_code_template(
            language="cpp",
            function_name="add",
            parameters=[{"name": "a", "type": "int"}, {"name": "b", "type": "int"}],
            return_type="int",
        )
        assert "#include <vector>" in template
        assert "#include <string>" in template
        assert "int add(int a, int b)" in template
        assert "return 0;" in template

    def test_cpp_vector_param(self):
        """C++: function with vector parameter."""
        template = generate_code_template(
            language="cpp",
            function_name="twoSum",
            parameters=[
                {"name": "nums", "type": "int[]"},
                {"name": "target", "type": "int"},
            ],
            return_type="int[]",
        )
        assert "vector<int>& twoSum(vector<int>& nums, int target)" in template

    def test_cpp_string_return(self):
        """C++: function returning string."""
        template = generate_code_template(
            language="cpp",
            function_name="greet",
            parameters=[{"name": "name", "type": "String"}],
            return_type="str",
        )
        assert "string greet(string name)" in template
        assert 'return "";' in template

    def test_c_simple_function(self):
        """C: simple function with basic types."""
        template = generate_code_template(
            language="c",
            function_name="add",
            parameters=[{"name": "a", "type": "int"}, {"name": "b", "type": "int"}],
            return_type="int",
        )
        assert "#include <stdio.h>" in template
        assert "int add(int a, int b)" in template
        assert "return 0;" in template

    def test_c_pointer_param(self):
        """C: function with pointer parameter."""
        template = generate_code_template(
            language="c",
            function_name="twoSum",
            parameters=[
                {"name": "nums", "type": "int[]"},
                {"name": "target", "type": "int"},
            ],
            return_type="int[]",
        )
        assert "int* twoSum(int* nums, int target)" in template

    def test_unsupported_language(self):
        """Unsupported language should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported language"):
            generate_code_template(
                language="javascript",
                function_name="foo",
                parameters=[],
                return_type="void",
            )

    def test_type_mapping_fallback(self):
        """Custom type names that aren't mapped should pass through."""
        template = generate_code_template(
            language="python",
            function_name="process",
            parameters=[{"name": "data", "type": "CustomType"}],
            return_type="CustomType",
        )
        assert "def process(data: CustomType) -> CustomType:" in template

    def test_multiple_params_python(self):
        """Python: function with many parameters."""
        template = generate_code_template(
            language="python",
            function_name="searchMatrix",
            parameters=[
                {"name": "matrix", "type": "int[][]"},
                {"name": "target", "type": "int"},
            ],
            return_type="bool",
        )
        assert "def searchMatrix(matrix: list[list[int]], target: int) -> bool:" in template
        assert "return False" in template

    def test_java_2d_array_param(self):
        """Java: function with 2D array parameter."""
        template = generate_code_template(
            language="java",
            function_name="searchMatrix",
            parameters=[
                {"name": "matrix", "type": "int[][]"},
                {"name": "target", "type": "int"},
            ],
            return_type="bool",
        )
        assert "public boolean searchMatrix(int[][] matrix, int target)" in template

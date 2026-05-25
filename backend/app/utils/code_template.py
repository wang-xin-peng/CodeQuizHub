"""
Code Template Generator - Automatically generates code templates for each language
based on function signature definitions.
"""

from __future__ import annotations

from typing import Any

# Language-specific type mappings for template generation
TYPE_MAP: dict[str, dict[str, str]] = {
    "python": {
        "int": "int",
        "int[]": "list[int]",
        "int[][]": "list[list[int]]",
        "str": "str",
        "str[]": "list[str]",
        "bool": "bool",
        "float": "float",
        "double": "float",
        "char": "str",
        "char[]": "list[str]",
        "long": "int",
        "void": "None",
        "ListNode": "Optional[ListNode]",
        "TreeNode": "Optional[TreeNode]",
    },
    "java": {
        "int": "int",
        "int[]": "int[]",
        "int[][]": "int[][]",
        "str": "String",
        "String": "String",
        "str[]": "String[]",
        "String[]": "String[]",
        "bool": "boolean",
        "boolean": "boolean",
        "float": "float",
        "double": "double",
        "char": "char",
        "long": "long",
        "void": "void",
        "ListNode": "ListNode",
        "TreeNode": "TreeNode",
        "list": "List<Integer>",
    },
    "cpp": {
        "int": "int",
        "int[]": "vector<int>&",
        "int[][]": "vector<vector<int>>&",
        "str": "string",
        "String": "string",
        "str[]": "vector<string>&",
        "bool": "bool",
        "boolean": "bool",
        "float": "float",
        "double": "double",
        "char": "char",
        "long": "long long",
        "void": "void",
        "ListNode": "ListNode*",
        "TreeNode": "TreeNode*",
    },
    "c": {
        "int": "int",
        "int[]": "int*",
        "int[][]": "int**",
        "str": "char*",
        "String": "char*",
        "str[]": "char**",
        "bool": "int",
        "boolean": "int",
        "float": "float",
        "double": "double",
        "char": "char",
        "long": "long",
        "void": "void",
        "ListNode": "struct ListNode*",
        "TreeNode": "struct TreeNode*",
    },
}


def _map_type(language: str, type_name: str) -> str:
    """Map a common type name to the language-specific type."""
    lang_map = TYPE_MAP.get(language, TYPE_MAP["python"])
    # Exact match first
    if type_name in lang_map:
        return lang_map[type_name]
    # Try stripping whitespace and common prefixes
    clean = type_name.strip()
    if clean in lang_map:
        return lang_map[clean]
    # Fallback: return as-is (it might be a custom type or struct)
    return clean


def _generate_python_template(
    function_name: str,
    parameters: list[dict[str, Any]],
    return_type: str,
) -> str:
    """Generate a Python code template with a Solution class."""
    params = []
    for p in parameters:
        ptype = _map_type("python", p["type"])
        params.append(f"{p['name']}: {ptype}")

    params_str = ", ".join(params)
    ret = _map_type("python", return_type)

    lines = ["class Solution:"]
    lines.append(f"    def {function_name}(self, {params_str}) -> {ret}:")
    if ret == "None" or ret == "void":
        lines.append("        pass")
    else:
        lines.append("        # TODO: implement your solution here")
        # Add a default return value based on type
        if ret in ("int", "float"):
            lines.append("        return 0")
        elif ret == "bool":
            lines.append("        return False")
        elif ret in ("str", "List[str]"):
            lines.append('        return ""')
        elif ret in ("list[int]", "List[int]"):
            lines.append("        return []")
        else:
            lines.append("        pass")
    return "\n".join(lines) + "\n"


def _generate_java_template(
    function_name: str,
    parameters: list[dict[str, Any]],
    return_type: str,
) -> str:
    """Generate a Java code template."""
    params = []
    for p in parameters:
        ptype = _map_type("java", p["type"])
        params.append(f"{ptype} {p['name']}")

    params_str = ", ".join(params)
    ret = _map_type("java", return_type)

    lines = ["class Solution {"]
    lines.append(f"    public {ret} {function_name}({params_str}) {{")
    if ret == "void":
        lines.append("        // TODO: implement your solution here")
        lines.append("    }")
    elif ret in ("int", "long", "float", "double", "char"):
        lines.append("        // TODO: implement your solution here")
        lines.append(f"        return 0;")
        lines.append("    }")
    elif ret == "boolean":
        lines.append("        // TODO: implement your solution here")
        lines.append("        return false;")
        lines.append("    }")
    elif ret == "String":
        lines.append("        // TODO: implement your solution here")
        lines.append('        return "";')
        lines.append("    }")
    elif ret.endswith("[]"):
        lines.append("        // TODO: implement your solution here")
        lines.append("        return null;")
        lines.append("    }")
    else:
        lines.append("        // TODO: implement your solution here")
        lines.append("        return null;")
        lines.append("    }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _generate_cpp_template(
    function_name: str,
    parameters: list[dict[str, Any]],
    return_type: str,
) -> str:
    """Generate a C++ code template."""
    params = []
    for p in parameters:
        ptype = _map_type("cpp", p["type"])
        params.append(f"{ptype} {p['name']}")

    params_str = ", ".join(params)
    ret = _map_type("cpp", return_type)

    # Include headers for common types
    lines = ['#include <vector>', '#include <string>']
    lines.append('#include <iostream>')
    lines.append('using namespace std;')
    lines.append('')
    lines.append('class Solution {')
    lines.append('public:')
    lines.append(f'    {ret} {function_name}({params_str}) {{')
    if ret == "void":
        lines.append("        // TODO: implement your solution here")
        lines.append("    }")
    elif ret in ("int", "long long", "float", "double", "char"):
        lines.append("        // TODO: implement your solution here")
        lines.append("        return 0;")
        lines.append("    }")
    elif ret == "bool":
        lines.append("        // TODO: implement your solution here")
        lines.append("        return false;")
        lines.append("    }")
    elif ret == "string":
        lines.append("        // TODO: implement your solution here")
        lines.append('        return "";')
        lines.append("    }")
    else:
        lines.append("        // TODO: implement your solution here")
        lines.append("    }")
    lines.append("};")
    return "\n".join(lines) + "\n"


def _generate_c_template(
    function_name: str,
    parameters: list[dict[str, Any]],
    return_type: str,
) -> str:
    """Generate a C code template."""
    params = []
    for p in parameters:
        ptype = _map_type("c", p["type"])
        params.append(f"{ptype} {p['name']}")

    params_str = ", ".join(params)
    ret = _map_type("c", return_type)

    lines = ['#include <stdio.h>', '#include <stdlib.h>', '#include <string.h>', '#include <stdbool.h>', '']
    lines.append(f'{ret} {function_name}({params_str}) {{')
    if ret == "void":
        lines.append("    // TODO: implement your solution here")
        lines.append("}")
    elif ret in ("int", "long", "float", "double", "char"):
        lines.append("    // TODO: implement your solution here")
        lines.append("    return 0;")
        lines.append("}")
    elif ret == "bool":
        lines.append("    // TODO: implement your solution here")
        lines.append("    return 0;")
        lines.append("}")
    elif ret.startswith("char*") or ret.startswith("char *"):
        lines.append("    // TODO: implement your solution here")
        lines.append('    return "";')
        lines.append("}")
    else:
        lines.append("    // TODO: implement your solution here")
        lines.append("}")
    return "\n".join(lines) + "\n"


def generate_code_template(
    language: str,
    function_name: str,
    parameters: list[dict[str, Any]],
    return_type: str,
) -> str:
    """Generate a code template for the given language and function signature.

    Args:
        language: One of 'python', 'java', 'cpp', 'c'.
        function_name: Name of the function.
        parameters: List of parameter dicts with 'name' and 'type' keys.
        return_type: Return type string.

    Returns:
        A code template string with a stub implementation.

    Raises:
        ValueError: If the language is not supported.
    """
    generators = {
        "python": _generate_python_template,
        "java": _generate_java_template,
        "cpp": _generate_cpp_template,
        "c": _generate_c_template,
    }

    if language not in generators:
        raise ValueError(f"Unsupported language for template generation: {language}")

    return generators[language](function_name, parameters, return_type)

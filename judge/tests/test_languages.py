"""Tests for language configurations."""
import sys
import os

import pytest

# Add judge directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from languages import get_language_config, LANGUAGE_CONFIGS


class TestLanguageConfigs:
    """Tests for language configuration and assembly functions."""

    def test_all_languages_present(self):
        """All expected languages should be configured."""
        expected = {"python", "java", "c", "cpp"}
        assert set(LANGUAGE_CONFIGS.keys()) == expected

    def test_python_config_structure(self):
        """Python config should have all required keys."""
        cfg = LANGUAGE_CONFIGS["python"]
        assert cfg["name"] == "python"
        assert cfg["display_name"] == "Python 3.11"
        assert cfg["source_file"] == "solution.py"
        assert cfg["compile_command"] is None  # interpreted
        assert cfg["run_command"] == "python3 solution.py"
        assert callable(cfg["assemble"])

    def test_java_config_structure(self):
        """Java config should have all required keys."""
        cfg = LANGUAGE_CONFIGS["java"]
        assert cfg["name"] == "java"
        assert cfg["display_name"] == "Java 17"
        assert cfg["source_file"] == "Solution.java"
        assert cfg["compile_command"] is not None
        assert cfg["run_command"] == "java -cp .:json.jar Main"
        assert callable(cfg["assemble"])

    def test_c_config_structure(self):
        """C config should have all required keys."""
        cfg = LANGUAGE_CONFIGS["c"]
        assert cfg["name"] == "c"
        assert cfg["display_name"] == "GCC 12 (C17)"
        assert cfg["source_file"] == "solution.c"
        assert cfg["compile_command"] is not None
        assert cfg["run_command"] == "./solution"
        assert callable(cfg["assemble"])

    def test_cpp_config_structure(self):
        """C++ config should have all required keys."""
        cfg = LANGUAGE_CONFIGS["cpp"]
        assert cfg["name"] == "cpp"
        assert cfg["display_name"] == "G++ 12 (C++17)"
        assert cfg["source_file"] == "solution.cpp"
        assert cfg["compile_command"] is not None
        assert cfg["run_command"] == "./solution"
        assert callable(cfg["assemble"])

    def test_get_language_config_valid(self):
        """get_language_config should return correct config for valid languages."""
        for lang in ["python", "java", "c", "cpp"]:
            cfg = get_language_config(lang)
            assert cfg["name"] == lang

    def test_get_language_config_invalid(self):
        """get_language_config should raise for unsupported languages."""
        with pytest.raises(ValueError, match="Unsupported language: rust"):
            get_language_config("rust")

    def test_python_assemble_function(self):
        """Python assemble function should combine code parts correctly."""
        assemble = LANGUAGE_CONFIGS["python"]["assemble"]
        prelude = "from typing import List"
        user_code = "class Solution: pass"
        driver = "print('test')"

        result = assemble(prelude, user_code, driver)
        assert "# === Prelude ===" in result
        assert prelude in result
        assert "# === Solution ===" in result
        assert user_code in result
        assert "# === Driver ===" in result
        assert driver in result

    def test_python_assemble_no_prelude(self):
        """Python assemble should skip prelude section when empty."""
        assemble = LANGUAGE_CONFIGS["python"]["assemble"]
        result = assemble("", "class Solution: pass", "print('test')")
        assert "# === Prelude ===" not in result
        assert "# === Solution ===" in result
        assert "# === Driver ===" in result

    def test_java_assemble_function(self):
        """Java assemble function should combine code parts correctly."""
        assemble = LANGUAGE_CONFIGS["java"]["assemble"]
        result = assemble("import java.util.*;", "class Solution {}", "// driver")
        assert "// === Prelude ===" in result
        assert "import java.util.*;" in result
        assert "// === Solution ===" in result
        assert "// === Driver ===" in result

    def test_c_assemble_function(self):
        """C assemble function should combine code parts correctly."""
        assemble = LANGUAGE_CONFIGS["c"]["assemble"]
        result = assemble("#include <stdio.h>", "int add() {}", "// driver")
        assert "/* === Prelude ===" in result
        assert "#include <stdio.h>" in result
        assert "/* === Solution ===" in result
        assert "/* === Driver ===" in result

    def test_cpp_assemble_function(self):
        """C++ assemble function should combine code parts correctly."""
        assemble = LANGUAGE_CONFIGS["cpp"]["assemble"]
        result = assemble("#include <iostream>", "int add() {}", "// driver")
        assert "// === Prelude ===" in result
        assert "#include <iostream>" in result
        assert "// === Solution ===" in result
        assert "// === Driver ===" in result

    def test_all_languages_have_image(self):
        """All language configs should specify a Docker image."""
        for lang, cfg in LANGUAGE_CONFIGS.items():
            assert "image" in cfg, f"{lang} missing image"
            assert cfg["image"].startswith("codequizhub-sandbox-"), \
                f"{lang} image should use sandbox prefix"

    def test_all_languages_have_source_file(self):
        """All language configs should specify a source file."""
        for lang, cfg in LANGUAGE_CONFIGS.items():
            assert cfg["source_file"] != "", f"{lang} missing source_file"

    def test_interpreted_vs_compiled(self):
        """Python should be interpreted; Java, C, C++ should be compiled."""
        assert LANGUAGE_CONFIGS["python"]["compile_command"] is None
        assert LANGUAGE_CONFIGS["java"]["compile_command"] is not None
        assert LANGUAGE_CONFIGS["c"]["compile_command"] is not None
        assert LANGUAGE_CONFIGS["cpp"]["compile_command"] is not None

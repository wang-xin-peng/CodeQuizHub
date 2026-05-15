"""Tests for the ResultComparator."""
import sys
import os

import pytest

# Add judge directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from comparator import ResultComparator


class TestResultComparator:
    """Tests for result comparison across all modes."""

    # ── Exact Mode ──

    def test_exact_match_json_integer(self):
        """Exact comparison with JSON integers."""
        c = ResultComparator("exact")
        assert c.compare("42", "42") is True

    def test_exact_match_json_string(self):
        """Exact comparison with JSON strings."""
        c = ResultComparator("exact")
        assert c.compare('"hello"', '"hello"') is True

    def test_exact_match_json_list(self):
        """Exact comparison with JSON lists."""
        c = ResultComparator("exact")
        assert c.compare("[1, 2, 3]", "[1, 2, 3]") is True

    def test_exact_mismatch_json(self):
        """Exact comparison should fail for different values."""
        c = ResultComparator("exact")
        assert c.compare("42", "43") is False

    def test_exact_mismatch_list(self):
        """Exact comparison should fail for different lists."""
        c = ResultComparator("exact")
        assert c.compare("[1, 2, 3]", "[3, 2, 1]") is False

    def test_exact_match_nested_object(self):
        """Exact comparison with nested JSON objects."""
        c = ResultComparator("exact")
        assert c.compare('{"a": 1, "b": {"c": 2}}', '{"a": 1, "b": {"c": 2}}') is True

    def test_exact_match_string_fallback(self):
        """Exact comparison falls back to string comparison for non-JSON."""
        c = ResultComparator("exact")
        assert c.compare("hello world", "hello world") is True

    def test_exact_mismatch_string_fallback(self):
        """String comparison should detect differences."""
        c = ResultComparator("exact")
        assert c.compare("hello", "world") is False

    def test_exact_match_json_array_order_matters(self):
        """Exact mode: array order matters."""
        c = ResultComparator("exact")
        assert c.compare("[1, 2]", "[2, 1]") is False

    def test_exact_match_bool(self):
        """Exact comparison with booleans."""
        c = ResultComparator("exact")
        assert c.compare("true", "true") is True
        assert c.compare("true", "false") is False

    def test_exact_match_null(self):
        """Exact comparison with null."""
        c = ResultComparator("exact")
        assert c.compare("null", "null") is True

    # ── Unordered Mode ──

    def test_unordered_match_list(self):
        """Unordered comparison with lists in different order."""
        c = ResultComparator("unordered")
        assert c.compare("[1, 2, 3]", "[3, 1, 2]") is True

    def test_unordered_mismatch_list(self):
        """Unordered comparison should fail for different elements."""
        c = ResultComparator("unordered")
        assert c.compare("[1, 2, 3]", "[1, 2, 4]") is False

    def test_unordered_match_nested(self):
        """Unordered comparison with nested lists."""
        c = ResultComparator("unordered")
        assert c.compare("[[1, 2], [3, 4]]", "[[3, 4], [1, 2]]") is True

    def test_unordered_mismatch_different_length(self):
        """Unordered comparison should fail for different lengths."""
        c = ResultComparator("unordered")
        assert c.compare("[1, 2]", "[1, 2, 3]") is False

    def test_unordered_non_list_falls_back_to_exact(self):
        """Unordered comparison falls back to exact for non-list values."""
        c = ResultComparator("unordered")
        assert c.compare("42", "42") is True
        assert c.compare("42", "43") is False

    def test_unordered_match_string_fallback(self):
        """Unordered comparison string fallback."""
        c = ResultComparator("unordered")
        assert c.compare("hello", "hello") is True

    def test_unordered_match_nested_unordered(self):
        """Unordered comparison sorts only the top-level list (not nested)."""
        c = ResultComparator("unordered")
        # The unordered mode normalizes and sorts the top-level list only
        # [[3, 1], [2, 4]] normalizes to [(3, 1), (2, 4)] sorted: [(2, 4), (3, 1)]
        # [[2, 4], [3, 1]] normalizes to [(2, 4), (3, 1)] sorted: [(2, 4), (3, 1)]
        assert c.compare('[[3, 1], [2, 4]]', '[[2, 4], [3, 1]]') is True
        assert c.compare('[[1, 2], [3, 4]]', '[[3, 4], [1, 2]]') is True

    # ── Float Mode ──

    def test_float_match_single_value(self):
        """Float comparison with matching single values."""
        c = ResultComparator("float", precision=1e-5)
        assert c.compare("3.14159", "3.14159") is True

    def test_float_match_within_precision(self):
        """Float comparison with values within precision."""
        c = ResultComparator("float", precision=1e-2)
        assert c.compare("3.14159", "3.142") is True

    def test_float_mismatch_outside_precision(self):
        """Float comparison should fail for values outside precision."""
        c = ResultComparator("float", precision=1e-5)
        assert c.compare("3.14159", "3.14") is False

    def test_float_match_list(self):
        """Float comparison with lists of floats."""
        c = ResultComparator("float", precision=1e-2)
        assert c.compare("[1.0, 2.001, 3.0]", "[1.0, 2.0, 3.0]") is True

    def test_float_mismatch_list_length(self):
        """Float comparison should fail for different list lengths."""
        c = ResultComparator("float")
        assert c.compare("[1.0, 2.0]", "[1.0]") is False

    def test_float_match_integer_values(self):
        """Float comparison with integer values."""
        c = ResultComparator("float")
        assert c.compare("42", "42.0") is True

    def test_float_non_number_falls_back_to_exact(self):
        """Float comparison falls back to exact for non-numeric values."""
        c = ResultComparator("float")
        assert c.compare('"hello"', '"hello"') is True

    def test_float_custom_precision(self):
        """Float comparison with custom precision."""
        c = ResultComparator("float", precision=0.5)
        assert c.compare("10.0", "10.4") is True
        assert c.compare("10.0", "10.6") is False

    # ── Edge Cases ──

    def test_empty_strings(self):
        """Comparison with empty strings."""
        c = ResultComparator("exact")
        assert c.compare("", "") is True

    def test_whitespace_handling(self):
        """String comparison strips whitespace (fallback for non-JSON)."""
        c = ResultComparator("exact")
        assert c.compare("  hello  ", "  hello  ") is True
        # Non-JSON fallback uses strip(), so padded strings can match
        assert c.compare("hello", "  hello  ") is True

    def test_invalid_json_in_exact(self):
        """Invalid JSON should fall back to string comparison."""
        c = ResultComparator("exact")
        assert c.compare("{invalid}", "{invalid}") is True
        assert c.compare("{invalid}", "{other}") is False

    def test_comparison_error_returns_false(self):
        """If comparison raises an exception, return False."""
        c = ResultComparator("exact")

        # Create a scenario that causes a comparison error
        # Pass None-like values as strings that are valid but complex
        result = c.compare("[1, 2", "[1, 2]")  # Malformed JSON
        # Should fall back to string comparison
        assert result is False

    def test_default_mode_is_exact(self):
        """Default mode should be exact."""
        c = ResultComparator()
        assert c.mode == "exact"
        assert c.compare("hello", "hello") is True
        assert c.compare("hello", "world") is False

    def test_unknown_mode_falls_back_to_exact(self):
        """Unknown comparison mode should fall back to exact."""
        c = ResultComparator("unknown_mode")
        assert c.compare("test", "test") is True
        assert c.compare("test", "other") is False

    def test_large_precision_float(self):
        """Float comparison with large precision."""
        c = ResultComparator("float", precision=1.0)
        assert c.compare("100", "100.9") is True
        assert c.compare("100", "101.0") is False

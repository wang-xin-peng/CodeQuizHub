"""
Result Comparator - Compares actual output with expected output.
Supports multiple comparison modes: exact, unordered, float.
"""

import json
import logging

logger = logging.getLogger("comparator")


class ResultComparator:
    def __init__(self, mode: str = "exact", precision: float = 1e-5):
        self.mode = mode
        self.precision = precision

    def compare(self, actual: str, expected: str) -> bool:
        """Compare actual output with expected output based on mode."""
        try:
            if self.mode == "exact":
                return self._exact_compare(actual, expected)
            elif self.mode == "unordered":
                return self._unordered_compare(actual, expected)
            elif self.mode == "float":
                return self._float_compare(actual, expected)
            else:
                return self._exact_compare(actual, expected)
        except Exception as e:
            logger.warning(f"Comparison error: {e}")
            return False

    def _exact_compare(self, actual: str, expected: str) -> bool:
        """Exact match after JSON normalization."""
        try:
            actual_val = json.loads(actual)
            expected_val = json.loads(expected)
            return actual_val == expected_val
        except json.JSONDecodeError:
            # Fallback to string comparison (strip whitespace)
            return actual.strip() == expected.strip()

    def _unordered_compare(self, actual: str, expected: str) -> bool:
        """Compare lists without considering order."""
        try:
            actual_val = json.loads(actual)
            expected_val = json.loads(expected)

            if isinstance(actual_val, list) and isinstance(expected_val, list):
                return sorted(self._normalize(actual_val)) == sorted(self._normalize(expected_val))
            return actual_val == expected_val
        except json.JSONDecodeError:
            return actual.strip() == expected.strip()

    def _float_compare(self, actual: str, expected: str) -> bool:
        """Compare with floating point precision."""
        try:
            actual_val = json.loads(actual)
            expected_val = json.loads(expected)

            if isinstance(actual_val, (int, float)) and isinstance(expected_val, (int, float)):
                return abs(float(actual_val) - float(expected_val)) < self.precision

            if isinstance(actual_val, list) and isinstance(expected_val, list):
                if len(actual_val) != len(expected_val):
                    return False
                return all(
                    abs(float(a) - float(e)) < self.precision
                    for a, e in zip(actual_val, expected_val)
                )

            return actual_val == expected_val
        except (json.JSONDecodeError, TypeError, ValueError):
            return actual.strip() == expected.strip()

    def _normalize(self, val):
        """Normalize value for sorting (convert nested lists to tuples)."""
        if isinstance(val, list):
            return tuple(self._normalize(item) for item in val)
        return val

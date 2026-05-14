"""Language configurations for the judge system."""

from languages.python import PYTHON_CONFIG
from languages.java import JAVA_CONFIG
from languages.c import C_CONFIG
from languages.cpp import CPP_CONFIG

LANGUAGE_CONFIGS = {
    "python": PYTHON_CONFIG,
    "java": JAVA_CONFIG,
    "c": C_CONFIG,
    "cpp": CPP_CONFIG,
}


def get_language_config(language: str) -> dict:
    if language not in LANGUAGE_CONFIGS:
        raise ValueError(f"Unsupported language: {language}")
    return LANGUAGE_CONFIGS[language]

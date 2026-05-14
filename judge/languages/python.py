"""Python language configuration."""


def assemble_python(prelude: str, user_code: str, driver: str) -> str:
    parts = []
    if prelude:
        parts.append(f"# === Prelude ===\n{prelude}")
    parts.append(f"# === Solution ===\n{user_code}")
    parts.append(f"# === Driver ===\n{driver}")
    return "\n\n".join(parts)


PYTHON_CONFIG = {
    "name": "python",
    "display_name": "Python 3.11",
    "image": "codequizhub-sandbox-python",
    "source_file": "solution.py",
    "compile_command": None,
    "run_command": "python3 solution.py",
    "assemble": assemble_python,
}

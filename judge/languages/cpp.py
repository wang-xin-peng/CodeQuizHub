"""C++ language configuration."""


def assemble_cpp(prelude: str, user_code: str, driver: str) -> str:
    parts = []
    if prelude:
        parts.append(f"// === Prelude ===\n{prelude}")
    parts.append(f"// === Solution ===\n{user_code}")
    parts.append(f"// === Driver ===\n{driver}")
    return "\n\n".join(parts)


CPP_CONFIG = {
    "name": "cpp",
    "display_name": "G++ 12 (C++17)",
    "image": "codequizhub-sandbox-cpp",
    "source_file": "solution.cpp",
    "compile_command": "g++ -o solution solution.cpp -std=c++17 -O2",
    "run_command": "./solution",
    "assemble": assemble_cpp,
}

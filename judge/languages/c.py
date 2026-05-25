"""C language configuration."""


def assemble_c(prelude: str, user_code: str, driver: str) -> str:
    # Always include common headers first so user code can use malloc, NULL, etc.
    parts = [
        "#include <stdio.h>",
        "#include <stdlib.h>",
        "#include <string.h>",
    ]
    if prelude:
        parts.append(f"/* === Prelude === */\n{prelude}")
    parts.append(f"/* === Solution === */\n{user_code}")
    parts.append(f"/* === Driver === */\n{driver}")
    return "\n\n".join(parts)


C_CONFIG = {
    "name": "c",
    "display_name": "GCC 12 (C17)",
    "image": "codequizhub-sandbox-c",
    "source_file": "solution.c",
    "compile_command": "gcc -o solution solution.c -I/usr/include/cjson -lcjson -lm -std=c17",
    "run_command": "./solution",
    "assemble": assemble_c,
}

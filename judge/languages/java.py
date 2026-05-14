"""Java language configuration."""


def assemble_java(prelude: str, user_code: str, driver: str) -> str:
    parts = []
    if prelude:
        parts.append(f"// === Prelude ===\n{prelude}")
    parts.append(f"// === Solution ===\n{user_code}")
    parts.append(f"// === Driver ===\n{driver}")
    return "\n\n".join(parts)


JAVA_CONFIG = {
    "name": "java",
    "display_name": "Java 17",
    "image": "codequizhub-sandbox-java",
    "source_file": "Solution.java",
    "compile_command": "javac -cp .:json.jar *.java",
    "run_command": "java -cp .:json.jar Main",
    "assemble": assemble_java,
}

"""
Docker Sandbox Executor - Runs user code in an isolated Docker container.
"""

import asyncio
import json
import logging
import os
import tempfile
import time

import docker
from docker.errors import ContainerError, ImageNotFound, APIError

logger = logging.getLogger("executor")

# Docker client
docker_client = docker.from_env()

IMAGE_MAP = {
    "python": "codequizhub-sandbox-python",
    "java": "codequizhub-sandbox-java",
    "c": "codequizhub-sandbox-c",
    "cpp": "codequizhub-sandbox-cpp",
}

COMPILE_COMMANDS = {
    "python": None,  # interpreted
    "java": "javac -cp .:json.jar Solution.java Main.java",
    "c": "gcc -o solution solution.c -lm -ljson-c",
    "cpp": "g++ -o solution solution.cpp -std=c++17",
}

RUN_COMMANDS = {
    "python": "python3 solution.py",
    "java": "java -cp .:json.jar Main",
    "c": "./solution",
    "cpp": "./solution",
}

SOURCE_FILES = {
    "python": "solution.py",
    "java": "Solution.java",
    "c": "solution.c",
    "cpp": "solution.cpp",
}


class DockerExecutor:
    def __init__(self, language: str, time_limit_ms: int = 1000, memory_limit_mb: int = 256):
        self.language = language
        self.time_limit_ms = time_limit_ms
        self.memory_limit_mb = memory_limit_mb
        self.image = IMAGE_MAP.get(language, "codequizhub-sandbox-python")

    async def execute(self, code: str, input_json: str) -> dict:
        """
        Execute code in Docker sandbox.
        Returns dict with: status, output, error, time_used, memory_used
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_sync, code, input_json)

    def _execute_sync(self, code: str, input_json: str) -> dict:
        """Synchronous Docker execution."""
        source_file = SOURCE_FILES[self.language]
        compile_cmd = COMPILE_COMMANDS.get(self.language)
        run_cmd = RUN_COMMANDS[self.language]

        # Escape single quotes in input for shell
        escaped_input = input_json.replace("'", "'\\''")

        # Build the command to run inside container
        if compile_cmd:
            # Compiled language: compile then run
            full_cmd = f"sh -c 'cd /workspace && {compile_cmd} 2>&1 && {run_cmd} '\\'{escaped_input}\\''"
        else:
            # Interpreted language: run directly
            full_cmd = f"sh -c 'cd /workspace && {run_cmd} '\\'{escaped_input}\\''"

        # Timeout in seconds (add 2s buffer)
        timeout_s = (self.time_limit_ms / 1000) + 2

        try:
            # Check if image exists
            try:
                docker_client.images.get(self.image)
            except ImageNotFound:
                logger.warning(f"Image {self.image} not found, using python fallback")
                self.image = "python:3.11-slim"

            start_time = time.time()

            container = docker_client.containers.run(
                image=self.image,
                command=full_cmd,
                mem_limit=f"{self.memory_limit_mb}m",
                nano_cpus=1_000_000_000,  # 1 CPU
                network_disabled=True,
                read_only=False,  # Need write for /workspace
                user="nobody",
                working_dir="/workspace",
                volumes={},
                stdin_open=False,
                detach=True,
                environment={"PYTHONDONTWRITEBYTECODE": "1"},
            )

            # Copy source code into container
            import tarfile
            import io

            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                code_bytes = code.encode('utf-8')
                info = tarfile.TarInfo(name=source_file)
                info.size = len(code_bytes)
                tar.addfile(info, io.BytesIO(code_bytes))
            tar_stream.seek(0)
            container.put_archive("/workspace", tar_stream)

            # Execute
            exec_result = container.exec_run(
                full_cmd,
                demux=True,
            )

            # Wait for container to finish
            result = container.wait(timeout=timeout_s)
            end_time = time.time()

            time_used_ms = int((end_time - start_time) * 1000)

            # Get logs
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')

            # Get memory usage stats
            try:
                stats = container.stats(stream=False)
                memory_used_kb = stats.get("memory_stats", {}).get("max_usage", 0) // 1024
            except Exception:
                memory_used_kb = 0

            # Cleanup container
            container.remove(force=True)

            exit_code = result.get("StatusCode", -1)

            # Check time limit
            if time_used_ms > self.time_limit_ms:
                return {
                    "status": "timeout",
                    "output": "",
                    "error": "Time Limit Exceeded",
                    "time_used": time_used_ms,
                    "memory_used": memory_used_kb,
                }

            # Check compilation error (for compiled languages)
            if compile_cmd and exit_code != 0 and "error" in stderr.lower():
                return {
                    "status": "compilation_error",
                    "output": "",
                    "error": stderr[:2000],
                    "time_used": time_used_ms,
                    "memory_used": memory_used_kb,
                }

            # Check runtime error
            if exit_code != 0:
                return {
                    "status": "runtime_error",
                    "output": stdout,
                    "error": stderr[:2000] if stderr else f"Exit code: {exit_code}",
                    "time_used": time_used_ms,
                    "memory_used": memory_used_kb,
                }

            return {
                "status": "success",
                "output": stdout.strip(),
                "error": None,
                "time_used": time_used_ms,
                "memory_used": memory_used_kb,
            }

        except docker.errors.ContainerError as e:
            return {
                "status": "runtime_error",
                "output": "",
                "error": str(e)[:2000],
                "time_used": 0,
                "memory_used": 0,
            }
        except Exception as e:
            logger.error(f"Docker execution error: {e}", exc_info=True)
            return {
                "status": "runtime_error",
                "output": "",
                "error": f"Execution error: {str(e)[:500]}",
                "time_used": 0,
                "memory_used": 0,
            }

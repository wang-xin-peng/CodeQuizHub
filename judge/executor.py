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
    "java": "javac -cp .:json.jar Solution.java",
    "c": "gcc -o solution solution.c -I/usr/include/cjson -lcjson -lm",
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
        input_file = "input.json"

        # Separate compile and run so that only execution time is measured
        if compile_cmd:
            compile_only_cmd = f"sh -c 'cd /workspace && {compile_cmd}'"
            run_only_cmd = f"sh -c 'cd /workspace && {run_cmd} \"$(cat {input_file})\"'"
        else:
            compile_only_cmd = None
            run_only_cmd = f"sh -c 'cd /workspace && {run_cmd} \"$(cat {input_file})\"'"

        # Timeout in seconds (add 2s buffer)
        timeout_s = (self.time_limit_ms / 1000) + 2

        try:
            # Check if image exists, try to pull if not
            try:
                docker_client.images.get(self.image)
            except ImageNotFound:
                logger.warning(f"Image {self.image} not found, attempting to pull")
                try:
                    docker_client.images.pull(self.image)
                except Exception:
                    raise RuntimeError(
                        f"Docker image '{self.image}' not found and could not be pulled. "
                        f"Please build it:\n"
                        f"  docker compose --profile sandbox build sandbox-{self.language}"
                    )

            # Create tar archive with source code and input data
            import tarfile
            import io

            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                code_bytes = code.encode('utf-8')
                info = tarfile.TarInfo(name=source_file)
                info.size = len(code_bytes)
                tar.addfile(info, io.BytesIO(code_bytes))
                input_bytes = input_json.encode('utf-8')
                info2 = tarfile.TarInfo(name=input_file)
                info2.size = len(input_bytes)
                tar.addfile(info2, io.BytesIO(input_bytes))
            tar_stream.seek(0)

            # Start container with sleep to keep it alive, then copy files and exec
            container = docker_client.containers.create(
                image=self.image,
                command="sleep 30",
                mem_limit=f"{self.memory_limit_mb}m",
                nano_cpus=1_000_000_000,  # 1 CPU
                network_disabled=True,
                read_only=False,
                user="nobody",
                working_dir="/workspace",
                stdin_open=False,
                detach=True,
                environment={"PYTHONDONTWRITEBYTECODE": "1"},
            )
            container.start()

            # Copy source code and input data into container
            container.put_archive("/workspace", tar_stream)

            # ── Step 1: Compile (not timed) ──
            if compile_only_cmd:
                c_result = container.exec_run(compile_only_cmd, demux=True)
                c_out, c_err = c_result.output
                c_out = c_out.decode('utf-8', errors='replace') if c_out else ""
                c_err = c_err.decode('utf-8', errors='replace') if c_err else ""
                c_exit = c_result.exit_code

                if c_exit != 0:
                    error_msg = c_err or c_out or f"Compilation failed (exit={c_exit})"
                    logger.info(f"compilation failed: exit={c_exit} stderr={c_err[:300]} stdout={c_out[:300]}")
                    container.remove(force=True)
                    return {
                        "status": "compilation_error",
                        "output": "",
                        "error": error_msg[:2000],
                        "time_used": 0,
                        "memory_used": 0,
                    }

            # ── Step 2: Run (timed) ──
            start_time = time.time()
            exec_result = container.exec_run(run_only_cmd, demux=True)
            end_time = time.time()

            time_used_ms = int((end_time - start_time) * 1000)

            stdout, stderr = exec_result.output
            stdout = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr = stderr.decode('utf-8', errors='replace') if stderr else ""
            exit_code = exec_result.exit_code

            logger.info(f"exec_run took {time_used_ms}ms exit={exit_code} stderr={stderr[:300]}")

            # Get memory usage stats
            try:
                stats = container.stats(stream=False)
                memory_used_kb = stats.get("memory_stats", {}).get("max_usage", 0) // 1024
            except Exception:
                memory_used_kb = 0

            # Cleanup container
            container.remove(force=True)

            # Check time limit
            if time_used_ms > self.time_limit_ms:
                return {
                    "status": "timeout",
                    "output": "",
                    "error": "Time Limit Exceeded",
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

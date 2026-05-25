"""Diagnose Docker C++ sandbox execution time."""
import docker, time, tarfile, io

client = docker.from_env()
image = "codequizhub-sandbox-cpp"

# Create tar with test file
code = b"vector<int> twoSum(vector<int>& nums, int target) { return {}; }"
tar_stream = io.BytesIO()
with tarfile.open(fileobj=tar_stream, mode="w") as tar:
    info = tarfile.TarInfo(name="solution.cpp")
    info.size = len(code)
    tar.addfile(info, io.BytesIO(code))
tar_stream.seek(0)

# Create tar with input
input_json = b'{"nums": [2,7,11,15], "target": 9}'
input_tar = io.BytesIO()
with tarfile.open(fileobj=input_tar, mode="w") as tar:
    info2 = tarfile.TarInfo(name="input.json")
    info2.size = len(input_json)
    tar.addfile(info2, io.BytesIO(input_json))
input_tar.seek(0)

# Start container
container = client.containers.create(image, command="sleep 30", working_dir="/workspace", detach=True)
t_start = time.time()
container.start()
container.put_archive("/workspace", tar_stream)
container.put_archive("/workspace", input_tar)
print(f"Container setup: {(time.time() - t_start)*1000:.0f}ms")

# Time just the compile
t0 = time.time()
exec_result = container.exec_run(
    'sh -c "cd /workspace && g++ -o solution solution.cpp -std=c++17 2>&1"',
    demux=True,
)
t1 = time.time()
stderr = exec_result.output[1].decode() if exec_result.output[1] else "(none)"
print(f"Compile time: {(t1-t0)*1000:.0f}ms, exit={exec_result.exit_code}, stderr={stderr}")

# Time just the run
t2 = time.time()
exec_result2 = container.exec_run(
    'sh -c "cd /workspace && ./solution \"$(cat input.json)\""',
    demux=True,
)
t3 = time.time()
stdout = exec_result2.output[0].decode() if exec_result2.output[0] else ""
print(f"Run time: {(t3-t2)*1000:.0f}ms, exit={exec_result2.exit_code}, stdout={stdout}")

container.remove(force=True)
print("Done.")

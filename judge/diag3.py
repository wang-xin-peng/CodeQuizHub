"""Diagnose exec_run timing inside container."""
import docker, time, tarfile, io

client = docker.from_env()
code = """#include <iostream>
#include <string>
#include <vector>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using namespace std;

vector<int> twoSum(vector<int>& nums, int target) { return {}; }

int main(int argc, char* argv[]) {
    if (argc < 2) return 1;
    json input = json::parse(argv[1]);
    vector<int> nums = input["nums"].get<vector<int>>();
    int target = input["target"];
    auto result = twoSum(nums, target);
    cout << json(result).dump() << endl;
    return 0;
}
"""

input_json = '{"nums": [2,7,11,15], "target": 9}'

tar_stream = io.BytesIO()
with tarfile.open(fileobj=tar_stream, mode="w") as tar:
    tar.addfile(tarfile.TarInfo(name="solution.cpp"), io.BytesIO(code.encode()))
    tar.addfile(tarfile.TarInfo(name="input.json"), io.BytesIO(input_json.encode()))
tar_stream.seek(0)

container = client.containers.create(
    "codequizhub-sandbox-cpp",
    command="sleep 30",
    mem_limit="256m",
    nano_cpus=1000000000,
    network_disabled=True,
    user="nobody",
    working_dir="/workspace",
    detach=True,
)
container.start()
container.put_archive("/workspace", tar_stream)

# Use a list command to avoid shlex quoting issues
full_cmd = [
    "sh", "-c",
    "cd /workspace && g++ -o solution solution.cpp -std=c++17 2>&1 && ./solution \"$(cat input.json)\""
]

t0 = time.time()
result = container.exec_run(full_cmd, demux=True)
t1 = time.time()

elapsed = int((t1 - t0) * 1000)
out = result.output[0].decode() if result.output[0] else ""
err = result.output[1].decode() if result.output[1] else ""
print(f"EXEC_RUN_TIME: {elapsed}ms")
print(f"EXIT_CODE: {result.exit_code}")
print(f"STDOUT: {out[:500]}")
print(f"STDERR: {err[:500]}")
container.remove(force=True)

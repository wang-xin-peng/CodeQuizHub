"""Diagnose Docker C++ sandbox execution time (simulating executor exactly)."""
import docker, time, tarfile, io

client = docker.from_env()
image = "codequizhub-sandbox-cpp"

# Full assembled code as the assembler would produce
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

# Create tar with source + input
tar_stream = io.BytesIO()
with tarfile.open(fileobj=tar_stream, mode="w") as tar:
    info = tarfile.TarInfo(name="solution.cpp")
    info.size = len(code)
    tar.addfile(info, io.BytesIO(code.encode()))
    info2 = tarfile.TarInfo(name="input.json")
    info2.size = len(input_json)
    tar.addfile(info2, io.BytesIO(input_json.encode()))
tar_stream.seek(0)

# Container setup (NOT timed in the fixed executor)
container = client.containers.create(
    image, command="sleep 30",
    mem_limit="256m", nano_cpus=1_000_000_000,
    network_disabled=True, user="nobody",
    working_dir="/workspace", detach=True,
)
container.start()
container.put_archive("/workspace", tar_stream)

# === This is what the fixed executor times ===
full_cmd = 'sh -c ' + "'cd /workspace && g++ -o solution solution.cpp -std=c++17 2>&1 && ./solution \"$(cat input.json)\"'"

t0 = time.time()
result = container.exec_run(full_cmd, demux=True)
t1 = time.time()

elapsed = int((t1 - t0) * 1000)
stdout = result.output[0].decode() if result.output[0] else ""
stderr = result.output[1].decode() if result.output[1] else ""
print(f"exec_run took: {elapsed}ms")
print(f"exit_code: {result.exit_code}")
print(f"stdout: {stdout[:300]}")
print(f"stderr: {stderr[:300]}")
container.remove(force=True)
print("Done.")

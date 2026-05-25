"""
种子脚本：向 CodeQuizHub 系统添加"计数质数"题目。
使用 Prelude 代码提供 isPrime 辅助函数。

使用方法：
    python scripts/reference/countPrimes/seed_count_primes.py [--url BASE_URL] [--email EMAIL] [--password PASSWORD]
"""

import argparse
import sys

import httpx

# ─── Problem Definition ─────────────────────────────────────────────────────

PROBLEM_PAYLOAD = {
    "title": "计数质数",
    "description": """统计所有小于非负整数 `n` 的质数的数量。

**提示：**
- `0 <= n <= 5 * 10⁶`

Prelude 中已提供 `isPrime` 辅助函数，你可以直接调用。
""",
    "difficulty": "medium",
    "time_limit": 2000,
    "memory_limit": 256,
    "tags": ["math", "prelude-test"],
    "compare_mode": "exact",
    "signatures": [
        {
            "language": "python",
            "function_name": "countPrimes",
            "parameters": [
                {"name": "n", "type": "int", "description": "非负整数上限"},
            ],
            "return_type": "int",
            "code_template": "class Solution:\n    def countPrimes(self, n: int) -> int:\n        # TODO: implement your solution here\n        return 0\n",
            "prelude_code": "def isPrime(x: int) -> bool:\n    \"\"\"Return True if x is a prime number.\"\"\"\n    if x < 2:\n        return False\n    i = 2\n    while i * i <= x:\n        if x % i == 0:\n            return False\n        i += 1\n    return True\n",
            "driver_template": None,
        },
        {
            "language": "java",
            "function_name": "countPrimes",
            "parameters": [
                {"name": "n", "type": "int", "description": "非负整数上限"},
            ],
            "return_type": "int",
            "code_template": "class Solution {\n    public int countPrimes(int n) {\n        // TODO: implement your solution here\n        return 0;\n    }\n}\n",
            "prelude_code": "class Util {\n    public static boolean isPrime(int x) {\n        if (x < 2) return false;\n        for (int i = 2; i * i <= x; i++)\n            if (x % i == 0) return false;\n        return true;\n    }\n}\n",
            "driver_template": None,
        },
        {
            "language": "cpp",
            "function_name": "countPrimes",
            "parameters": [
                {"name": "n", "type": "int", "description": "非负整数上限"},
            ],
            "return_type": "int",
            "code_template": "class Solution {\npublic:\n    int countPrimes(int n) {\n        // TODO: implement your solution here\n        return 0;\n    }\n};\n",
            "prelude_code": "bool isPrime(int x) {\n    if (x < 2) return false;\n    for (int i = 2; i * i <= x; i++)\n        if (x % i == 0) return false;\n    return true;\n}\n",
            "driver_template": None,
        },
        {
            "language": "c",
            "function_name": "countPrimes",
            "parameters": [
                {"name": "n", "type": "int", "description": "非负整数上限"},
            ],
            "return_type": "int",
            "code_template": "int countPrimes(int n) {\n    // TODO: implement your solution here\n    return 0;\n}\n",
            "prelude_code": "#include <stdbool.h>\n\nbool isPrime(int x) {\n    if (x < 2) return false;\n    for (int i = 2; i * i <= x; i++)\n        if (x % i == 0) return false;\n    return true;\n}\n",
            "driver_template": None,
        },
    ],
    "test_cases": [
        {
            "input_params": {"n": 10},
            "expected_output": 4,
            "is_public": True,
            "description": "示例1：小于10的质数有4个",
        },
        {
            "input_params": {"n": 0},
            "expected_output": 0,
            "is_public": True,
            "description": "示例2：n=0",
        },
        {
            "input_params": {"n": 1},
            "expected_output": 0,
            "is_public": True,
            "description": "示例3：n=1",
        },
        {
            "input_params": {"n": 2},
            "expected_output": 0,
            "is_public": True,
            "description": "n=2，没有小于2的质数",
        },
        {
            "input_params": {"n": 20},
            "expected_output": 8,
            "is_public": False,
            "description": "20以内的质数",
        },
        {
            "input_params": {"n": 100},
            "expected_output": 25,
            "is_public": False,
            "description": "100以内的质数",
        },
        {
            "input_params": {"n": 500000},
            "expected_output": 41538,
            "is_public": False,
            "description": "大数测试",
        },
    ],
}


# ─── Helper Functions ───────────────────────────────────────────────────────

def login(client: httpx.Client, base_url: str, email: str, password: str) -> str:
    resp = client.post(
        f"{base_url}/api/auth/login",
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    data = resp.json()
    token = data["data"]["access_token"]
    print(f"  ✓ 登录成功 (email: {email})")
    return token


def create_problem(client: httpx.Client, base_url: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        f"{base_url}/api/problems",
        json=PROBLEM_PAYLOAD,
        headers=headers,
    )
    if resp.status_code == 201:
        data = resp.json()["data"]
        print(f"  ✓ 题目创建成功！ID: {data['id']}")
        print(f"    标题: {data['title']}")
        print(f"    难度: {data['difficulty']}")
        print(f"    标签: {data['tags']}")
        print(f"    测试用例: {len(PROBLEM_PAYLOAD['test_cases'])} 个")
        print(f"    语言: {[s['language'] for s in PROBLEM_PAYLOAD['signatures']]}")
        for s in PROBLEM_PAYLOAD["signatures"]:
            has_prelude = "有" if s.get("prelude_code") else "无"
            print(f"    {s['language']}: Prelude {has_prelude}")
        return data
    else:
        print(f"  ✗ 题目创建失败: {resp.status_code}")
        print(f"    错误: {resp.text}")
        sys.exit(1)


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="向 CodeQuizHub 添加'计数质数'题目")
    parser.add_argument("--url", default="http://localhost:8000", help="后端服务地址")
    parser.add_argument("--email", default="wxp3023244137@tju.edu.cn", help="教师邮箱")
    parser.add_argument("--password", default="12345678", help="教师密码")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    print("=" * 50)
    print("  CodeQuizHub - 题目种子脚本")
    print("  题目: 计数质数 (Count Primes)")
    print("  特性: 测试 Prelude 代码")
    print("=" * 50)
    print()

    with httpx.Client(timeout=30) as client:
        print("[1/2] 正在登录...")
        token = login(client, base_url, args.email, args.password)

        print("[2/2] 正在创建题目...")
        problem = create_problem(client, base_url, token)

    print()
    print("✅ 完成！")

if __name__ == "__main__":
    main()

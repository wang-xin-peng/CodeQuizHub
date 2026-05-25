"""
种子脚本：向 CodeQuizHub 系统添加"有效的括号"题目。

使用方法：
    python scripts/seed_valid_parentheses.py [--url BASE_URL] [--email EMAIL] [--password PASSWORD]

如果未提供凭据，会尝试使用默认的测试教师账号。
"""

import argparse
import json
import sys

import httpx

# ─── Problem Definition ─────────────────────────────────────────────────────

PROBLEM_PAYLOAD = {
    "title": "有效的括号",
    "description": """给定一个只包括 `'('`，`')'`，`'{'`，`'}'`，`'['`，`']'` 的字符串 `s` ，判断字符串是否有效。

**有效字符串需满足：**

1. 左括号必须用相同类型的右括号闭合。
2. 左括号必须以正确的顺序闭合。
3. 每个右括号都有一个对应的相同类型的左括号。

**提示：**

- `1 <= s.length <= 10⁴`
- `s` 仅由括号 `'()[]{}'` 组成""",
    "difficulty": "easy",
    "time_limit": 1000,
    "memory_limit": 256,
    "tags": ["stack", "string"],
    "compare_mode": "exact",
    "signatures": [
        {
            "language": "python",
            "function_name": "isValid",
            "parameters": [
                {"name": "s", "type": "str", "description": "括号字符串"},
            ],
            "return_type": "bool",
            "code_template": "class Solution:\n    def isValid(self, s: str) -> bool:\n        # TODO: implement your solution here\n        return False\n",
            "prelude_code": None,
            "driver_template": None,
        },
        {
            "language": "java",
            "function_name": "isValid",
            "parameters": [
                {"name": "s", "type": "String", "description": "括号字符串"},
            ],
            "return_type": "bool",
            "code_template": "class Solution {\n    public boolean isValid(String s) {\n        // TODO: implement your solution here\n        return false;\n    }\n}\n",
            "prelude_code": None,
            "driver_template": None,
        },
        {
            "language": "cpp",
            "function_name": "isValid",
            "parameters": [
                {"name": "s", "type": "string", "description": "括号字符串"},
            ],
            "return_type": "bool",
            "code_template": '#include <vector>\n#include <string>\n#include <iostream>\nusing namespace std;\n\nclass Solution {\npublic:\n    bool isValid(string s) {\n        // TODO: implement your solution here\n        return false;\n    }\n};\n',
            "prelude_code": None,
            "driver_template": None,
        },
    ],
    "test_cases": [
        {
            "input_params": {"s": "()"},
            "expected_output": True,
            "is_public": True,
            "description": "示例1：简单有效括号",
        },
        {
            "input_params": {"s": "()[]{}"},
            "expected_output": True,
            "is_public": True,
            "description": "示例2：多种括号组合",
        },
        {
            "input_params": {"s": "(]"},
            "expected_output": False,
            "is_public": True,
            "description": "示例3：括号不匹配",
        },
        {
            "input_params": {"s": "([)]"},
            "expected_output": False,
            "is_public": True,
            "description": "示例4：括号顺序错误",
        },
        {
            "input_params": {"s": "{[]}"},
            "expected_output": True,
            "is_public": False,
            "description": "嵌套正确",
        },
        {
            "input_params": {"s": ""},
            "expected_output": True,
            "is_public": False,
            "description": "边界情况：空字符串",
        },
        {
            "input_params": {"s": "((((("},
            "expected_output": False,
            "is_public": False,
            "description": "只有左括号",
        },
        {
            "input_params": {"s": "((()))"},
            "expected_output": True,
            "is_public": False,
            "description": "多层嵌套",
        },
    ],
}


# ─── Helper Functions ───────────────────────────────────────────────────────

def login(client: httpx.Client, base_url: str, email: str, password: str) -> str:
    """登录并返回 Bearer token."""
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
    """创建题目并返回题目数据."""
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
        print(f"    语言支持: {[s['language'] for s in PROBLEM_PAYLOAD['signatures']]}")
        return data
    else:
        print(f"  ✗ 题目创建失败: {resp.status_code}")
        print(f"    错误: {resp.text}")
        sys.exit(1)


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="向 CodeQuizHub 添加'有效的括号'题目")
    parser.add_argument("--url", default="http://localhost:8000", help="后端服务地址")
    parser.add_argument("--email", default="teacher@test.com", help="教师邮箱")
    parser.add_argument("--password", default="Test1234", help="教师密码")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    print("=" * 50)
    print("  CodeQuizHub - 题目种子脚本")
    print("  题目: 有效的括号 (Valid Parentheses)")
    print("=" * 50)
    print()

    with httpx.Client(timeout=30) as client:
        # Step 1: Login
        print("[1/2] 正在登录...")
        token = login(client, base_url, args.email, args.password)

        # Step 2: Create problem
        print("[2/2] 正在创建题目...")
        problem = create_problem(client, base_url, token)

    print()
    print("✅ 完成！现在学生可以使用此题目提交答案。")
    print(f"   题目 ID: {problem['id']}")


if __name__ == "__main__":
    main()

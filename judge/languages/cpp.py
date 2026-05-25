"""C++ language configuration."""

# Default prelude with commonly used STL headers and data structures.
# This is automatically prepended before user code so that standalone
# functions (without `class Solution`) can use vector, string, etc.
DEFAULT_PRELUDE = """#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>
#include <queue>
#include <stack>
#include <iostream>
#include <sstream>
#include <climits>
#include <cmath>

using namespace std;

struct ListNode {
    int val;
    ListNode *next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode *next) : val(x), next(next) {}
};

struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
};
"""


def assemble_cpp(prelude: str, user_code: str, driver: str) -> str:
    parts = []
    # Always include the default prelude first
    parts.append(f"// === Prelude ===\n{DEFAULT_PRELUDE}")
    if prelude:
        parts.append(f"// === Custom Prelude ===\n{prelude}")
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

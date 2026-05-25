"""
有效的括号 - 参考答案 (Python)

题目：给定一个只包括 '('，')'，'{'，'}'，'['，']' 的字符串 s，判断字符串是否有效。

有效字符串需满足：
1. 左括号必须用相同类型的右括号闭合。
2. 左括号必须以正确的顺序闭合。
3. 每个右括号都有一个对应的相同类型的左括号。
"""


class Solution:
    def isValid(self, s: str) -> bool:
        """使用栈来匹配括号。

        Args:
            s: 只包含括号字符的字符串

        Returns:
            如果括号有效返回 True，否则返回 False
        """
        stack = []
        # 右括号到左括号的映射
        mapping = {")": "(", "}": "{", "]": "["}

        for ch in s:
            if ch in mapping:
                # 遇到右括号：栈顶必须是对应的左括号
                if not stack or stack[-1] != mapping[ch]:
                    return False
                stack.pop()
            else:
                # 遇到左括号：入栈
                stack.append(ch)

        # 栈为空说明所有括号都匹配上了
        return not stack

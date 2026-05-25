/**
 * 有效的括号 - 参考答案 (Java)
 *
 * 题目：给定一个只包括 '('，')'，'{'，'}'，'['，']' 的字符串 s，判断字符串是否有效。
 *
 * 有效字符串需满足：
 * 1. 左括号必须用相同类型的右括号闭合。
 * 2. 左括号必须以正确的顺序闭合。
 * 3. 每个右括号都有一个对应的相同类型的左括号。
 */
import java.util.Stack;

class Solution {
    /**
     * 使用栈来匹配括号。
     *
     * @param s 只包含括号字符的字符串
     * @return 如果括号有效返回 true，否则返回 false
     */
    public boolean isValid(String s) {
        Stack<Character> stack = new Stack<>();

        for (char c : s.toCharArray()) {
            if (c == '(') {
                stack.push(')');
            } else if (c == '{') {
                stack.push('}');
            } else if (c == '[') {
                stack.push(']');
            } else {
                // 遇到右括号：栈顶必须是对应的右括号
                if (stack.isEmpty() || stack.pop() != c) {
                    return false;
                }
            }
        }

        // 栈为空说明所有括号都匹配上了
        return stack.isEmpty();
    }
}

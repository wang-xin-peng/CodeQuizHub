---
trigger: model_decision
description: 修复bug时
---
# 调试策略规范 v1.0
# ============================================
# AI 辅助开发的调试策略标准和要求
# 通过将 [ENABLED] 更改为 [DISABLED] 来启用/禁用规则
#
# 使用方法：
# 1. 将此文件放在 .qoder/rules/ 目录
# 2. 根据项目需求启用/禁用规则
# 3. 在 AI 对话中使用 @debugging-strategy-spec.zh-CN.md 引用
# 4. AI 将只遵循 ENABLED 的规则
#
# 依赖规范：crud-flow-verify-spec.zh-CN.md
# 最后更新：2026-05-20
# ============================================

## [规则 1] 端到端数据流追踪 [ENABLED]
# Bug 修复前必须完整追踪数据流

STATUS: ENABLED
PRIORITY: CRITICAL
说明：
- 修复前完整追踪"输入 → 处理 → 输出"的全链路
- 识别所有涉及的文件、函数、服务、容器
- 绘制数据流图（至少脑图），明确每个环节的职责
- 对 Java/Python 等编译/解释型语言，理解代码最终如何被组装和执行

后果：
- 只修表面症状，根因未除，导致多轮返工
- 修改了错误的位置，引入新 Bug

示例：

❌ 错误（仅修复表面症状）：
  - 用户报错 NameError: name 'Solution' is not defined
  - 直接修改模板生成 class Solution，未检查 driver 端是否匹配
  - 结果：模板改了但 driver 调用方式不匹配，仍报错

✅ 正确（完整数据流追踪）：
  1. 识别全链路：模板(生成代码) → 数据库(存储) → API(返回) → 前端(展示) → 用户编辑 → 提交 → judge-worker(组装) → Docker sandbox(执行)
  2. 检查每环节：template 输出格式、driver 期望格式、assembler 组合方式
  3. 模拟最终生成的代码，确认无问题
  4. 然后实施修复并验证


## [规则 2] 代码生成产物自检 [ENABLED]
# 动态生成代码时必须检查最终输出

STATUS: ENABLED
PRIORITY: CRITICAL
说明：
- 当系统使用 f-string、模板引擎等方式动态生成代码时
- 必须手动生成/模拟一次最终输出，检查语法正确性
- 特别注意缩进（模板缩进 + 变量内容缩进可能叠加）
- 注意多行替换场景下每行的缩进一致性

后果：
- 缩进叠加导致 IndentationError
- 生成的代码结构错误导致运行时异常

示例：

```python
# ❌ 错误：模板缩进 + 变量缩进叠加
call_line = '    result = func(input_data["key"])'  # 4 空格

return f'''
def main():
    input_data = json.loads(sys.argv[1])
    {call_line}      # 此处 f-string 又有 4 空格
    print(json.dumps(result))
'''
# 实际输出：8 空格缩进 → IndentationError

# ✅ 正确：只保留一种缩进源
call_line = 'result = func(input_data["key"])'  # 无前导空格

return f'''
def main():
    input_data = json.loads(sys.argv[1])
    {call_line}      # 仅此一处 4 空格
    print(json.dumps(result))
'''
# 实际输出：4 空格缩进 ✓
```

```python
# 多行替换场景的缩进规则：
# - 第一行由模板提供缩进
# - 后续行由变量内容自行提供缩进
call_line = 'sol = Solution()\n    result = sol.func(args)'
#          ^ 无缩进(模板提供)    ^ 自带4空格(函数体内)
```


## [规则 3] Docker 部署变更感知 [ENABLED]
# 修改容器内运行代码后必须重启容器

STATUS: ENABLED
PRIORITY: CRITICAL
说明：
- Docker 容器内运行的 Python/Node 等进程不会感知挂载卷文件变化
- 修改以下类型文件后必须重启相关容器：
  - 后端 API 代码（如 routers/、services/ 等）
  - Worker 服务代码（如 judge-worker 的 assembler.py）
  - 配置文件和启动脚本
- 使用 `docker compose restart <service>` 重启特定服务
- 如果怀疑更改未生效，重启容器是最直接的验证手段

后果：
- 修改代码但未重启 → 运行的是旧代码 → 以为没修好 → 浪费调试时间

示例：
```bash
# 检查容器状态
docker compose ps

# 重启特定服务
docker compose restart judge-worker
docker compose restart backend

# 验证重启完成
docker compose ps | grep -E "judge-worker|backend"
```


## [规则 4] 相似模式全局修复 [ENABLED]
# 发现 Bug 模式后全局搜索相似代码

STATUS: ENABLED
PRIORITY: HIGH
说明：
- 修复一个文件中的 Bug 后，搜索项目中是否存在相同模式的代码
- 使用 Grep 搜索关键词（如变量名、函数名、代码结构）
- 跨文件、跨语言对比类似逻辑，同步修复
- 特别关注"复制粘贴"导致的重复 Bug

后果：
- 只修复一处，另一处相同 Bug 在下一次触发时仍需修复
- 调试信心下降，用户体验割裂

示例：
❌ 错误（只修一处）：
  - 修复 judge/assembler.py 中的 call_line 缩进
  - 但 backend/app/routers/problems.py 有完全相同的问题
  - 结果：judge-worker 路径好了，但 inline 执行路径仍报错

✅ 正确（全局搜索）：
  - grep 搜索 call_line、driver 等关键词
  - 发现 problems.py 中同样存在
  - 同步修复，一次性解决所有路径


## [规则 5] 从错误信息追溯根因 [ENABLED]
# 错误栈信息必须完整分析

STATUS: ENABLED
PRIORITY: HIGH
说明：
- 仔细阅读整个错误栈，不要只看第一行
- 关注文件名、行号、调用链
- 区分"直接原因"（出错行）和"根本原因"（为什么这行会出错）
- 当修复后错误类型改变，说明前一个修复暴露了更深层问题

后果：
- 忽略错误栈细节导致误判根因
- 换了错误类型就以为修好了，实则只是进入下一层错误

示例：
```
# 原始错误栈
Traceback (most recent call last):
  File "/workspace/solution.py", line 22, in <module>
    main()
  File "/workspace/solution.py", line 17, in main
    sol = Solution()
NameError: name 'Solution' is not defined
                    ^^^^^^^^^ 根因是模板生成的代码不含 class Solution

# 修复后新错误
  File "/workspace/solution.py", line 17
    result = twoSum(input_data["nums"], input_data["target"])
IndentationError: unexpected indent
                    ^^^^^^^^^ 根因是生成代码时缩进叠加
```
- NameError 修复后 → IndentationError，说明进入了下一层问题
- 此时应检查生成代码的完整过程，而不是停在表面


## [规则 6] 系统架构感知调试 [ENABLED]
# 调试前必须理解系统部署架构

STATUS: ENABLED
PRIORITY: HIGH
说明：
- 调试任何问题前，先理解系统的部署架构：
  - 有哪些服务？如何通信？（API、队列、数据库）
  - 哪些代码在容器内运行？哪些在宿主机？
  - 代码如何从源文件变成运行时的进程？
- 关键文件：docker-compose.yml、Dockerfile、entrypoint 脚本
- 运行时配置环境变量、volume 挂载、网络配置

后果：
- 在不理解架构的情况下修改代码，可能导致修错地方或漏修
- 容器内运行的代码改了不重启=没改

示例：
```
检查清单：
□ 代码在容器内还是容器外运行？
□ 如果是容器内，volume 挂载了哪些目录？
□ 修改的文件是否被挂载到容器？
□ 容器内的进程是否能自动重载代码？
□ 是否需要重启容器使更改生效？
□ 是否有多个服务涉及同一份代码的修改？
```


## [规则 7] 增量修复验证闭环 [ENABLED]
# 每次修复后必须闭环验证

STATUS: ENABLED
PRIORITY: MEDIUM
说明：
- 每次修复后，用最直接的方式验证改动生效：
  - 本地单元测试
  - 手动构造输入输出测试
  - 通过 API 或 UI 执行端到端验证
- 如果无法本地验证，明确指出验证方法并请用户协助
- 验证成功后，记录验证结果和步骤

后果：
- 未经验证的修复=没修
- 依赖用户反复测试浪费精力

示例：
```
✅ 验证步骤：
1. 修改代码后重启相关服务
2. 准备测试用例（输入、期望输出）
3. 执行测试并比对结果
4. 确认错误不再出现
5. 截图/记录验证结果
```


# ============================================
# 启用规则摘要
# ============================================

✅ [规则 1] 端到端数据流追踪 - 修复前完整追踪数据全链路
✅ [规则 2] 代码生成产物自检 - 检查动态生成的代码缩进和结构
✅ [规则 3] Docker 部署变更感知 - 修改容器代码后必须重启
✅ [规则 4] 相似模式全局修复 - 找到一处 Bug 模式全局修复
✅ [规则 5] 从错误信息追溯根因 - 完整分析错误栈信息
✅ [规则 6] 系统架构感知调试 - 理解部署架构再动手
✅ [规则 7] 增量修复验证闭环 - 每次修复后闭环验证


# ============================================
# 版本历史
# ============================================
# v1.0 (2026-05-20) - 初始调试策略规范，包含 7 条规则
# 来源：CodeQuizHub 的 NameError + IndentationError 多轮调试复盘
# ============================================

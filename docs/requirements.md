# CodeQuizHub 需求分析文档

## 1. 项目概述

### 1.1 项目背景

CodeQuizHub 是一个在线编程作业测评平台，旨在为高校编程类课程提供从题目管理、作业发布到自动化评测的一站式解决方案。平台采用类似 LeetCode 的函数签名模式，教师为每道题定义函数签名和测试用例，学生只需实现核心函数逻辑即可提交评测。平台支持多种编程语言，通过自动化代码判题系统对学生提交的代码进行编译、运行和评测，帮助教师高效管理编程作业，帮助学生即时获取代码反馈。

### 1.2 项目目标

- 为教师提供便捷的课程管理、题目管理和作业管理功能
- 为学生提供在线编程、即时提交和评测反馈的学习体验
- 实现代码自动判题，支持多种编程语言
- 提供成绩统计与导出功能，辅助教学评估

### 1.3 目标用户

| 角色   | 描述                                         |
| ------ | -------------------------------------------- |
| 管理员 | 系统管理人员，负责用户管理、系统配置         |
| 教师   | 课程创建者，负责题目管理、作业发布、成绩管理 |
| 学生   | 课程学习者，完成编程作业并提交评测           |

---

## 2. 功能需求

### 2.1 用户管理模块

#### 2.1.1 注册与登录

- 支持用户名/邮箱 + 密码注册
- 支持登录、登出
- 注册时选择角色（教师/学生）
- 密码找回功能（通过邮箱验证）

#### 2.1.2 个人信息管理

- 查看和编辑个人资料（昵称、头像、简介）
- 修改密码
- 查看自己加入/创建的课程列表

#### 2.1.3 管理员功能

- 用户列表查看与管理（禁用/启用账号）
- 角色变更（如将学生升级为教师）
- 系统公告发布

---

### 2.2 课程管理模块

#### 2.2.1 创建课程（教师）

- 填写课程名称、描述
- 指定课程编程语言（C、C++、Java、Python）
- 生成课程邀请码（用于学生加入）
- 设置课程状态（进行中/已结课）

#### 2.2.2 课程管理（教师）

- 查看课程学生列表
- 导出学生列表与成绩
- 移除学生
- 编辑课程信息
- 删除/归档课程
- 查看课程下所有作业及整体完成情况

#### 2.2.3 加入课程（学生）

- 通过邀请码加入课程
- 查看已加入课程列表
- 退出课程

---

### 2.3 题目管理模块

#### 2.3.1 题目创建（教师）

- 填写题目标题、描述（支持 Markdown 格式，包含题目说明、示例、约束条件）
- 指定题目支持的编程语言
- 设置题目难度等级（简单/中等/困难）
- **定义函数签名（核心特性）**：

  - 为每种支持的编程语言定义函数签名
  - 包括：函数名、参数列表（参数名 + 类型）、返回值类型
  - 示例：
    ```
    // C
    int* twoSum(int* nums, int numsSize, int target, int* returnSize);

    // C++
    vector<int> twoSum(vector<int>& nums, int target);

    // Java
    public int[] twoSum(int[] nums, int target);

    // Python
    def twoSum(self, nums: List[int], target: int) -> List[int]:
    ```
- **生成代码模板**：

  - 根据函数签名自动生成各语言的代码模板（含类/函数骨架）
  - 学生打开题目时看到带有函数签名的代码框架，只需填写函数体
  - 教师可自定义模板内容（如添加辅助说明注释）
- 添加测试用例：

  - 支持多组测试用例
  - 区分公开测试用例（学生可见，用于调试）和隐藏测试用例（仅用于最终评测）
  - 测试用例格式：函数输入参数 → 期望返回值
  - 支持复杂数据结构的序列化输入（如数组、链表、树等）
- 设置时间限制和内存限制（可按语言分别设置）
- 添加题目标签（如：数组、链表、动态规划、排序等）

#### 2.3.2 题目管理（教师）

- 题目列表查看（支持按语言、难度、标签筛选）
- 编辑题目（含函数签名和测试用例）
- 删除题目
- 题目可复用于不同课程/作业
- 批量导入题目（可选）

#### 2.3.3 题目库

- 教师可创建个人题库
- 支持从题库中选题组成作业
- 支持题目的标签分类管理
- 题目支持按算法类别归档（数组、字符串、树、图、动态规划等）

#### 2.3.4 函数签名与数据类型支持

平台需为各编程语言提供统一的类型映射：

| 逻辑类型   | C                 | C++                     | Java     | Python             |
| ---------- | ----------------- | ----------------------- | -------- | ------------------ |
| 整数       | int               | int                     | int      | int                |
| 整数数组   | int*, int size    | vector\<int\>           | int[]    | List[int]          |
| 字符串     | char*             | string                  | String   | str                |
| 字符串数组 | char**, int size  | vector\<string\>        | String[] | List[str]          |
| 二维数组   | int**, rows, cols | vector\<vector\<int\>\> | int[][]  | List[List[int]]    |
| 链表节点   | struct ListNode*  | ListNode*               | ListNode | Optional[ListNode] |
| 二叉树节点 | struct TreeNode*  | TreeNode*               | TreeNode | Optional[TreeNode] |
| 布尔值     | int (0/1)         | bool                    | boolean  | bool               |

- 平台内置常用数据结构定义（ListNode、TreeNode 等），自动包含在代码模板中
- 教师也可自定义数据结构（写在题目的辅助代码区）

---

### 2.4 作业管理模块

#### 2.4.1 发布作业（教师）

- 选择课程 → 从题库中选择题目组成作业
- 设置作业标题和描述
- 设置作业起止时间（开始时间、截止时间）
- 发布/草稿状态切换

#### 2.4.2 作业查看（教师）

- 查看作业提交情况统计（已提交人数/总人数）
- 查看每个学生的提交详情
- 查看每道题的通过率

#### 2.4.3 作业完成（学生）

- 查看作业列表（按截止时间排序，区分未完成/已完成/已过期）
- 查看作业中的题目列表
- 针对每道题目进行编程和提交

---

### 2.5 在线编程与代码提交模块

#### 2.5.1 在线代码编辑器

- 左侧显示题目描述（Markdown 渲染），右侧为代码编辑区
- 代码编辑器（Monaco Editor）：
  - 语法高亮、自动补全、自动缩进
  - 编辑器内预填充代码模板（函数签名 + 空函数体）
  - 学生在函数体内编写实现代码
- 支持切换编程语言（切换时自动加载对应语言的代码模板）
- 代码自动保存（草稿功能，避免丢失）
- 代码重置（恢复为初始模板）

#### 2.5.2 运行与调试

- **运行测试**：用公开测试用例运行代码，查看每个用例的输入/标准输出/输出/期望值
- **自定义测试**：学生可自行输入测试参数进行调试
- 显示编译错误或运行时异常的详细信息

#### 2.5.3 代码提交

- 提交代码进行正式评测（使用全部测试用例，含隐藏用例）
- 查看提交历史列表（每次提交的时间、语言、状态、得分）
- 查看每次提交的详细评测结果（各测试用例通过情况）

---

### 2.6 自动判题模块（函数级评测）

#### 2.6.1 判题流程

采函数级判题，流程如下：

```
学生提交代码（仅函数实现）
       ↓
后端组装完整可执行代码：
  = 平台预置代码（数据结构定义、辅助函数）
  + 学生提交的函数实现
  + 测试驱动代码（调用函数、比对结果）
       ↓
发送到判题沙箱编译运行
       ↓
逐个测试用例执行，收集结果
       ↓
返回评测结果
```

#### 2.6.2 代码组装机制

- **预置代码（Prelude）**：平台为各语言提供的基础代码
  - 数据结构定义（ListNode、TreeNode 等）
  - 工具函数（数组构建、链表构建、树构建等）
  - 教师自定义的辅助代码
- **用户代码（Solution）**：学生提交的函数实现
- **驱动代码（Driver）**：平台自动生成的测试入口
  - 解析测试用例输入（从序列化格式反序列化为实际参数）
  - 调用学生实现的函数
  - 序列化函数返回值
  - 与期望输出进行比对

组装示例（Java）：

```java
/ === 预置代码 ===
class ListNode { int val; ListNode next; ... }

/ === 学生代码 ===
class Solution {
    public int[] twoSum(int[] nums, int target) {
        // 学生的实现
    }
}

/ === 驱动代码（平台自动生成）===
public class Main {
    public static void main(String[] args) {
        Solution sol = new Solution();
        // 解析输入、调用函数、比对输出
    }
}
```

#### 2.6.3 评测执行

- 支持多种编程语言的编译和运行（C、C++、Java、Python）
- 沙箱环境运行用户代码（Docker 容器隔离）
- 根据测试用例判定每个用例的结果：

  - AC（Accepted）：通过
  - WA（Wrong Answer）：答案错误
  - TLE（Time Limit Exceeded）：超时
  - MLE（Memory Limit Exceeded）：内存超限
  - RE（Runtime Error）：运行时错误
  - CE（Compilation Error）：编译错误
- 返回编译错误信息（如有）
- 记录每个用例的运行时间和内存占用

#### 2.6.4 结果比对策略

- 精确匹配：返回值与期望值完全一致
- 无序匹配：对于结果顺序不重要的题目（如"返回任意一个有效答案"），支持无序比对
- 浮点精度：浮点数结果支持设定误差范围（如 1e-5）
- 特殊判题：教师可提供自定义 checker（判题函数），用于特殊比对逻辑

#### 2.6.5 评分规则

- 按通过测试用例比例计分（如通过 8/10 个用例得 80 分）
- 作业总分 = 各题得分之和（或加权）
- 支持教师自定义评分权重
- 取最优提交得分（多次提交取最高分）

---

### 2.7 成绩管理模块

#### 2.7.1 成绩查看

- 教师：查看课程下所有学生的成绩汇总
- 教师：查看单个学生的详细答题情况
- 学生：查看自己在每次作业中的得分
- 学生：查看自己在课程中的总体成绩

#### 2.7.2 成绩导出（教师）

- 导出课程成绩为 Excel/CSV 格式
- 导出内容包括：学生姓名、学号、每次作业得分、总分
- 支持按作业/按学生两种维度导出

#### 2.7.3 数据统计

- 课程维度：平均分、最高分、最低分
- 作业维度：各题通过率、平均得分

---

## 3. 非功能需求

### 3.1 性能需求

| 指标         | 要求                             |
| ------------ | -------------------------------- |
| 页面加载时间 | 首屏加载 < 3 秒                  |
| 代码评测响应 | 单次评测 < 30 秒（含编译和运行） |
| 并发支持     | 支持至少 100 人同时在线提交评测  |
| 数据库查询   | 常规查询 < 500ms                 |

### 3.2 安全需求

- 用户密码加密存储（bcrypt 或同等算法）
- 代码执行沙箱隔离，防止恶意代码影响宿主系统
- 接口鉴权（JWT Token 认证）
- 防止 SQL 注入、XSS、CSRF 等常见攻击
- 敏感操作日志记录
- 代码提交防作弊（可选：代码相似度检测）

### 3.3 可用性需求

- 响应式设计，支持 PC 和平板访问
- 界面简洁直观，操作步骤清晰
- 关键操作有确认提示
- 错误信息友好且具有指导性

### 3.4 可维护性需求

- 前后端分离架构
- 代码规范统一，配置 Lint 工具
- 关键模块有单元测试覆盖
- 判题服务可独立扩展部署

### 3.5 兼容性需求

- 浏览器支持：Chrome、Firefox、Edge 最新两个大版本
- 判题语言支持可扩展（后续可增加 Go、Rust 等）

---

## 4. 系统架构概述

### 4.1 总体架构

```
┌─────────────────────────────────────────────────────┐
│                   前端（Web 客户端）                 │
│         React + TypeScript + Monaco Editor          │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────▼───────────────────────────────┐
│                  后端 API 服务                       │
│           RESTful API + 业务逻辑层                   │
└───────┬─────────────┬───────────────┬───────────────┘
        │             │               │
┌───────▼──────┐ ┌────▼─────┐ ┌──────▼───────┐
│   数据库      │ │ 消息队列  │ │  文件存储    │
│ PostgreSQL   │ │  Redis   │ │ (代码文件/    │
│              │ │          │ │  测试用例)    │
└──────────────┘ └────┬─────┘ └──────────────┘
                      │
              ┌───────▼────────┐
              │   判题服务      │
              │ (沙箱环境执行)  │
              │  Docker 容器   │
              └────────────────┘
```

### 4.2 核心模块划分

| 模块     | 职责                 |
| -------- | -------------------- |
| 用户服务 | 注册、登录、权限管理 |
| 课程服务 | 课程 CRUD、学生管理  |
| 题目服务 | 题目 CRUD、题库管理  |
| 作业服务 | 作业发布、提交管理   |
| 判题服务 | 代码编译、运行、评测 |
| 成绩服务 | 成绩统计、导出       |

---

## 5. 数据模型概要

### 5.1 核心实体

```
User（用户）
├── id, username, email, password_hash, role, avatar, created_at

Course（课程）
├── id, name, description, languages[], invite_code, status, teacher_id, created_at

CourseStudent（课程-学生关系）
├── id, course_id, student_id, joined_at

Problem（题目）
├── id, title, description, difficulty, time_limit, memory_limit,
│   tags[], compare_mode, teacher_id, created_at

ProblemFunctionSignature（题目函数签名，每种语言一条记录）
├── id, problem_id, language, function_name, parameters_json,
│   return_type, code_template, prelude_code, driver_template

TestCase（测试用例）
├── id, problem_id, input_params_json, expected_output_json,
│   is_public, order, description

Assignment（作业）
├── id, course_id, title, description, start_time, end_time,
│   max_submissions, late_policy, status, created_at

AssignmentProblem（作业-题目关系）
├── id, assignment_id, problem_id, score_weight, order

Submission（代码提交）
├── id, student_id, assignment_id, problem_id, language, code,
│   status, score, time_used, memory_used, submitted_at

SubmissionResult（提交评测详情）
├── id, submission_id, test_case_id, status, actual_output, time_used, memory_used

CodeDraft（代码草稿，自动保存）
├── id, student_id, problem_id, assignment_id, language, code, updated_at

Notification（通知）
├── id, user_id, type, title, content, is_read, created_at
```

### 5.2 函数签名数据结构说明

`ProblemFunctionSignature.parameters_json` 格式示例：

```json
[
  { "name": "nums", "type": "int[]", "description": "整数数组" },
  { "name": "target", "type": "int", "description": "目标值" }
]
```

`ProblemFunctionSignature.code_template` 示例（Java）：

```java
class Solution {
    public int[] twoSum(int[] nums, int target) {
        // 在此编写你的代码
    }
}
```

`TestCase.input_params_json` 格式示例：

```json
{
  "nums": [2, 7, 11, 15],
  "target": 9
}
```

`TestCase.expected_output_json` 格式示例：

```json
[0, 1]
```

---

## 6. 用户交互流程

### 6.1 教师核心流程

```
创建课程 → 创建题目 → 定义函数签名（各语言）→ 添加测试用例 → 从题库选题组成作业 → 发布作业
                                                                                    ↓
                                                          查看提交情况 ← 学生提交代码
                                                                                    ↓
                                                          查看/导出成绩
```

### 6.2 学生核心流程

```
通过邀请码加入课程 → 查看作业列表 → 选择题目 → 查看题目描述 + 函数签名
                                                              ↓
                                                   在代码模板中实现函数体
                                                              ↓
                                          运行测试（公开用例）← 调试修改
                                                              ↓
                                          提交代码 → 自动评测（全部用例）
                                                              ↓
                                          查看评测结果与成绩
```

---

## 7. 接口规划（RESTful API 概要）

### 7.1 用户相关

| 方法 | 路径               | 描述             |
| ---- | ------------------ | ---------------- |
| POST | /api/auth/register | 用户注册         |
| POST | /api/auth/login    | 用户登录         |
| GET  | /api/users/me      | 获取当前用户信息 |
| PUT  | /api/users/me      | 更新个人信息     |

### 7.2 课程相关

| 方法   | 路径                      | 描述             |
| ------ | ------------------------- | ---------------- |
| POST   | /api/courses              | 创建课程         |
| GET    | /api/courses              | 获取课程列表     |
| GET    | /api/courses/:id          | 获取课程详情     |
| PUT    | /api/courses/:id          | 更新课程         |
| DELETE | /api/courses/:id          | 删除课程         |
| POST   | /api/courses/join         | 学生加入课程     |
| GET    | /api/courses/:id/students | 获取课程学生列表 |

### 7.3 题目相关

| 方法   | 路径                               | 描述                         |
| ------ | ---------------------------------- | ---------------------------- |
| POST   | /api/problems                      | 创建题目                     |
| GET    | /api/problems                      | 获取题目列表                 |
| GET    | /api/problems/:id                  | 获取题目详情（含函数签名）   |
| PUT    | /api/problems/:id                  | 更新题目                     |
| DELETE | /api/problems/:id                  | 删除题目                     |
| POST   | /api/problems/:id/signatures       | 添加/更新函数签名            |
| GET    | /api/problems/:id/signatures/:lang | 获取指定语言的函数签名与模板 |
| POST   | /api/problems/:id/testcases        | 添加测试用例                 |
| PUT    | /api/problems/:id/testcases/:tcId  | 更新测试用例                 |
| DELETE | /api/problems/:id/testcases/:tcId  | 删除测试用例                 |

### 7.4 作业相关

| 方法 | 路径                         | 描述               |
| ---- | ---------------------------- | ------------------ |
| POST | /api/assignments             | 创建/发布作业      |
| GET  | /api/courses/:id/assignments | 获取课程下作业列表 |
| GET  | /api/assignments/:id         | 获取作业详情       |
| PUT  | /api/assignments/:id         | 更新作业           |

### 7.5 提交与评测

| 方法 | 路径                             | 描述                                 |
| ---- | -------------------------------- | ------------------------------------ |
| POST | /api/submissions                 | 提交代码（仅函数实现部分）           |
| GET  | /api/submissions/:id             | 获取提交结果                         |
| GET  | /api/assignments/:id/submissions | 获取作业的所有提交                   |
| POST | /api/problems/:id/run            | 运行测试（公开用例，不计入正式提交） |
| POST | /api/problems/:id/run-custom     | 自定义输入运行                       |

### 7.6 成绩相关

| 方法 | 路径                           | 描述         |
| ---- | ------------------------------ | ------------ |
| GET  | /api/courses/:id/grades        | 获取课程成绩 |
| GET  | /api/courses/:id/grades/export | 导出成绩     |

---

## 8. 技术选型

| 层次       | 选型                            |
| ---------- | ------------------------------- |
| 前端框架   | React 18 + TypeScript           |
| UI 组件库  | Ant Design 5                    |
| 代码编辑器 | Monaco Editor（VS Code 同款）   |
| 后端框架   | FastAPI (Python 3.11+)          |
| ORM        | SQLAlchemy 2.0 + Alembic        |
| 数据库     | PostgreSQL 16                   |
| 缓存/队列  | Redis 7（兼作缓存和消息队列）   |
| 判题沙箱   | Docker 容器隔离                 |
| 部署       | Docker Compose                  |

---

## 9. 项目里程碑规划

| 阶段     | 内容                             |
| -------- | -------------------------------- |
| 第一阶段 | 用户管理 + 课程管理基础功能      |
| 第二阶段 | 题目管理 + 作业发布功能          |
| 第三阶段 | 在线编辑器 + 代码提交 + 判题服务 |
| 第四阶段 | 成绩管理 + 数据统计 + 导出功能   |
| 第五阶段 | 通知系统 + 系统优化 + 部署上线   |

---

## 10. 风险与约束

| 风险                         | 应对措施                                 |
| ---------------------------- | ---------------------------------------- |
| 判题服务安全风险（恶意代码） | 使用 Docker 沙箱隔离，限制资源和网络访问 |
| 高并发提交导致判题延迟       | 引入消息队列，判题服务可水平扩展         |
| 代码抄袭问题                 | 可集成代码相似度检测工具                 |
| 多语言支持复杂度             | 初期先支持核心语言，后续逐步扩展         |

---

## 附录：术语表

| 术语 | 含义                                      |
| ---- | ----------------------------------------- |
| OJ   | Online Judge，在线评测系统                |
| AC   | Accepted，代码通过所有测试用例            |
| WA   | Wrong Answer，输出结果与期望不符          |
| TLE  | Time Limit Exceeded，运行超时             |
| MLE  | Memory Limit Exceeded，内存超限           |
| RE   | Runtime Error，运行时错误                 |
| CE   | Compilation Error，编译错误               |
| 沙箱 | Sandbox，隔离环境，用于安全运行不可信代码 |

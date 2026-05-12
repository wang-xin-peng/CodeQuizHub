# CodeQuizHub 系统设计文档

## 1. 技术栈确认

| 层次       | 技术选型                         |
| ---------- | -------------------------------- |
| 前端框架   | React 18 + TypeScript            |
| UI 组件库  | Ant Design 5                     |
| 代码编辑器 | Monaco Editor                    |
| 后端框架   | FastAPI (Python 3.11+)           |
| ORM        | SQLAlchemy 2.0 + Alembic (迁移)  |
| 数据库     | PostgreSQL 16                    |
| 缓存/队列  | Redis 7                         |
| 判题沙箱   | Docker 容器隔离                  |
| 认证       | JWT (PyJWT) + bcrypt             |
| API 文档   | FastAPI 内置 OpenAPI (Swagger)   |
| 部署       | Docker Compose                   |

---

## 2. 项目目录结构

### 2.1 整体结构

```
CodeQuizHub/
├── frontend/                # React 前端
├── backend/                 # FastAPI 后端
├── judge/                   # 判题服务
├── docker/                  # Docker 相关配置
├── docs/                    # 文档
├── docker-compose.yml       # 容器编排
└── README.md
```

### 2.2 后端目录结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理（环境变量）
│   ├── database.py          # 数据库连接与会话
│   ├── dependencies.py      # 公共依赖注入
│   ├── models/              # SQLAlchemy 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── problem.py
│   │   ├── assignment.py
│   │   ├── submission.py
│   │   └── code_draft.py
│   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── problem.py
│   │   ├── assignment.py
│   │   └── submission.py
│   ├── routers/             # API 路由
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── courses.py
│   │   ├── problems.py
│   │   ├── assignments.py
│   │   ├── submissions.py
│   │   └── grades.py
│   ├── services/            # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── course_service.py
│   │   ├── problem_service.py
│   │   ├── assignment_service.py
│   │   ├── submission_service.py
│   │   ├── judge_service.py
│   │   └── grade_service.py
│   ├── core/                # 核心模块
│   │   ├── security.py      # JWT、密码哈希
│   │   ├── errors.py        # 自定义异常类
│   │   └── error_codes.py   # 错误码枚举
│   └── utils/               # 工具函数
│       ├── code_template.py # 代码模板生成
│       └── export.py        # 成绩导出
├── alembic/                 # 数据库迁移
│   └── versions/
├── alembic.ini
├── requirements.txt
├── pyproject.toml
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_courses.py
    ├── test_problems.py
    ├── test_submissions.py
    └── test_grades.py
```

### 2.3 前端目录结构

```
frontend/
├── public/
├── src/
│   ├── main.tsx              # 入口文件
│   ├── App.tsx               # 根组件
│   ├── api/                  # API 请求封装
│   │   ├── client.ts         # Axios 实例
│   │   ├── auth.ts
│   │   ├── courses.ts
│   │   ├── problems.ts
│   │   ├── assignments.ts
│   │   ├── submissions.ts
│   │   └── grades.ts
│   ├── components/           # 通用组件
│   │   ├── Layout/
│   │   ├── CodeEditor/       # Monaco Editor 封装
│   │   ├── MarkdownRenderer/
│   │   └── ErrorBoundary/
│   ├── pages/                # 页面组件
│   │   ├── Auth/
│   │   │   ├── Login.tsx
│   │   │   └── Register.tsx
│   │   ├── Dashboard/
│   │   ├── Course/
│   │   │   ├── CourseList.tsx
│   │   │   ├── CourseDetail.tsx
│   │   │   └── CourseCreate.tsx
│   │   ├── Problem/
│   │   │   ├── ProblemList.tsx
│   │   │   ├── ProblemCreate.tsx
│   │   │   └── ProblemSolve.tsx  # LeetCode 风格做题页
│   │   ├── Assignment/
│   │   │   ├── AssignmentList.tsx
│   │   │   └── AssignmentDetail.tsx
│   │   └── Grade/
│   │       └── GradeOverview.tsx
│   ├── hooks/                # 自定义 Hooks
│   ├── store/                # 状态管理 (Zustand)
│   ├── types/                # TypeScript 类型定义
│   ├── utils/                # 工具函数
│   └── routes/               # 路由配置
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### 2.4 判题服务目录结构

```
judge/
├── judge_worker.py          # 判题消费者（监听 Redis 队列）
├── executor.py              # 代码执行引擎
├── assembler.py             # 代码组装（Prelude + Solution + Driver）
├── comparator.py            # 结果比对器
├── languages/               # 各语言配置
│   ├── __init__.py
│   ├── c.py
│   ├── cpp.py
│   ├── java.py
│   └── python.py
├── sandbox/                 # 沙箱配置
│   ├── Dockerfile.c
│   ├── Dockerfile.cpp
│   ├── Dockerfile.java
│   └── Dockerfile.python
├── prelude/                 # 预置代码（各语言的通用数据结构）
│   ├── c/
│   │   └── prelude.h
│   ├── cpp/
│   │   └── prelude.hpp
│   ├── java/
│   │   └── Prelude.java
│   └── python/
│       └── prelude.py
├── requirements.txt
└── tests/
```

---

## 3. 数据库设计

### 3.1 ER 关系图

```
User(1) ──────< CourseStudent >────── (N)Course
  │                                      │
  │(1:N)                                 │(1:N)
  │                                      │
  ▼                                      ▼
Problem(1) ──< AssignmentProblem >── (N)Assignment
  │
  ├──(1:N)── ProblemFunctionSignature
  ├──(1:N)── TestCase
  └──(1:N)── Submission(N) ──< SubmissionResult >── TestCase
                │
                └──(1:N)── CodeDraft
```

### 3.2 表结构定义

#### users 表

```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'student',  -- admin / teacher / student
    nickname      VARCHAR(100),
    avatar_url    VARCHAR(500),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_role CHECK (role IN ('admin', 'teacher', 'student'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role  ON users(role);
```

#### courses 表

```sql
CREATE TABLE courses (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(200)  NOT NULL,
    description TEXT,
    languages   VARCHAR(20)[] NOT NULL,  -- {'c', 'cpp', 'java', 'python'}
    invite_code VARCHAR(8)    NOT NULL UNIQUE,
    status      VARCHAR(20)   NOT NULL DEFAULT 'active',  -- active / archived
    teacher_id  UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_status CHECK (status IN ('active', 'archived'))
);

CREATE INDEX idx_courses_teacher  ON courses(teacher_id);
CREATE INDEX idx_courses_invite   ON courses(invite_code);
```

#### course_students 表

```sql
CREATE TABLE course_students (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id  UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
    joined_at  TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_course_student UNIQUE (course_id, student_id)
);

CREATE INDEX idx_cs_course  ON course_students(course_id);
CREATE INDEX idx_cs_student ON course_students(student_id);
```

#### problems 表

```sql
CREATE TABLE problems (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title        VARCHAR(300) NOT NULL,
    description  TEXT         NOT NULL,  -- Markdown 格式
    difficulty   VARCHAR(20)  NOT NULL DEFAULT 'medium',
    time_limit   INTEGER      NOT NULL DEFAULT 1000,   -- 毫秒
    memory_limit INTEGER      NOT NULL DEFAULT 256,     -- MB
    tags         VARCHAR(50)[] DEFAULT '{}',
    compare_mode VARCHAR(30)  NOT NULL DEFAULT 'exact', -- exact / unordered / float / custom
    teacher_id   UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_difficulty CHECK (difficulty IN ('easy', 'medium', 'hard')),
    CONSTRAINT chk_compare   CHECK (compare_mode IN ('exact', 'unordered', 'float', 'custom'))
);

CREATE INDEX idx_problems_teacher    ON problems(teacher_id);
CREATE INDEX idx_problems_difficulty ON problems(difficulty);
CREATE INDEX idx_problems_tags       ON problems USING GIN(tags);
```

#### problem_function_signatures 表

```sql
CREATE TABLE problem_function_signatures (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id      UUID        NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    language        VARCHAR(20) NOT NULL,  -- c / cpp / java / python
    function_name   VARCHAR(100) NOT NULL,
    parameters_json JSONB       NOT NULL,  -- [{"name":"nums","type":"int[]","description":"..."}]
    return_type     VARCHAR(100) NOT NULL,
    code_template   TEXT        NOT NULL,  -- 学生看到的初始代码
    prelude_code    TEXT,                  -- 预置代码（数据结构定义等）
    driver_template TEXT,                  -- 驱动代码模板
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_problem_lang UNIQUE (problem_id, language)
);

CREATE INDEX idx_pfs_problem ON problem_function_signatures(problem_id);
```

#### test_cases 表

```sql
CREATE TABLE test_cases (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id           UUID    NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    input_params_json    JSONB   NOT NULL,  -- {"nums":[2,7,11,15],"target":9}
    expected_output_json JSONB   NOT NULL,  -- [0,1]
    is_public            BOOLEAN NOT NULL DEFAULT FALSE,
    "order"              INTEGER NOT NULL DEFAULT 0,
    description          VARCHAR(500),
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_tc_order UNIQUE (problem_id, "order")
);

CREATE INDEX idx_tc_problem ON test_cases(problem_id);
```

#### assignments 表

```sql
CREATE TABLE assignments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id   UUID        NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title       VARCHAR(300) NOT NULL,
    description TEXT,
    start_time  TIMESTAMP   NOT NULL,
    end_time    TIMESTAMP   NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'draft',  -- draft / published / closed
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_time   CHECK (end_time > start_time),
    CONSTRAINT chk_astatus CHECK (status IN ('draft', 'published', 'closed'))
);

CREATE INDEX idx_assign_course ON assignments(course_id);
```

#### assignment_problems 表

```sql
CREATE TABLE assignment_problems (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID    NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    problem_id    UUID    NOT NULL REFERENCES problems(id)    ON DELETE CASCADE,
    score_weight  INTEGER NOT NULL DEFAULT 100,
    "order"       INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT uq_ap UNIQUE (assignment_id, problem_id)
);

CREATE INDEX idx_ap_assignment ON assignment_problems(assignment_id);
```

#### submissions 表

```sql
CREATE TABLE submissions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id    UUID        NOT NULL REFERENCES users(id)        ON DELETE CASCADE,
    assignment_id UUID        NOT NULL REFERENCES assignments(id)  ON DELETE CASCADE,
    problem_id    UUID        NOT NULL REFERENCES problems(id)     ON DELETE CASCADE,
    language      VARCHAR(20) NOT NULL,
    code          TEXT        NOT NULL,
    status        VARCHAR(30) NOT NULL DEFAULT 'pending',
    -- pending / judging / accepted / wrong_answer / tle / mle / re / ce
    score         INTEGER     DEFAULT 0,
    time_used     INTEGER,    -- 毫秒
    memory_used   INTEGER,    -- KB
    error_message TEXT,
    submitted_at  TIMESTAMP   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_sub_status CHECK (status IN (
        'pending', 'judging', 'accepted', 'wrong_answer',
        'time_limit_exceeded', 'memory_limit_exceeded',
        'runtime_error', 'compilation_error'
    ))
);

CREATE INDEX idx_sub_student    ON submissions(student_id);
CREATE INDEX idx_sub_assignment ON submissions(assignment_id);
CREATE INDEX idx_sub_problem    ON submissions(problem_id);
CREATE INDEX idx_sub_status     ON submissions(status);
```

#### submission_results 表

```sql
CREATE TABLE submission_results (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID        NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    test_case_id  UUID        NOT NULL REFERENCES test_cases(id)  ON DELETE CASCADE,
    status        VARCHAR(30) NOT NULL,
    actual_output TEXT,
    time_used     INTEGER,    -- 毫秒
    memory_used   INTEGER,    -- KB

    CONSTRAINT uq_sr UNIQUE (submission_id, test_case_id)
);

CREATE INDEX idx_sr_submission ON submission_results(submission_id);
```

#### code_drafts 表

```sql
CREATE TABLE code_drafts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id    UUID        NOT NULL REFERENCES users(id)       ON DELETE CASCADE,
    problem_id    UUID        NOT NULL REFERENCES problems(id)    ON DELETE CASCADE,
    assignment_id UUID        NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    language      VARCHAR(20) NOT NULL,
    code          TEXT        NOT NULL,
    updated_at    TIMESTAMP   NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_draft UNIQUE (student_id, problem_id, assignment_id, language)
);

CREATE INDEX idx_draft_student ON code_drafts(student_id);
```

---

## 4. API 详细设计

### 4.1 统一响应格式

#### 成功响应

```json
{
  "code": 0,
  "data": { ... },
  "message": "success"
}
```

#### 分页响应

```json
{
  "code": 0,
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "page_size": 20
  },
  "message": "success"
}
```

#### 错误响应

```json
{
  "code": "AUTH_INVALID_CREDENTIALS",
  "message": "用户名或密码错误",
  "detail": null
}
```

### 4.2 认证接口

#### POST /api/auth/register

注册新用户。

**请求体：**

```json
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "SecurePass123!",
  "role": "student"
}
```

**验证规则：**
- username: 3-50 字符，字母数字下划线
- email: 有效邮箱格式
- password: 至少 8 位，包含大小写字母和数字
- role: 只能是 "teacher" 或 "student"

**成功响应 (201)：**

```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "role": "student"
  }
}
```

**错误码：**
- `VALIDATION_INVALID_FORMAT` — 输入格式不合法
- `USER_ALREADY_EXISTS` — 用户名或邮箱已存在

#### POST /api/auth/login

用户登录，返回 JWT Token。

**请求体：**

```json
{
  "email": "zhangsan@example.com",
  "password": "SecurePass123!"
}
```

**成功响应 (200)：**

```json
{
  "code": 0,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": "uuid",
      "username": "zhangsan",
      "role": "student"
    }
  }
}
```

**错误码：**
- `AUTH_INVALID_CREDENTIALS` — 邮箱或密码错误
- `AUTH_ACCOUNT_DISABLED` — 账号已被禁用

#### 速率限制

登录接口速率限制：同一 IP 15 分钟内最多 10 次请求。

### 4.3 课程接口

#### POST /api/courses

创建课程（仅教师）。

**请求头：** `Authorization: Bearer <token>`

**请求体：**

```json
{
  "name": "Python 程序设计",
  "description": "2026 春季学期 Python 课程",
  "languages": ["python"]
}
```

**成功响应 (201)：**

```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "name": "Python 程序设计",
    "languages": ["python"],
    "invite_code": "ABC12345",
    "status": "active",
    "teacher_id": "uuid"
  }
}
```

#### POST /api/courses/join

学生通过邀请码加入课程。

**请求体：**

```json
{
  "invite_code": "ABC12345"
}
```

**错误码：**
- `COURSE_NOT_FOUND` — 邀请码无效
- `COURSE_ALREADY_JOINED` — 已加入该课程
- `COURSE_ARCHIVED` — 课程已归档

### 4.4 题目接口

#### POST /api/problems

创建题目（仅教师）。

**请求体：**

```json
{
  "title": "两数之和",
  "description": "给定一个整数数组 `nums` 和一个整数目标值 `target`...",
  "difficulty": "easy",
  "time_limit": 1000,
  "memory_limit": 256,
  "tags": ["array", "hash-table"],
  "compare_mode": "unordered",
  "signatures": [
    {
      "language": "python",
      "function_name": "twoSum",
      "parameters": [
        { "name": "nums", "type": "List[int]", "description": "整数数组" },
        { "name": "target", "type": "int", "description": "目标值" }
      ],
      "return_type": "List[int]",
      "code_template": "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        # 在此编写代码\n        pass",
      "prelude_code": ""
    },
    {
      "language": "java",
      "function_name": "twoSum",
      "parameters": [
        { "name": "nums", "type": "int[]", "description": "整数数组" },
        { "name": "target", "type": "int", "description": "目标值" }
      ],
      "return_type": "int[]",
      "code_template": "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        // 在此编写代码\n    }\n}"
    }
  ],
  "test_cases": [
    {
      "input_params": { "nums": [2, 7, 11, 15], "target": 9 },
      "expected_output": [0, 1],
      "is_public": true,
      "description": "示例 1"
    },
    {
      "input_params": { "nums": [3, 2, 4], "target": 6 },
      "expected_output": [1, 2],
      "is_public": false
    }
  ]
}
```

#### GET /api/problems/:id

获取题目详情（根据角色返回不同数据）。

- 教师：返回全部信息（含隐藏用例、参考实现）
- 学生：只返回描述、公开用例、函数签名和代码模板

#### POST /api/problems/:id/run

运行代码（公开用例调试），不计入正式提交。

**请求体：**

```json
{
  "language": "python",
  "code": "class Solution:\n    def twoSum(self, nums, target):\n        ...",
  "assignment_id": "uuid"
}
```

**响应 (200)：**

```json
{
  "code": 0,
  "data": {
    "results": [
      {
        "test_case_order": 1,
        "status": "accepted",
        "input": { "nums": [2, 7, 11, 15], "target": 9 },
        "expected": [0, 1],
        "actual": [0, 1],
        "time_used": 12,
        "memory_used": 8400
      }
    ],
    "compile_error": null
  }
}
```

### 4.5 提交接口

#### POST /api/submissions

正式提交代码评测。

**请求体：**

```json
{
  "assignment_id": "uuid",
  "problem_id": "uuid",
  "language": "python",
  "code": "class Solution:\n    def twoSum(self, nums, target):\n        ..."
}
```

**响应 (202)：** 异步处理，返回提交 ID

```json
{
  "code": 0,
  "data": {
    "submission_id": "uuid",
    "status": "pending"
  }
}
```

#### GET /api/submissions/:id

查询提交结果（轮询或 WebSocket 推送）。

**响应 (200)：**

```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "status": "accepted",
    "score": 100,
    "time_used": 24,
    "memory_used": 9200,
    "submitted_at": "2026-05-12T10:30:00Z",
    "results": [
      {
        "test_case_order": 1,
        "status": "accepted",
        "is_public": true,
        "input": { "nums": [2, 7, 11, 15], "target": 9 },
        "expected": [0, 1],
        "actual": [0, 1],
        "time_used": 12
      },
      {
        "test_case_order": 2,
        "status": "accepted",
        "is_public": false,
        "input": null,
        "expected": null,
        "actual": null,
        "time_used": 12
      }
    ]
  }
}
```

> 注意：隐藏测试用例只返回 status，不返回 input/expected/actual。

### 4.6 成绩接口

#### GET /api/courses/:id/grades/export

导出成绩为 Excel 文件。

**查询参数：**
- `format`: `xlsx` | `csv`（默认 xlsx）

**响应：** 文件流下载

---

## 5. 认证与授权设计

### 5.1 JWT Token 设计

```python
# Token Payload
{
    "sub": "user-uuid",           # 用户 ID
    "role": "teacher",            # 角色
    "exp": 1716000000,            # 过期时间（24 小时）
    "iat": 1715913600             # 签发时间
}
```

- 算法：HS256
- 密钥：从环境变量 `JWT_SECRET` 读取
- 有效期：24 小时
- 刷新机制：Token 过期前 1 小时可用旧 Token 换取新 Token

### 5.2 权限控制

使用依赖注入实现角色校验：

```python
# dependencies.py
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """解析 JWT，返回当前用户"""
    ...

async def require_teacher(user: User = Depends(get_current_user)) -> User:
    """要求教师角色"""
    if user.role not in ('teacher', 'admin'):
        raise ForbiddenError("需要教师权限")
    return user

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """要求管理员角色"""
    if user.role != 'admin':
        raise ForbiddenError("需要管理员权限")
    return user
```

### 5.3 接口权限矩阵

| 接口                         | 学生 | 教师 | 管理员 |
| ---------------------------- | ---- | ---- | ------ |
| POST /api/auth/register      | -    | -    | -      |
| POST /api/auth/login         | -    | -    | -      |
| GET  /api/users/me           | R    | R    | R      |
| POST /api/courses            | -    | W    | W      |
| POST /api/courses/join       | W    | -    | -      |
| GET  /api/courses/:id        | R    | R    | R      |
| POST /api/problems           | -    | W    | W      |
| GET  /api/problems/:id       | R*   | R    | R      |
| POST /api/submissions        | W    | -    | -      |
| GET  /api/courses/:id/grades | R*   | R    | R      |
| GET  .../grades/export       | -    | W    | W      |

> R* 表示返回的数据经过过滤（如学生只能看到自己的成绩、只能看公开用例）

---

## 6. 判题服务设计

### 6.1 判题流程

```
                    ┌──────────┐
                    │ 学生提交  │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ 后端 API  │  1. 验证提交合法性
                    │          │  2. 保存 Submission (status=pending)
                    │          │  3. 发送消息到 Redis 队列
                    └────┬─────┘
                         │ Redis List: judge_queue
                    ┌────▼─────┐
                    │ 判题 Worker│  4. 消费队列消息
                    │          │  5. 组装完整代码
                    │          │  6. 创建 Docker 容器
                    └────┬─────┘
                         │
                    ┌────▼─────────┐
                    │ Docker 沙箱   │  7. 编译运行
                    │ (资源限制)     │  8. 逐用例执行
                    └────┬─────────┘
                         │
                    ┌────▼─────┐
                    │ 判题 Worker│  9. 收集结果
                    │          │ 10. 比对输出
                    │          │ 11. 计算得分
                    │          │ 12. 更新数据库 (status/score)
                    └──────────┘
```

### 6.2 Redis 消息队列设计

使用 Redis List 作为任务队列：

```python
# 生产者（后端 API）
task = {
    "submission_id": "uuid",
    "problem_id": "uuid",
    "language": "python",
    "code": "...",
    "time_limit": 1000,
    "memory_limit": 256
}
redis.lpush("judge_queue", json.dumps(task))

# 消费者（判题 Worker）
while True:
    _, task_json = redis.brpop("judge_queue")
    task = json.loads(task_json)
    process_submission(task)
```

### 6.3 代码组装示例

以 Python 为例：

```python
# assembler.py
def assemble_python(prelude: str, solution: str, driver: str) -> str:
    return f"""
# === Prelude ===
{prelude}

# === Solution ===
{solution}

# === Driver ===
{driver}
"""
```

组装后的完整代码（Python）：

```python
# === Prelude ===
from typing import List, Optional

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

# === Solution (学生代码) ===
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        lookup = {}
        for i, num in enumerate(nums):
            if target - num in lookup:
                return [lookup[target - num], i]
            lookup[num] = i

# === Driver (平台生成) ===
import json, sys

def main():
    input_data = json.loads(sys.argv[1])
    sol = Solution()
    result = sol.twoSum(input_data["nums"], input_data["target"])
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

### 6.4 Docker 沙箱配置

每种语言一个基础镜像：

```dockerfile
# sandbox/Dockerfile.python
FROM python:3.11-slim
RUN useradd -m -s /bin/bash judge
USER judge
WORKDIR /home/judge
```

运行容器时的资源限制：

```python
container = docker_client.containers.run(
    image="codequizhub-python",
    command=f"python solution.py '{input_json}'",
    mem_limit="256m",         # 内存限制
    nano_cpus=1_000_000_000,  # 1 CPU
    network_disabled=True,    # 禁止网络
    read_only=True,           # 只读文件系统
    timeout=10,               # 超时秒数
    user="judge",             # 非 root 用户
    detach=True
)
```

### 6.5 结果比对器

```python
# comparator.py
def compare(actual: str, expected: str, mode: str, precision: float = 1e-5) -> bool:
    if mode == "exact":
        return json.loads(actual) == json.loads(expected)

    elif mode == "unordered":
        a = json.loads(actual)
        e = json.loads(expected)
        return sorted(a) == sorted(e) if isinstance(a, list) else a == e

    elif mode == "float":
        a = float(actual)
        e = float(expected)
        return abs(a - e) < precision

    elif mode == "custom":
        # 调用教师提供的 checker
        ...
```

---

## 7. 错误处理设计

### 7.1 错误码枚举

```python
# core/error_codes.py
from enum import Enum

class ErrorCode(str, Enum):
    # 认证
    AUTH_INVALID_CREDENTIALS   = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED         = "AUTH_TOKEN_EXPIRED"
    AUTH_ACCOUNT_DISABLED      = "AUTH_ACCOUNT_DISABLED"
    AUTH_FORBIDDEN             = "AUTH_FORBIDDEN"

    # 验证
    VALIDATION_INVALID_FORMAT  = "VALIDATION_INVALID_FORMAT"
    VALIDATION_REQUIRED_FIELD  = "VALIDATION_REQUIRED_FIELD"

    # 用户
    USER_ALREADY_EXISTS        = "USER_ALREADY_EXISTS"
    USER_NOT_FOUND             = "USER_NOT_FOUND"

    # 课程
    COURSE_NOT_FOUND           = "COURSE_NOT_FOUND"
    COURSE_ALREADY_JOINED      = "COURSE_ALREADY_JOINED"
    COURSE_ARCHIVED            = "COURSE_ARCHIVED"

    # 题目
    PROBLEM_NOT_FOUND          = "PROBLEM_NOT_FOUND"
    PROBLEM_LANG_NOT_SUPPORTED = "PROBLEM_LANG_NOT_SUPPORTED"

    # 作业
    ASSIGNMENT_NOT_FOUND       = "ASSIGNMENT_NOT_FOUND"
    ASSIGNMENT_NOT_STARTED     = "ASSIGNMENT_NOT_STARTED"
    ASSIGNMENT_EXPIRED         = "ASSIGNMENT_EXPIRED"

    # 提交
    SUBMISSION_NOT_FOUND       = "SUBMISSION_NOT_FOUND"
    SUBMISSION_LIMIT_EXCEEDED  = "SUBMISSION_LIMIT_EXCEEDED"

    # 判题
    JUDGE_COMPILATION_ERROR    = "JUDGE_COMPILATION_ERROR"
    JUDGE_RUNTIME_ERROR        = "JUDGE_RUNTIME_ERROR"
    JUDGE_TIMEOUT              = "JUDGE_TIMEOUT"
    JUDGE_SERVICE_UNAVAILABLE  = "JUDGE_SERVICE_UNAVAILABLE"
```

### 7.2 自定义异常类

```python
# core/errors.py
class AppError(Exception):
    """应用基础异常"""
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class BusinessError(AppError):
    """业务逻辑错误（用户可恢复）"""
    pass

class AuthenticationError(AppError):
    """认证错误"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(ErrorCode.AUTH_INVALID_CREDENTIALS, message, 401)

class ForbiddenError(AppError):
    """权限不足"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(ErrorCode.AUTH_FORBIDDEN, message, 403)

class NotFoundError(AppError):
    """资源未找到"""
    def __init__(self, resource: str, id: str):
        super().__init__(
            ErrorCode(f"{resource.upper()}_NOT_FOUND"),
            f"{resource} 不存在",
            404
        )

class SystemError(AppError):
    """系统内部错误（需运维介入）"""
    def __init__(self, message: str = "服务器内部错误"):
        super().__init__(ErrorCode.JUDGE_SERVICE_UNAVAILABLE, message, 500)
```

### 7.3 全局异常处理器

```python
# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code.value,
            "message": exc.message,
            "detail": None
        }
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None
        }
    )
```

---

## 8. 安全设计

### 8.1 密码安全

```python
# core/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### 8.2 输入验证

所有请求通过 Pydantic 模型验证：

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr, Field
import re

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["teacher", "student"]

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含小写字母")
        if not re.search(r"[0-9]", v):
            raise ValueError("密码必须包含数字")
        return v
```

### 8.3 SQL 注入防护

使用 SQLAlchemy ORM 参数化查询，禁止拼接 SQL：

```python
# 正确 - 参数化查询
stmt = select(User).where(User.email == email)
user = await session.execute(stmt)

# 禁止 - 字符串拼接
# query = f"SELECT * FROM users WHERE email = '{email}'"
```

### 8.4 API 速率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("10/15minutes")
async def login(request: Request, body: LoginRequest):
    ...
```

### 8.5 CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 从环境变量读取
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 8.6 判题沙箱安全

| 措施             | 说明                                        |
| ---------------- | ------------------------------------------- |
| 网络隔离         | `network_disabled=True`                     |
| 资源限制         | CPU、内存、磁盘空间限制                     |
| 非 root 用户     | 容器内以普通用户运行                        |
| 只读文件系统     | `read_only=True`，仅挂载临时写入目录        |
| 超时强制终止     | 超过时间限制后强制 kill 容器                |
| 禁止系统调用     | 通过 seccomp profile 限制危险系统调用       |

---

## 9. 前端核心页面设计

### 9.1 页面路由

```typescript
const routes = [
  // 公开页面
  { path: "/login",    component: Login },
  { path: "/register", component: Register },

  // 学生/教师通用
  { path: "/dashboard",          component: Dashboard },
  { path: "/courses",            component: CourseList },
  { path: "/courses/:id",        component: CourseDetail },
  { path: "/assignments/:id",    component: AssignmentDetail },
  { path: "/solve/:assignmentId/:problemId", component: ProblemSolve },

  // 教师专属
  { path: "/courses/create",     component: CourseCreate },
  { path: "/problems",           component: ProblemList },
  { path: "/problems/create",    component: ProblemCreate },
  { path: "/problems/:id/edit",  component: ProblemEdit },
  { path: "/assignments/create", component: AssignmentCreate },
  { path: "/grades/:courseId",   component: GradeOverview },

  // 管理员
  { path: "/admin/users",        component: AdminUsers },
];
```

### 9.2 做题页面布局（ProblemSolve）

LeetCode 风格，左右分栏：

```
┌─────────────────────────────────────────────────────────────┐
│  [作业名称]   [< 上一题] [题目 1/5] [下一题 >]              │
├────────────────────────┬────────────────────────────────────┤
│                        │  [Python ▼]  [重置代码]            │
│   题目描述              │  ┌──────────────────────────────┐ │
│   (Markdown 渲染)      │  │ class Solution:              │ │
│                        │  │     def twoSum(self, ...):   │ │
│   示例 1:              │  │         # 在此编写代码        │ │
│   输入: nums=[2,7...]  │  │         pass                 │ │
│   输出: [0, 1]         │  │                              │ │
│                        │  │                              │ │
│   约束条件:            │  │      Monaco Editor           │ │
│   ...                  │  │                              │ │
│                        │  └──────────────────────────────┘ │
│                        │                                    │
│                        │  ┌────────────────────────────────┐│
│                        │  │ 测试结果 / 提交记录            ││
│                        │  │ 用例1: ✅ AC  12ms  8.4MB     ││
│                        │  │ 用例2: ✅ AC  15ms  8.5MB     ││
│                        │  └────────────────────────────────┘│
├────────────────────────┴────────────────────────────────────┤
│  [运行测试]                              [提交]             │
└─────────────────────────────────────────────────────────────┘
```

### 9.3 前端状态管理

使用 Zustand：

```typescript
// store/authStore.ts
interface AuthState {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

// store/editorStore.ts
interface EditorState {
  code: string;
  language: string;
  isRunning: boolean;
  isSubmitting: boolean;
  testResults: TestResult[];
  setCode: (code: string) => void;
  setLanguage: (lang: string) => void;
  runTests: () => Promise<void>;
  submit: () => Promise<void>;
}
```

### 9.4 代码自动保存

使用防抖策略自动保存草稿：

```typescript
// 每 3 秒自动保存一次（防抖）
const debouncedSave = useDebouncedCallback(
  async (code: string) => {
    await api.saveDraft({
      problem_id: problemId,
      assignment_id: assignmentId,
      language,
      code
    });
  },
  3000
);

// 编辑器内容变化时触发
const handleCodeChange = (value: string) => {
  setCode(value);
  debouncedSave(value);
};
```

---

## 10. 部署架构

### 10.1 Docker Compose 编排

```yaml
# docker-compose.yml
version: "3.8"

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/codequizhub
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - db
      - redis

  judge-worker:
    build: ./judge
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # 需要 Docker-in-Docker
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/codequizhub
    depends_on:
      - redis
      - db

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: codequizhub
      POSTGRES_USER: user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

### 10.2 环境变量配置

```env
# .env (不提交到 Git)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/codequizhub
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-256-bit-secret-key-here
CORS_ORIGINS=http://localhost:3000
DEBUG=true
DB_PASSWORD=your-db-password
```

---

## 11. 关键技术方案

### 11.1 邀请码生成

```python
import secrets
import string

def generate_invite_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
```

### 11.2 成绩导出

使用 openpyxl 生成 Excel：

```python
from openpyxl import Workbook
from fastapi.responses import StreamingResponse

async def export_grades(course_id: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "成绩表"
    ws.append(["学号", "姓名", "作业1", "作业2", ..., "总分"])
    # 填充数据...

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=grades.xlsx"}
    )
```

### 11.3 WebSocket 实时推送评测结果

```python
# routers/submissions.py
from fastapi import WebSocket

@app.websocket("/ws/submissions/{submission_id}")
async def submission_ws(websocket: WebSocket, submission_id: str):
    await websocket.accept()
    while True:
        status = await redis.get(f"submission:{submission_id}:status")
        await websocket.send_json({"status": status})
        if status in ("accepted", "wrong_answer", "compilation_error", ...):
            break
        await asyncio.sleep(1)
    await websocket.close()
```

---

## 12. 项目开发规范

### 12.1 Git 分支策略

```
main           ← 生产分支，只接受 PR 合并
├── develop    ← 开发主分支
│   ├── feature/user-auth      ← 功能分支
│   ├── feature/course-mgmt
│   ├── feature/problem-mgmt
│   └── feature/judge-service
└── hotfix/xxx ← 紧急修复
```

### 12.2 代码规范

| 工具       | 用途           |
| ---------- | -------------- |
| Ruff       | Python Lint    |
| Black      | Python 格式化  |
| mypy       | Python 类型检查|
| ESLint     | TypeScript Lint|
| Prettier   | 前端格式化     |

### 12.3 测试策略

| 层次       | 工具                | 覆盖目标     |
| ---------- | ------------------- | ------------ |
| 后端单元测试 | pytest + httpx    | 核心业务逻辑 |
| 后端集成测试 | pytest + testcontainers | API + 数据库 |
| 前端单元测试 | Vitest + React Testing Library | 组件逻辑 |
| E2E 测试   | Playwright          | 关键用户流程 |

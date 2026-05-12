# CodeQuizHub 任务清单

> 状态标记：⬜ 未开始 | 🔵 进行中 | ✅ 已完成

---

## 阶段一：项目初始化与基础设施

### 1.1 项目脚手架搭建
- ⬜ 初始化后端项目（FastAPI + 依赖配置）
- ⬜ 初始化前端项目（Vite + React + TypeScript）
- ⬜ 初始化判题服务项目结构
- ⬜ 配置 Docker Compose（PostgreSQL + Redis）
- ⬜ 配置代码规范工具（Ruff / Black / ESLint / Prettier）

### 1.2 数据库与ORM
- ⬜ 配置 SQLAlchemy 2.0 + 异步引擎
- ⬜ 配置 Alembic 数据库迁移
- ⬜ 创建 User 模型与迁移
- ⬜ 创建 Course / CourseStudent 模型与迁移
- ⬜ 创建 Problem / ProblemFunctionSignature / TestCase 模型与迁移
- ⬜ 创建 Assignment / AssignmentProblem 模型与迁移
- ⬜ 创建 Submission / SubmissionResult 模型与迁移
- ⬜ 创建 CodeDraft 模型与迁移

### 1.3 后端基础设施
- ⬜ 统一响应格式封装（成功/分页/错误）
- ⬜ 自定义异常类（AppError / BusinessError / AuthError / NotFoundError）
- ⬜ 错误码枚举（ErrorCode）
- ⬜ 全局异常处理器
- ⬜ JWT 认证工具（签发/验证）
- ⬜ 密码哈希工具（bcrypt）
- ⬜ 依赖注入（get_current_user / require_teacher / require_admin）
- ⬜ CORS 中间件配置
- ⬜ API 速率限制中间件

### 1.4 前端基础设施
- ⬜ 配置 Axios 请求封装（拦截器、Token 注入、错误处理）
- ⬜ 配置路由（React Router）
- ⬜ 配置状态管理（Zustand）
- ⬜ 配置 Ant Design 主题
- ⬜ 实现 Layout 组件（导航栏、侧边栏）
- ⬜ 实现 ErrorBoundary 组件
- ⬜ 实现路由守卫（登录态/角色校验）

---

## 阶段二：用户管理模块

### 2.1 后端 - 用户认证
- ⬜ POST /api/auth/register — 用户注册
- ⬜ POST /api/auth/login — 用户登录
- ⬜ 注册输入验证（用户名/邮箱/密码强度）
- ⬜ 登录速率限制
- ⬜ 单元测试：注册/登录

### 2.2 后端 - 用户信息
- ⬜ GET /api/users/me — 获取当前用户信息
- ⬜ PUT /api/users/me — 更新个人信息
- ⬜ PUT /api/users/me/password — 修改密码
- ⬜ 单元测试：用户信息

### 2.3 后端 - 管理员功能
- ⬜ GET /api/admin/users — 用户列表（分页/筛选）
- ⬜ PUT /api/admin/users/:id — 更新用户状态（禁用/启用）
- ⬜ PUT /api/admin/users/:id/role — 变更角色
- ⬜ 单元测试：管理员功能

### 2.4 前端 - 认证页面
- ⬜ 登录页面
- ⬜ 注册页面
- ⬜ 登录状态持久化（Token 存储）
- ⬜ 登出功能

### 2.5 前端 - 个人中心
- ⬜ 个人信息展示与编辑页面
- ⬜ 修改密码页面

### 2.6 前端 - 管理员页面
- ⬜ 用户管理列表页面
- ⬜ 用户状态/角色操作

---

## 阶段三：课程管理模块

### 3.1 后端 - 课程 CRUD
- ⬜ POST /api/courses — 创建课程（教师）
- ⬜ GET /api/courses — 获取课程列表（教师：自己创建的；学生：已加入的）
- ⬜ GET /api/courses/:id — 获取课程详情
- ⬜ PUT /api/courses/:id — 更新课程信息（教师）
- ⬜ DELETE /api/courses/:id — 删除/归档课程（教师）
- ⬜ 邀请码生成逻辑
- ⬜ 单元测试：课程 CRUD

### 3.2 后端 - 课程成员管理
- ⬜ POST /api/courses/join — 学生加入课程（邀请码）
- ⬜ DELETE /api/courses/:id/leave — 学生退出课程
- ⬜ GET /api/courses/:id/students — 获取课程学生列表
- ⬜ DELETE /api/courses/:id/students/:studentId — 教师移除学生
- ⬜ 单元测试：成员管理

### 3.3 前端 - 课程页面
- ⬜ 课程列表页面（教师/学生视图）
- ⬜ 创建课程页面（教师）
- ⬜ 课程详情页面
- ⬜ 加入课程弹窗（输入邀请码）
- ⬜ 课程学生列表组件
- ⬜ 编辑课程/归档课程

---

## 阶段四：题目管理模块

### 4.1 后端 - 题目 CRUD
- ⬜ POST /api/problems — 创建题目（含函数签名 + 测试用例）
- ⬜ GET /api/problems — 获取题目列表（支持筛选：语言/难度/标签）
- ⬜ GET /api/problems/:id — 获取题目详情（角色区分返回内容）
- ⬜ PUT /api/problems/:id — 更新题目
- ⬜ DELETE /api/problems/:id — 删除题目
- ⬜ 单元测试：题目 CRUD

### 4.2 后端 - 函数签名管理
- ⬜ POST /api/problems/:id/signatures — 添加/更新函数签名
- ⬜ GET /api/problems/:id/signatures/:lang — 获取指定语言的签名与模板
- ⬜ 代码模板自动生成逻辑
- ⬜ 单元测试：函数签名

### 4.3 后端 - 测试用例管理
- ⬜ POST /api/problems/:id/testcases — 添加测试用例
- ⬜ PUT /api/problems/:id/testcases/:tcId — 更新测试用例
- ⬜ DELETE /api/problems/:id/testcases/:tcId — 删除测试用例
- ⬜ 单元测试：测试用例

### 4.4 前端 - 题目管理页面（教师）
- ⬜ 题目列表页面（筛选/搜索）
- ⬜ 创建题目页面
  - ⬜ 基本信息表单（标题/描述/难度/标签）
  - ⬜ 函数签名编辑器（多语言 Tab 切换）
  - ⬜ 测试用例编辑器（公开/隐藏标记）
  - ⬜ Markdown 实时预览
- ⬜ 编辑题目页面
- ⬜ 题目详情预览

---

## 阶段五：作业管理模块

### 5.1 后端 - 作业 CRUD
- ⬜ POST /api/assignments — 创建/发布作业
- ⬜ GET /api/courses/:id/assignments — 获取课程下作业列表
- ⬜ GET /api/assignments/:id — 获取作业详情（含题目列表）
- ⬜ PUT /api/assignments/:id — 更新作业（编辑/发布/关闭）
- ⬜ 作业状态自动管理（到期自动关闭）
- ⬜ 单元测试：作业 CRUD

### 5.2 前端 - 作业页面
- ⬜ 创建作业页面（教师：选题组卷）
- ⬜ 作业列表页面（学生：区分状态；教师：查看提交情况）
- ⬜ 作业详情页面（题目列表 + 完成状态）

---

## 阶段六：在线编程与代码提交

### 6.1 后端 - 代码运行与提交
- ⬜ POST /api/problems/:id/run — 运行测试（公开用例）
- ⬜ POST /api/problems/:id/run-custom — 自定义输入运行
- ⬜ POST /api/submissions — 正式提交代码
- ⬜ GET /api/submissions/:id — 获取提交结果
- ⬜ GET /api/assignments/:id/submissions — 获取作业的所有提交
- ⬜ WebSocket /ws/submissions/:id — 实时推送评测结果
- ⬜ 代码草稿自动保存接口（PUT /api/drafts）
- ⬜ 单元测试：提交与评测

### 6.2 前端 - 做题页面（核心页面）
- ⬜ 左右分栏布局（题目描述 | 代码编辑器）
- ⬜ Monaco Editor 集成
  - ⬜ 语法高亮 + 自动补全
  - ⬜ 代码模板预填充
  - ⬜ 语言切换（自动加载对应模板）
- ⬜ 运行测试功能（调用 /run，展示用例结果对比）
- ⬜ 自定义测试输入
- ⬜ 提交功能（调用 /submissions，轮询/WebSocket 获取结果）
- ⬜ 测试结果展示面板（AC/WA/TLE/RE/CE 状态 + 详情）
- ⬜ 提交历史列表
- ⬜ 代码自动保存（防抖 3 秒）
- ⬜ 代码重置按钮
- ⬜ 题目切换（上一题/下一题）

---

## 阶段七：判题服务

### 7.1 判题核心
- ⬜ Redis 队列消费者（judge_worker.py）
- ⬜ 代码组装器（assembler.py：Prelude + Solution + Driver）
- ⬜ Docker 沙箱执行器（executor.py）
  - ⬜ 容器创建与资源限制（CPU/内存/网络/文件系统）
  - ⬜ 超时强制终止
  - ⬜ 编译错误捕获
  - ⬜ 运行时错误捕获
- ⬜ 结果比对器（comparator.py）
  - ⬜ 精确匹配
  - ⬜ 无序匹配
  - ⬜ 浮点精度匹配
- ⬜ 评分计算与数据库更新

### 7.2 多语言支持
- ⬜ Python 语言配置（编译命令/运行命令/Docker 镜像）
- ⬜ Java 语言配置
- ⬜ C 语言配置
- ⬜ C++ 语言配置

### 7.3 预置代码
- ⬜ Python prelude（ListNode / TreeNode 等）
- ⬜ Java prelude
- ⬜ C prelude
- ⬜ C++ prelude

### 7.4 判题服务 Docker 化
- ⬜ 各语言沙箱 Dockerfile
- ⬜ 判题 Worker Dockerfile
- ⬜ 集成到 docker-compose.yml

### 7.5 测试
- ⬜ 判题服务单元测试（代码组装/结果比对）
- ⬜ 集成测试（完整判题流程）

---

## 阶段八：成绩管理模块

### 8.1 后端 - 成绩查询与导出
- ⬜ GET /api/courses/:id/grades — 获取课程成绩汇总
- ⬜ GET /api/courses/:id/grades/export — 导出成绩（Excel/CSV）
- ⬜ 成绩计算逻辑（取最优提交 + 加权汇总）
- ⬜ 数据统计（平均分/最高分/最低分/通过率）
- ⬜ 单元测试：成绩模块

### 8.2 前端 - 成绩页面
- ⬜ 教师：课程成绩汇总表格（支持排序/筛选）
- ⬜ 教师：单个学生详细成绩查看
- ⬜ 教师：成绩导出按钮（下载 Excel）
- ⬜ 学生：个人成绩查看页面
- ⬜ 数据统计图表（通过率/得分分布）

---

## 阶段九：系统优化与部署

### 9.1 性能优化
- ⬜ 数据库查询优化（N+1 问题、索引检查）
- ⬜ Redis 缓存热点数据（课程信息/题目信息）
- ⬜ 前端代码分割（React.lazy）
- ⬜ 前端静态资源 CDN 配置

### 9.2 安全加固
- ⬜ 安全审计（依赖漏洞扫描）
- ⬜ 生产环境错误信息脱敏
- ⬜ 日志安全检查（确保不记录敏感信息）
- ⬜ CSP / X-Frame-Options 等安全头配置

### 9.3 部署
- ⬜ 前端 Nginx 配置（SPA 路由 + 静态文件）
- ⬜ 后端 Gunicorn/Uvicorn 生产配置
- ⬜ Docker Compose 生产配置
- ⬜ 环境变量管理（.env.production）
- ⬜ 数据库备份策略

### 9.4 文档
- ⬜ API 文档完善（FastAPI Swagger 自动生成）
- ⬜ 部署文档
- ⬜ 用户使用手册

---
trigger: model_decision
description: 进行功能开发和bug解决时
---
# CRUD 端点修改 — 完整数据流验证规范

## 背景

AI 在实现"编辑作业"功能时，因未追踪完整数据流而引入 Bug：前端将 `problem_ids`
传给 `updateAssignment`，但后端 `AssignmentUpdateRequest` schema 和 `PUT` 端点
均未定义该字段，导致题目关联未被更新，页面仍显示旧数据。

## 规范

### 1. 修改前通读全链路代码

在改动任何 CRUD 端点前，必须依次阅读以下文件中的**相关部分**：

| 层级 | 文件 | 确认事项 |
|------|------|----------|
| 前端组件 | 调用 API 的页面/组件 | 传入了哪些字段？ |
| 前端 API | `api/*.ts` 中的函数签名 | 参数类型是否包含所需字段？ |
| 后端 Schema | `schemas/*.py` 的 Request 类 | 该请求类定义了哪些字段？ |
| 后端端点 | `routers/*.py` 的对应方法 | 实际使用了 schema 中的哪些字段写入了数据库？ |
| 数据模型 | `models/*.py` | 数据库表结构是否支持？ |

### 2. 追踪完整数据流

以本次 Bug 为例，正确的追踪路径：

```
前端 <AssignmentCreate/> onFinish
  → assignmentsApi.updateAssignment(id, { problem_ids, ... })
    → client.put('/assignments/{id}', data)
      → 后端 PUT /assignments/{assignment_id}
        → AssignmentUpdateRequest（检查是否有 problem_ids 字段）
          → update_assignment() 方法体（检查是否写入了 AssignmentProblem 表）
```

**规则**：在数据流每一步都确认字段被正确传递和处理，直到数据库写入。

### 3. 创建和更新使用不同 Schema 时必须逐字段对照

常见模式：

```python
class AssignmentCreateRequest(BaseModel):
    problem_ids: list[str]           # ✅ 创建时有

class AssignmentUpdateRequest(BaseModel):
    # ❌ 更新时没有！这是 Bug 的根源
```

**规则**：当 `CreateRequest` 和 `UpdateRequest` 是不同类时，列出两者的字段清单做 diff，
确保更新请求不缺字段。

### 4. 不依赖"望文生义"

**反例**：

- "`updateAssignment` 名字叫 update，应该能更新所有字段吧"
- "后端应该会自动处理关联表更新"
- "前端传了后端就会收到"

**正例**：

- 读 `AssignmentUpdateRequest` 的字段定义
- 读 `update_assignment()` 方法体，逐行确认哪些字段被写入
- 确认 `AssignmentProblem` 关联表有没有被操作

### 5. 改完后验证持久化结果

通过表面反馈（如弹窗"保存成功"）不足以确认功能正确。必须验证数据是否**真正持久化**：

- **方法一**：调用 `GET /assignments/{id}` 检查响应中 `problems` 字段是否更新
- **方法二**：在详情页刷新后确认展示数据与提交数据一致
- **方法三**：直接查数据库确认 `assignment_problem` 表已更新

### 6. 涉及关联表更新时，检查后端是否处理了级联操作

当修改涉及多对多关联时（如 `Assignment` ↔ `Problem` 通过 `AssignmentProblem`），
需要确认后端端点是否包含了关联记录的删除和重建逻辑。

**检查清单**：

- [ ] 是否需要先删除旧的关联记录?
- [ ] 新记录是否包含所有必要字段（`assignment_id`, `problem_id`, `order` 等）?
- [ ] 数据一致性：flush/commit 时机是否正确？

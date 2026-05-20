# CodeQuizHub

一个在线编程作业测评平台，支持多语言判题、课程管理、成绩统计。

## 快速启动

```bash
# 启动全部服务
docker compose up -d

# 或按需启动（推荐开发环境）
docker compose up -d db redis backend frontend judge-worker

# 构建沙箱镜像（首次运行前必须执行）
docker compose --profile sandbox build
```

- **前端**: http://localhost:5173
- **后端 API**: http://localhost:8000/api/docs (Swagger)
- **数据库**: localhost:5432

## 系统架构

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  PostgreSQL  │
│  (Vite+React)│     │  (FastAPI)   │     │              │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │                          │
                    ┌──────▼───────┐           ┌──────▼───────┐
                    │    Redis     │◀──────────│ Judge Worker │
                    │  (队列+缓存)  │──────────▶│  (Docker沙箱) │
                    └──────────────┘           └──────────────┘
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_PASSWORD` | `codequizhub` | 数据库密码 |
| `JWT_SECRET` | _(需设置)_ | JWT 签名密钥（生产环境必须修改） |
| `DEBUG` | `false` | 调试模式 |
| `VITE_CDN_BASE` | `/` | 前端静态资源 CDN 地址 |

## 部署

### 生产部署

```bash
# 1. 配置环境变量
cp .env.example .env.production
# 编辑 .env.production 设置 JWT_SECRET/DB_PASSWORD

# 2. 构建并启动
docker compose --profile sandbox build
docker compose up -d

# 3. 执行数据库迁移
docker compose exec backend alembic upgrade head

# 4. 验证健康状态
curl http://localhost:8000/api/health
```

### Nginx/CDN

静态资源缓存和 CDN 配置见 `frontend/nginx.conf`。构建时通过 `VITE_CDN_BASE` 环境变量指定 CDN 地址：

```bash
docker compose run -e VITE_CDN_BASE=https://cdn.example.com/ frontend npm run build
```

### 数据库备份

```bash
# 手动备份
export DB_PASSWORD=your-password
bash scripts/backup_db.sh

# 自动备份（含 30 天轮换）
bash scripts/backup_db.sh --auto

# 恢复
bash scripts/backup_db.sh --restore backups/codequizhub_20250101_120000.dump
```

### 安全审计

```bash
python scripts/security_audit.py
```

## API 文档

FastAPI 自动生成 OpenAPI 文档：
- Swagger UI: `/api/docs`
- OpenAPI JSON: `/api/openapi.json`

## 测试

```bash
# 后端测试（142 项）
cd backend && python -m pytest tests/ -v

# 判题服务测试（77 项）
cd judge && python -m pytest tests/ -v
```

## 技术栈

- **后端**: Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16
- **前端**: React 18 / TypeScript / Vite / Ant Design 5
- **判题**: Docker 沙箱 / Python / Java / C / C++
- **中间件**: Redis / Nginx

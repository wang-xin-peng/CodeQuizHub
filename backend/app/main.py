import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from sqlalchemy import text, select

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.core.errors import AppError
from app.database import async_session_factory
from app.models.assignment import Assignment
from app.routers import auth, users, courses, problems, assignments, submissions, grades

settings = get_settings()

logger = logging.getLogger(__name__)


async def auto_close_assignments():
    """Periodically check and close overdue assignments."""
    while True:
        try:
            async with async_session_factory() as session:
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                result = await session.execute(
                    select(Assignment).where(
                        Assignment.status == "published",
                        Assignment.end_time < now,
                    )
                )
                overdue = result.scalars().all()
                for assignment in overdue:
                    assignment.status = "closed"
                if overdue:
                    await session.commit()
                    print(
                        f"  [scheduler] Closed {len(overdue)} overdue assignment(s)",
                        flush=True,
                    )
        except Exception as e:
            print(f"  [scheduler] Error: {e}", flush=True)
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-validate all dependencies on startup."""
    print("=" * 60, flush=True)
    print(f"  {settings.APP_NAME} starting up ...", flush=True)

    # ── Verify database connectivity ──
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        print("  ✓ Database connection OK", flush=True)
    except Exception as e:
        print(f"  ✗ Database connection FAILED: {e}", flush=True)
        print("  ✗ The application cannot function without a database.", flush=True)
        raise  # Fail fast — DB is non-negotiable

    # ── Verify Redis connectivity (non-fatal) ──
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        print("  ✓ Redis connection OK", flush=True)
    except Exception as e:
        print(f"  ✗ Redis connection FAILED: {e}", flush=True)
        print("  ✗ Judge queue and rate limiting are disabled.", flush=True)

    print("=" * 60, flush=True)

    # ── Start background scheduler for auto-closing assignments ──
    scheduler_task = asyncio.create_task(auto_close_assignments())
    print("  ✓ Assignment auto-close scheduler started", flush=True)

    yield  # App runs here

    # ── Shutdown ──
    scheduler_task.cancel()
    print("  ✓ Assignment auto-close scheduler stopped", flush=True)
    print("  Shutting down ...", flush=True)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Security headers (applied before CORS in middleware order)
app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code.value,
            "message": exc.message,
            "detail": None,
        },
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "请求过于频繁，请稍后再试",
            "detail": None,
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )


# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(courses.router, prefix="/api/courses", tags=["课程"])
app.include_router(problems.router, prefix="/api/problems", tags=["题目"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["作业"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["提交"])
app.include_router(grades.router, prefix="/api/grades", tags=["成绩"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

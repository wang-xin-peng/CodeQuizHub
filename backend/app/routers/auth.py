from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.errors import AuthenticationError, BusinessError
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.response import success_response
from app.schemas.user import LoginRequest, LoginResponse, RegisterRequest, UserResponse

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if username or email already exists
    existing = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if existing.scalar_one_or_none():
        raise BusinessError(
            ErrorCode.USER_ALREADY_EXISTS, "用户名或邮箱已存在", 409
        )

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return success_response(
        UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
        ).model_dump()
    )


@router.post("/login")
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise AuthenticationError("邮箱或密码错误")

    if not user.is_active:
        raise AuthenticationError("账号已被禁用", ErrorCode.AUTH_ACCOUNT_DISABLED)

    token = create_access_token(str(user.id), user.role)

    return success_response(
        LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_HOURS * 3600,
            user=UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                role=user.role,
                nickname=user.nickname,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
            ),
        ).model_dump()
    )

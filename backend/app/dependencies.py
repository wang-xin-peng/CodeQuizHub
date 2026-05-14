import uuid as uuid_mod

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.errors import AuthenticationError, ForbiddenError
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Parse JWT token and return current user."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token 已过期", ErrorCode.AUTH_TOKEN_EXPIRED)
    except jwt.InvalidTokenError:
        raise AuthenticationError("Token 无效", ErrorCode.AUTH_TOKEN_INVALID)

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token 无效", ErrorCode.AUTH_TOKEN_INVALID)

    try:
        user_uuid = uuid_mod.UUID(user_id)
    except (ValueError, AttributeError):
        raise AuthenticationError("Token 无效", ErrorCode.AUTH_TOKEN_INVALID)

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError("用户不存在", ErrorCode.AUTH_TOKEN_INVALID)
    if not user.is_active:
        raise AuthenticationError("账号已被禁用", ErrorCode.AUTH_ACCOUNT_DISABLED)

    return user


async def require_teacher(user: User = Depends(get_current_user)) -> User:
    """Require teacher or admin role."""
    if user.role not in ("teacher", "admin"):
        raise ForbiddenError("需要教师权限")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require admin role."""
    if user.role != "admin":
        raise ForbiddenError("需要管理员权限")
    return user

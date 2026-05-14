from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessError, AuthenticationError
from app.core.error_codes import ErrorCode
from app.core.security import hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.response import success_response, paginated_response
from app.schemas.user import ChangePasswordRequest, UpdateProfileRequest, UserResponse

router = APIRouter()


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
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


@router.put("/me")
async def update_profile(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.nickname is not None:
        user.nickname = body.nickname
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
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


@router.put("/me/password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.old_password, user.password_hash):
        raise AuthenticationError("原密码错误")

    user.password_hash = hash_password(body.new_password)
    await db.flush()

    return success_response(message="密码修改成功")


# Admin endpoints
@router.get("/admin/list")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = None,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    count_query = select(func.count()).select_from(User)

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    items = [
        UserResponse(
            id=str(u.id),
            username=u.username,
            email=u.email,
            role=u.role,
            nickname=u.nickname,
            avatar_url=u.avatar_url,
            is_active=u.is_active,
        ).model_dump()
        for u in users
    ]

    return paginated_response(items, total, page, page_size)


@router.put("/admin/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise BusinessError(ErrorCode.USER_NOT_FOUND, "用户不存在", 404)

    target.is_active = is_active
    await db.flush()

    return success_response(message="操作成功")


@router.put("/admin/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if role not in ("admin", "teacher", "student"):
        raise BusinessError(ErrorCode.VALIDATION_INVALID_FORMAT, "无效的角色", 400)

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise BusinessError(ErrorCode.USER_NOT_FOUND, "用户不存在", 404)

    target.role = role
    await db.flush()

    return success_response(message="角色变更成功")

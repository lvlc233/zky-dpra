from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from base.pg.entity import User
from base.pg.service import SessionDep, UserRepository
from controller.api.auth.router import get_current_user
from controller.response import Response
from common.security import get_password_hash
from controller.api.admin.schema import (
    UserAdminResponse,
    UserAdminListResponse,
    UserCreateRequest,
    UserUpdateRequest,
    PasswordResetRequest
)

router = APIRouter(prefix="/admin/users", tags=["admin-users"])

async def get_current_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """确认当前用户是否为管理员"""
    # 暂时保留对 admin@drap.com 的硬编码支持，同时也支持 is_admin 字段
    if not current_user.is_admin and current_user.email != 'admin@drap.com':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

AdminDep = Annotated[User, Depends(get_current_admin)]

@router.get("", response_model=Response[UserAdminListResponse])
async def list_users(
    admin: AdminDep,
    session: SessionDep,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None
):
    """获取用户列表 (管理员专用)"""
    offset = (page - 1) * size
    users, total = await UserRepository.get_users_paged(
        session, offset=offset, limit=size, search=search
    )
    
    user_responses = [
        UserAdminResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            is_active=u.is_active,
            is_admin=u.is_admin,
            created_at=u.created_at,
            updated_at=u.updated_at
        ) for u in users
    ]
    
    return Response.success(data=UserAdminListResponse(users=user_responses, total=total))

@router.post("", response_model=Response[UserAdminResponse])
async def create_user(
    admin: AdminDep,
    session: SessionDep,
    data: UserCreateRequest
):
    """创建新用户 (管理员专用)"""
    # 检查邮箱冲突
    existing = await UserRepository.get_user_by_email(session, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
        
    new_user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        is_active=data.is_active,
        is_admin=data.is_admin
    )
    
    try:
        created = await UserRepository.create_user(session, new_user)
        return Response.success(data=UserAdminResponse(
            id=created.id,
            email=created.email,
            full_name=created.full_name,
            is_active=created.is_active,
            is_admin=created.is_admin,
            created_at=created.created_at,
            updated_at=created.updated_at
        ))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"保存用户失败: {str(e)}")

@router.patch("/{user_id}", response_model=Response[UserAdminResponse])
async def update_user(
    user_id: UUID,
    admin: AdminDep,
    session: SessionDep,
    data: UserUpdateRequest
):
    """更新用户信息 (管理员专用)"""
    user = await UserRepository.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_admin is not None:
        user.is_admin = data.is_admin
        
    updated = await UserRepository.update_user(session, user)
    return Response.success(data=UserAdminResponse(
        id=updated.id,
        email=updated.email,
        full_name=updated.full_name,
        is_active=updated.is_active,
        is_admin=updated.is_admin,
        created_at=updated.created_at,
        updated_at=updated.updated_at
    ))

@router.post("/{user_id}/reset-password", response_model=Response[bool])
async def reset_password(
    user_id: UUID,
    admin: AdminDep,
    session: SessionDep,
    data: PasswordResetRequest
):
    """重置用户密码 (管理员专用)"""
    user = await UserRepository.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    user.hashed_password = get_password_hash(data.new_password)
    await UserRepository.update_user(session, user)
    return Response.success(data=True)

@router.delete("/{user_id}", response_model=Response[bool])
async def delete_user(
    user_id: UUID,
    admin: AdminDep,
    session: SessionDep
):
    """删除用户 (管理员专用)"""
    # 不允许管理员删除自己
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录的管理员账号")
        
    try:
        success = await UserRepository.delete_user(session, user_id)
        return Response.success(data=success)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")

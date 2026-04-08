from typing import List, Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from base.pg.entity import SystemModelConfig, User
from base.pg.service import SessionDep, SystemModelConfigRepository
from controller.api.auth.router import get_current_user
from controller.response import Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/admin/models", tags=["admin-models"])

async def get_current_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """确认当前用户是否为管理员"""
    if not current_user.is_admin and current_user.email != 'admin@drap.com':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

AdminDep = Annotated[User, Depends(get_current_admin)]

class SystemModelConfigUpdate(BaseModel):
    provider: str | None = None
    model_name: str | None = None
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    api_key: str | None = None
    base_url: str | None = None
    is_active: bool | None = None

@router.get("", response_model=Response[List[SystemModelConfig]])
async def list_system_configs(
    admin: AdminDep,
    session: SessionDep
):
    """获取所有系统模型配置"""
    configs = await SystemModelConfigRepository.get_all_configs(session)
    return Response.success(data=configs)

@router.patch("/{config_id}", response_model=Response[SystemModelConfig])
async def update_system_config(
    config_id: UUID,
    admin: AdminDep,
    session: SessionDep,
    data: SystemModelConfigUpdate
):
    """更新系统模型配置"""
    updated = await SystemModelConfigRepository.update_config(
        session, config_id, data.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="配置不存在")
    return Response.success(data=updated)

@router.post("", response_model=Response[SystemModelConfig])
async def create_system_config(
    admin: AdminDep,
    session: SessionDep,
    config_type: str,
    data: SystemModelConfigUpdate
):
    """创建系统模型配置 (如果不存在)"""
    existing = await SystemModelConfigRepository.get_config_by_type(session, config_type)
    if existing:
        raise HTTPException(status_code=400, detail=f"类型为 {config_type} 的配置已存在")
    
    new_config = SystemModelConfig(
        type=config_type,
        **data.model_dump()
    )
    created = await SystemModelConfigRepository.create_config(session, new_config)
    return Response.success(data=created)

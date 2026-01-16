"""
配置管理 API 路由。

开发者: BackendAgent
当前版本: v1.0_config_router
创建时间: 2026-01-14 20:30:00
"""

from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from base.pg.entity import User
from base.redis.service import get_redis
from controller.api.auth.router import get_current_user
from controller.response import Response
from service.config.config_service import ConfigService
from service.config.schema import (
    BatchConfigUpdate,
    UserConfigUpdate,
    UserSettingsResponse,
)
from base.pg.service import SessionDep

router = APIRouter(prefix="/users/settings", tags=["settings"])

# TODO: 2026-01-16 13:35,在审核了论文操作的相关模块后:lxz说,嗯,就是这种我们之前写的方式我觉得是更好的方式(就是这种注入)
# TODO: 不过这里的from base.config import get_session 导入失败,找不到 get_session
def get_config_service(
    db: SessionDep,
    redis: Redis = Depends(get_redis)
) -> ConfigService:
    return ConfigService(db, redis)

# TODO: 这里同样也是边界的问题...后期吧。
@router.get("", response_model=Response[UserSettingsResponse])
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    service: ConfigService = Depends(get_config_service)
):
    """
    获取当前用户的所有配置（合并了系统默认值和用户自定义值）。
    """
    settings = await service.get_user_settings(current_user.id)
    return Response.success(data=UserSettingsResponse(settings=settings))


@router.put("/batch", response_model=Response[UserSettingsResponse])
async def batch_update_settings(
    update_data: BatchConfigUpdate,
    current_user: User = Depends(get_current_user),
    service: ConfigService = Depends(get_config_service)
):
    """
    批量更新用户配置。
    """
    new_settings = await service.batch_update_user_settings(
        current_user.id, update_data.configs
    )
    return Response.success(data=UserSettingsResponse(settings=new_settings))


@router.put("/{key:path}", response_model=Response[UserSettingsResponse])
async def update_setting(
    key: str,
    update_data: UserConfigUpdate,
    current_user: User = Depends(get_current_user),
    service: ConfigService = Depends(get_config_service)
):
    """
    更新单个配置项。
    注意：key 可能包含点号（如 ui.theme），path 参数转换器可以匹配。
    """
    new_settings = await service.update_user_setting(
        current_user.id, key, update_data.value
    )
    return Response.success(data=UserSettingsResponse(settings=new_settings))


@router.post("/init-defaults", response_model=Response[bool])
async def init_default_configs(
    service: ConfigService = Depends(get_config_service),
    current_user: User = Depends(get_current_user)
):
    """
    初始化系统默认配置（仅限管理员或内部调用）。
    """
    # TODO: 这里is_superuser找不到,status.HTTP_403_FORBIDDEN,这个也是。
    if not current_user.is_superuser:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. Admin access required."
        )
        
    await service.init_default_configs()
    return Response.success(data=True)

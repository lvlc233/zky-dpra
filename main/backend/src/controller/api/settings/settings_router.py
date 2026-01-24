"""
配置管理 API 路由。

开发者: BackendAgent
当前版本: v1.2_config_router_complete
创建时间: 2026-01-14 20:30:00
更新时间: 2026-01-21 23:30:00
更新记录:
    [2026-01-14 20:30:00:v1.0_config_router:初始化配置路由]
    [2026-01-21 23:25:00:v1.1_config_router_refactor:重构配置路由以匹配统一架构文档]
    [2026-01-21 23:30:00:v1.2_config_router_complete:添加搜索配置路由，完成所有设置项迁移]
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from base.pg.entity import User
from base.pg.service import SessionDep
from controller.api.auth.router import get_current_user
from controller.response import Response
from controller.api.settings.schema import (
    AIReaderSettingsRequest,
    AIReaderSettingsResponse,
    SystemSettingsRequest,
    SystemSettingsResponse,
    AgentSettingsRequest,
    AgentSettingsResponse,
)
from controller.api.search.schema import (
    SearchSettingsRequest,
    SearchSettingsResponse,
)
from service.setting.setting_service import SettingService

router = APIRouter(prefix="/settings", tags=["settings"])


def get_setting_service(db: SessionDep) -> SettingService:
    return SettingService(db)


SettingServiceDep = Annotated[SettingService, Depends(get_setting_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.get("/reader/ai", response_model=Response[AIReaderSettingsResponse])
async def get_ai_reader_settings(
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    """获取AI阅读器设置"""
    items = await service.get_ai_reader_settings(current_user.id)
    return Response.success(data=AIReaderSettingsResponse(items=items))


@router.patch("/reader/ai", response_model=Response[AIReaderSettingsResponse])
async def update_ai_reader_settings(
    data: AIReaderSettingsRequest,
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    """更新AI阅读器设置"""
    items = await service.update_ai_reader_settings(current_user.id, data.items)
    return Response.success(data=AIReaderSettingsResponse(items=items))


@router.get("/system", response_model=Response[SystemSettingsResponse])
async def get_system_settings(
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    """获取系统设置"""
    settings = await service.get_system_settings(current_user.id)
    return Response.success(data=SystemSettingsResponse(system_settings=settings))


@router.patch("/system", response_model=Response[SystemSettingsResponse])
async def update_system_settings(
    data: SystemSettingsRequest,
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    """更新系统设置"""
    settings = await service.update_system_settings(current_user.id, data.system_settings)
    return Response.success(data=SystemSettingsResponse(system_settings=settings))


@router.get("/agent", response_model=Response[AgentSettingsResponse])
async def get_agent_settings(
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    """获取Agent(RAG/Embedding)设置"""
    settings = await service.get_agent_settings(current_user.id)
    return Response.success(data=AgentSettingsResponse(agent_settings=settings))


@router.patch("/agent", response_model=Response[AgentSettingsResponse])
async def update_agent_settings(
    data: AgentSettingsRequest,
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    """更新Agent(RAG/Embedding)设置"""
    settings = await service.update_agent_settings(current_user.id, data.agent_settings)
    return Response.success(data=AgentSettingsResponse(agent_settings=settings))


@router.get("/search", response_model=Response[SearchSettingsResponse])
async def get_search_settings(
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    """获取搜索设置"""
    settings = await service.get_search_settings(current_user.id)
    return Response.success(data=SearchSettingsResponse(search_settings=settings))


@router.put("/search", response_model=Response[SearchSettingsResponse])
async def update_search_settings(
    data: SearchSettingsRequest,
    current_user: CurrentUserDep,
    service: SettingServiceDep,
):
    """更新搜索设置"""
    settings = await service.update_search_settings(current_user.id, data.search_settings)
    return Response.success(data=SearchSettingsResponse(search_settings=settings))

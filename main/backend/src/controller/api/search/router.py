from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from redis.asyncio import Redis
from sqlmodel import Session

from base.config import get_session
from base.redis.service import get_redis
from service.config.config_service import ConfigService
from controller.api.search.schema import (
    SearchRequest, 
    SearchResponse, 
    SearchHistoryResponse,
    SearchSettingsResponse,
    SearchSettingsUpdate
)
from service.search.search_service import SearchService, get_search_service
from controller.api.auth.router import get_current_user
from base.pg.entity import User

router = APIRouter(prefix="/search", tags=["Search"])

SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

# TODO: 或可以把AI搜索和普通搜索分成两个?这样子,普通搜索也可以利用embadding进行语义搜索了。
@router.post("", response_model=SearchResponse)
async def search_papers(
    request: SearchRequest,
    current_user: CurrentUserDep,
    search_service: SearchServiceDep
):
    """
    搜索论文
    - 支持关键词匹配 (title, abstract)
    - 支持过滤 (日期, 状态)
    - 自动记录搜索历史
    """
    return await search_service.search_papers(current_user.id, request)

@router.get("/history", response_model=List[SearchHistoryResponse])
async def get_search_history(
    current_user: CurrentUserDep,
    search_service: SearchServiceDep,
    limit: int = Query(10, ge=1, le=50)
):
    """获取最近搜索历史"""
    return await search_service.get_search_history(current_user.id, limit)

@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_search_history(
    current_user: CurrentUserDep,
    search_service: SearchServiceDep
):
    """清空搜索历史"""
    await search_service.clear_search_history(current_user.id)


def get_config_service(
    db: Session = Depends(get_session),
    redis: Redis = Depends(get_redis)
) -> ConfigService:
    return ConfigService(db, redis)


@router.get("/config", response_model=SearchSettingsResponse)
async def get_search_config(
    current_user: CurrentUserDep,
    config_service: ConfigService = Depends(get_config_service)
):
    """获取搜索相关配置"""
    settings = await config_service.get_user_settings(current_user.id)
    # 使用 .get() 并提供默认值，防止配置未初始化
    return SearchSettingsResponse(
        enable_deep_reasoning=settings.get("search.enable_deep_reasoning", False),
        enable_auto_summary=settings.get("search.enable_auto_summary", True),
        default_sort_by=settings.get("search.default_sort_by", "relevance"),
        max_results=settings.get("search.max_results", 10),
        search_depth=settings.get("agent.search_depth", 3)
    )


@router.put("/config", response_model=SearchSettingsResponse)
async def update_search_config(
    data: SearchSettingsUpdate,
    current_user: CurrentUserDep,
    config_service: ConfigService = Depends(get_config_service)
):
    """更新搜索相关配置"""
    updates = {}
    if data.enable_deep_reasoning is not None:
        updates["search.enable_deep_reasoning"] = data.enable_deep_reasoning
    if data.enable_auto_summary is not None:
        updates["search.enable_auto_summary"] = data.enable_auto_summary
    if data.default_sort_by is not None:
        updates["search.default_sort_by"] = data.default_sort_by
    if data.max_results is not None:
        updates["search.max_results"] = data.max_results
    if data.search_depth is not None:
        updates["agent.search_depth"] = data.search_depth
        
    if updates:
        await config_service.batch_update_user_settings(current_user.id, updates)
        
    return await get_search_config(current_user, config_service)

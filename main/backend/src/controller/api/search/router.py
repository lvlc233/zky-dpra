from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from redis.asyncio import Redis
from sqlmodel import Session

from base.redis.service import get_redis
from base.pg.service import get_db_session
from service.setting.setting_service import SettingService
from controller.api.search.schema import (
    SearchRequest, 
    SearchResponse, 
    SearchHistoryResponse,
    SearchedPaperMetaResponse
)
from service.search.search_service import SearchService, get_search_service
from controller.api.auth.router import get_current_user
from controller.response import Response
from base.pg.entity import User
from base.arxiv.client import ArxivClient
from base.arxiv.parser import ArxivXmlParser
from service.papers.arxiv_service import ArxivService

router = APIRouter(prefix="/search", tags=["Search"])

SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

# TODO: 或可以把AI搜索和普通搜索分成两个?这样子,普通搜索也可以利用embadding进行语义搜索了。
@router.post("", response_model=Response[SearchedPaperMetaResponse])
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
    result = await search_service.search_papers(current_user.id, request)
    return Response.success(data=result)

@router.get("/history", response_model=Response[List[SearchHistoryResponse]])
async def get_search_history(
    current_user: CurrentUserDep,
    search_service: SearchServiceDep,
    limit: int = Query(10, ge=1, le=50)
):
    """获取最近搜索历史"""
    history = await search_service.get_search_history(current_user.id, limit)
    return Response.success(data=history)

@router.delete("/history", response_model=Response[bool])
async def clear_search_history(
    current_user: CurrentUserDep,
    search_service: SearchServiceDep
):
    """清空搜索历史"""
    await search_service.clear_search_history(current_user.id)
    return Response.success(data=True)

from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from controller.api.search.schema import SearchRequest, SearchResponse, SearchHistoryResponse
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

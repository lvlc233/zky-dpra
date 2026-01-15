from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from common.model.enums import PaperStatus
from service.papers.schema import PaperDTO


# TODO: 关于搜索条件这里有两类,第一类是搜索范围: 这个条件是指开启了某项条件后,搜索的query会全文匹配对应的字段,例如开启了作者条件,搜索, leCun,就会收缩到作者包含leCun的论文,第二种是在设置中的,例如是否开启摘要,搜索深度,排序方式间接影响搜索效果的
# TODO: 目前的搜索条件有: 标题,作者,摘要,年份,期刊。设置中的选项有,是否开启深度推理模式,是否开启自动生成摘要,搜索深度,排序方式[相关性,引用量,最新发表,影响力],发表年份范围
# TODO: 注意后期可能的修改和兼容。
class SearchFilter(BaseModel):
    """搜索过滤条件"""
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    authors: Optional[List[str]] = Field(None, description="作者列表")
    status: Optional[PaperStatus] = Field(None, description="论文状态")

class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="搜索关键词", min_length=1)
    filters: Optional[SearchFilter] = Field(None, description="过滤条件")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    # TODO: 不是语义而是AI搜索
    enable_semantic_search: bool = Field(False, description="是否启用语义搜索(暂未实现)")

class SearchHistoryResponse(BaseModel):
    """搜索历史响应"""
    id: UUID
    query: str
    created_at: datetime
    result_count: int

class SearchResponse(BaseModel):
    """搜索结果响应"""
    total: int
    items: List[PaperDTO]
    query_id: Optional[UUID] = Field(None, description="搜索历史记录ID")

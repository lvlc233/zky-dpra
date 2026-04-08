from typing import List, Optional, Literal, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from common.model.enums import PaperStatus
from service.papers.schema import PaperDTO, PaperMeta
from service.setting.schema import SearchSetting


class SearchFilter(BaseModel):
    """搜索过滤条件"""
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    authors: Optional[List[str]] = Field(None, description="作者列表")
    status: Optional[PaperStatus] = Field(None, description="论文状态")
    source: Optional[str] = Field(None, description="搜索来源(local/arXiv), 默认为local")

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def empty_string_to_none_filter(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="搜索关键词", min_length=1)
    filters: Optional[SearchFilter] = Field(None, description="过滤条件")
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(10, ge=1, le=100, alias="page_size", description="每页数量")
    enable_semantic_search: bool = Field(False, description="是否启用语义搜索(暂未实现)")

    # 文本匹配配置
    match_title: bool = Field(True, description="是否匹配标题")
    match_author: bool = Field(True, description="是否匹配作者")
    match_abstract: bool = Field(True, description="是否匹配摘要")
    match_source: bool = Field(True, description="是否匹配来源")
    enable_web_search: bool = Field(False, description="是否启用网络搜索")

    # 高级筛选配置 (对应 SearchSetting)
    match_analysis_status: Optional[Literal['unprocessed', 'processing', 'processed', 'error', '']] = Field(None, description="解析状态过滤")
    min_date: Optional[datetime] = Field(None, description="最小发表/上传时间")
    max_date: Optional[datetime] = Field(None, description="最大发表/上传时间")

    @field_validator('min_date', 'max_date', mode='before')
    @classmethod
    def empty_string_to_none_request(cls, v: Any) -> Any:
        if v == "":
            return None
        return v

    model_config = {
        "populate_by_name": True
    }


class SearchedPaperMetaResponse(BaseModel):
    """搜索结果响应 (Standardized)"""
    items: List[PaperMeta]
    total: int
    query_id: Optional[UUID] = Field(None, description="搜索历史记录ID")
    message: Optional[str] = Field(None, description="系统提示或警告消息")


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


class SearchSettingsRequest(BaseModel):
    search_settings: SearchSetting


class SearchSettingsResponse(BaseModel):
    search_settings: SearchSetting

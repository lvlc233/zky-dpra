'''
开发者: BackendAgent
当前版本: v1.0_paper_schema
创建时间: 2026年01月10日 10:05
更新时间: 2026年01月10日 10:05
更新记录:
    [2026年01月10日 10:05:v1.0_paper_schema:创建论文服务层数据模型，实现SaaS化契约设计]
'''

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from common.model.enums import PaperStatus


class PaperInfo(BaseModel):
    '''
    单篇论文信息模型 (External Source)
    
    描述:
    用于表示从外部源（如arXiv）获取的论文信息。
    '''
    title: str
    authors: List[str]
    abstract: str
    paper_url: Optional[str] = None
    pdf_url: Optional[str] = None
    published_date: Optional[str] = None
    categories: List[str] = []
    source_id: Optional[str] = None


class PaperListResponse(BaseModel):
    '''
    论文集获取响应模型 (Service Output)
    '''
    papers: List[PaperInfo]
    total_count: int
    source: Optional[str] = None
    fetch_url: Optional[str] = None


class PaperUploadResponse(BaseModel):
    """论文上传响应模型 (Service Output)"""
    paper_id: str
    status: str
    message: str


class PaperDTO(BaseModel):
    """
    论文业务模型 (Service Output)
    
    描述:
    用于Service层向Controller层传递论文数据的标准契约。
    完全解耦数据库实体。
    """
    id: UUID
    user_id: UUID
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    file_key: str
    file_url: Optional[str] = None
    status: PaperStatus
    error_message: Optional[str] = None
    created_at: datetime
    toc: Optional[List] = None
    # updated_at 暂时不包含，因为Entity中没有


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str
    limit: int = 10
    offset: int = 0


class SearchResponse(BaseModel):
    """搜索响应模型"""
    papers: List[PaperInfo]
    total_count: int
    query: str

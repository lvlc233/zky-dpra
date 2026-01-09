'''
开发者: BackendAgent
当前版本: v0.1_papers
创建时间: 2026年01月02日 10:16
更新时间: 2026年01月02日 10:16
更新记录:
    [2026年01月02日 10:16:v0.1_papers:重构请求模型位置，移除PaperFetchRequest（移至controller层）]
    [2026年01月02日 08:54:v0.1_paper_models:新增论文相关的响应数据模型]
'''

from pydantic import BaseModel
from typing import List, Optional


class PaperInfo(BaseModel):
    '''
    单篇论文信息模型

    字段说明:
    - title: 论文标题
    - authors: 作者列表
    - abstract: 论文摘要
    - paper_url: 论文详情页URL
    - pdf_url: PDF下载链接
    - published_date: 发表日期（可选）
    - categories: 分类标签（如arXiv的分类）
    - source_id: 来源ID（如arXiv编号）

    约束说明:
    - title, authors, abstract 为必填项，保证基本信息完整性
    - 其他字段可为空，适应不同来源的数据差异

    使用场景:
    - 作为单个论文信息的传递载体
    - 用于列表响应和详情查看
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
    论文集获取响应模型

    字段说明:
    - papers: 论文列表
    - total_count: 论文总数
    - source: 数据来源（如'arXiv'）
    - fetch_url: 原始请求的URL

    使用场景:
    - 作为获取论文集的完整响应
    - 包含元数据和论文列表
    '''
    papers: List[PaperInfo]
    total_count: int
    source: Optional[str] = None
    fetch_url: Optional[str] = None


# 数据库模型（用于内部引用）
from base.pg.entity import (
    User,
    Paper,
    PaperChunk,
    PaperSummary,
    ChatSession,
    ChatMessage,
    PaperStatus
)

# 新增请求/响应模型
class PaperUploadResponse(BaseModel):
    """论文上传响应模型"""
    paper_id: str
    status: str
    message: str


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    message: str
    sources: Optional[List[dict]] = None


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

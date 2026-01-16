from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from service.papers.schema import PaperDTO


class CollectionBase(BaseModel):
    """收藏夹基础模型"""
    name: str = Field(..., description="收藏夹名称")
    description: Optional[str] = Field(None, description="收藏夹描述")


class CollectionCreate(CollectionBase):
    """创建收藏夹请求模型"""
    pass


class CollectionUpdate(BaseModel):
    """更新收藏夹请求模型"""
    name: Optional[str] = Field(None, description="收藏夹名称")
    description: Optional[str] = Field(None, description="收藏夹描述")


class CollectionResponse(CollectionBase):
    """收藏夹响应模型"""
    id: UUID = Field(..., description="收藏夹ID")
    user_id: UUID = Field(..., description="所属用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class CollectionDetailResponse(CollectionResponse):
    """收藏夹详情响应模型"""
    papers: List[PaperDTO] = Field(default_factory=list, description="包含的论文列表")

# TODO: 添加论文应该考虑未解析(网络/本地的情况)-->是否在调度之前就已经完成了解析?流程需要明确下。
class AddPaperRequest(BaseModel):
    """添加论文请求模型"""
    paper_id: UUID = Field(..., description="论文ID")


class CollectionListResponse(BaseModel):
    """收藏夹列表响应模型"""
    items: List[CollectionResponse]
    total: int = Field(..., description="总数")
    limit: int = Field(..., description="每页限制")
    offset: int = Field(..., description="偏移量")
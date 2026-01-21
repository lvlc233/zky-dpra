from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


from service.reader.schema import (
    TocItem, Toc, Annotation, View, NoteMeta, AISummary,
    MindMapNode, MindMapEdge, MindMap, Record, Message,  Job
)


class PaperReaderMetaResponse(BaseModel):
    paper_id: UUID = Field(..., description="论文全局唯一标识(UUID)")
    url: Optional[str] = Field(None, alias="file_url", description="文件访问URL")
    summary: Optional[AISummary] = Field(None, description="论文AI总结")
    toc: Optional[Toc] = Field(None, description="论文目录结构")
    views: List[View] = Field(..., description="论文视图")
    notes: List[NoteMeta] = Field(..., description="论文笔记")
    mind_map: Optional[MindMap] = Field(None, description="论文AI脑图")
    history: List[Record] = Field(..., description="论文AI历史记录")
    jobs: List[Job] = Field(..., description="关联任务列表")

    model_config = ConfigDict(populate_by_name=True)


class TocResponse(BaseModel):
    items: List[TocItem]


class ViewResponse(BaseModel):
    view_id: UUID = Field(..., alias="id", description="视图id")
    name: str = Field(..., description="视图名")
    enable: bool = Field(..., alias="visible", description="开启状态")
    
    model_config = ConfigDict(populate_by_name=True)


class AnnotationRequest(BaseModel):
    type: Literal['highlight','translation','note'] = Field(..., description="注解类型[高光,翻译,随笔内容]")
    rect: List[Dict[str, float]] = Field(..., description="标注区域的几何坐标")
    content: str = Field(..., description="注解内容[随笔内容,翻译内容]")
    color: str = Field(..., description="RGB/Hex")


class AnnotationResponse(BaseModel):
    items: List[Annotation]


class NoteMetaResponse(BaseModel):
    items: List[NoteMeta]


class NoteResponse(BaseModel):
    note_id: UUID = Field(..., alias="id", description="笔记ID")
    title: Optional[str] = Field(None, description="笔记标题")
    page: Optional[int] = Field(None, description="笔记对应的页码")
    created_at: datetime = Field(..., description="创建时间")
    content: str = Field(..., description="笔记内容(Markdown)")

    model_config = ConfigDict(populate_by_name=True)


class AISummaryResponse(BaseModel):
    summary_config: Dict[str, str]


class MindMapResponse(BaseModel):
    nodes: List[MindMapNode]
    edges: List[MindMapEdge]


class RecordResponse(BaseModel):
    record_id: UUID = Field(..., alias="id", description="记录id")
    title: Optional[str] = Field(..., description="对话记录的标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(populate_by_name=True)


class MessageResponse(BaseModel):
    items: List[Message]


class JobListResponse(BaseModel):
    items: List[Job]

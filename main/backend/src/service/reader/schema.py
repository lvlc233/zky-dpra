from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

# TODO: 共享模型模式,但不太符合规格(Service层不应定义Create/Update等API契约模型),但是暂时没什么问题,就先这样子,等后期再说吧。
# 理想架构: 
# - Controller: 定义 Request/Response 模型
# - Service: 定义 DTO 模型
# - Mapper: 负责 Request -> DTO -> Response 的转换

class AnnotationBase(BaseModel):
    type: str # 'highlight' | 'note' | 'translate'
    rects: List[Dict[str, Any]] # {x, y, width, height, pageIndex}
    content: Optional[str] = None
    color: Optional[str] = None

class AnnotationCreate(AnnotationBase):
    pass

class AnnotationUpdate(BaseModel):
    content: Optional[str] = None
    color: Optional[str] = None

class AnnotationResponse(AnnotationBase):
    id: UUID
    layer_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LayerBase(BaseModel):
    name: str
    type: str = "user" # 'system' | 'user'
    visible: bool = True

class LayerCreate(LayerBase):
    pass

class LayerUpdate(BaseModel):
    name: Optional[str] = None
    visible: Optional[bool] = None

class LayerResponse(LayerBase):
    id: UUID
    paper_id: UUID
    user_id: UUID
    created_at: datetime
    annotations: List[AnnotationResponse] = []

    model_config = ConfigDict(from_attributes=True)

class LayerListResponse(BaseModel):
    layers: List[LayerResponse]

class SummaryCreate(BaseModel):
    summary_type: str = "abstract_rewrite" # 'abstract_rewrite' | 'key_points' | 'methodology'

class SummaryResponse(BaseModel):
    id: UUID
    paper_id: UUID
    summary_type: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NoteBase(BaseModel):
    title: Optional[str] = None
    content: str

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class NoteResponse(NoteBase):
    id: UUID
    paper_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class GraphNode(BaseModel):
    id: str
    label: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class MindMapCreate(BaseModel):
    # 可选，如果为空则初始化空图或触发生成
    graph_data: Optional[GraphData] = None

class MindMapUpdate(BaseModel):
    graph_data: GraphData

class MindMapResponse(BaseModel):
    id: UUID
    paper_id: UUID
    graph_data: GraphData
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

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

    class Config:
        from_attributes = True

class LayerBase(BaseModel):
    name: str
    type: str = "user" # 'system' | 'user'
    visible: bool = True

class LayerCreate(LayerBase):
    pass

class LayerResponse(LayerBase):
    id: UUID
    paper_id: UUID
    user_id: UUID
    created_at: datetime
    annotations: List[AnnotationResponse] = []

    class Config:
        from_attributes = True

class LayerListResponse(BaseModel):
    layers: List[LayerResponse]

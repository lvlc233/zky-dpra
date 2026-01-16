from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ReportCreate(BaseModel):
    type: str # 'deep_research' | 'related_work'

class ReportResponse(BaseModel):
    id: UUID
    paper_id: UUID
    title: str
    type: str
    status: str
    content: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReportListResponse(BaseModel):
    reports: List[ReportResponse]

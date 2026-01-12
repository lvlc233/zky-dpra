from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class ChatSessionCreate(BaseModel):
    agent_type: str = "chat" # 'chat' | 'search'
    context: Optional[Dict[str, Any]] = None # {paperId: ...}

class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    agent_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionListResponse(BaseModel):
    sessions: List[ChatSessionResponse]

class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageListResponse(BaseModel):
    messages: List[ChatMessageResponse]

class ChatMessageRequest(BaseModel):
    content: str
    files: Optional[List[str]] = None

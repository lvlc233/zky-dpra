from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ChatSessionCreate(BaseModel):
    agent_type: str = "chat" # 'chat' | 'search' | 'paper_chat'
    paper_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None # {paperId: ...}

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    agent_type: str
    paper_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatSessionListResponse(BaseModel):
    sessions: List[ChatSessionResponse]

class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatMessageListResponse(BaseModel):
    messages: List[ChatMessageResponse]

class ChatMessageRequest(BaseModel):
    content: str
    files: Optional[List[str]] = None

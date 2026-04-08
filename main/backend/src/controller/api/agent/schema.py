from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel

class PaperChatRequest(BaseModel):
    paper_id: UUID
    messages: List[Dict[str, Any]]
    chat_session_id: Optional[UUID] = None # 前端生成的会话ID,用于持久化状态
    
    class Config:
        json_schema_extra = {
            "example": {
                "paper_id": "123e4567-e89b-12d3-a456-426614174000",
                "messages": [
                    {"role": "user", "content": "这篇文章主要讲了什么？"}
                ]
            }
        }

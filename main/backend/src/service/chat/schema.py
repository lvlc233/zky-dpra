"""
开发者: BackendAgent
创建时间: 2026年01月10日
描述: Chat 模块的数据模型定义
"""

from typing import List, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """聊天响应模型"""
    message: str
    sources: Optional[List[dict]] = None

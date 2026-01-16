"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14 19:30
更新时间: 2026-01-14 19:30
更新记录:
    [2026-01-14 19:30:v1.0.0:定义 Agent 状态持久化相关的 API Schema]
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class AgentSessionSummary(BaseModel):
    """Agent 会话摘要"""
    agent_type: str = Field(..., description="Agent 类型")
    status: str = Field(..., description="会话状态 (active/interrupted/completed/error)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    interrupt_info: Optional[Dict[str, Any]] = Field(None, description="中断信息（如果有）")


class SessionStateSummaryResponse(BaseModel):
    """会话状态摘要响应"""
    chat_session_id: UUID
    agent_sessions: List[AgentSessionSummary]
    has_interrupted: bool = Field(..., description="是否有中断的会话")


class InterruptInfo(BaseModel):
    """中断信息"""
    interrupt_type: str = Field(..., description="中断类型 (strong/weak)")
    interrupt_data: Optional[Dict[str, Any]] = Field(None, description="中断数据")
    pending_todos: Optional[List[Dict[str, Any]]] = Field(None, description="待办事项（弱中断）")


class RestoreAgentSessionRequest(BaseModel):
    """恢复 Agent 会话请求"""
    resume_data: Optional[Dict[str, Any]] = Field(None, description="恢复数据（如用户输入）")


class RestoreAgentSessionResponse(BaseModel):
    """恢复 Agent 会话响应"""
    status: str = Field(..., description="恢复状态")
    can_resume: bool = Field(..., description="是否可以恢复")
    agent_type: Optional[str] = Field(None, description="Agent 类型")
    thread_id: Optional[str] = Field(None, description="线程 ID")
    interrupt_info: Optional[InterruptInfo] = Field(None, description="中断信息")
    todos: Optional[List[Dict[str, Any]]] = Field(None, description="待办事项")
    message: Optional[str] = Field(None, description="提示消息")


class CompleteTodoRequest(BaseModel):
    """完成待办事项请求"""
    result_data: Dict[str, Any] = Field(..., description="结果数据")


class CompleteTodoResponse(BaseModel):
    """完成待办事项响应"""
    status: str = Field(..., description="状态 (can_resume/has_more_todos)")
    agent_type: Optional[str] = Field(None, description="Agent 类型（可以恢复时）")
    thread_id: Optional[str] = Field(None, description="线程 ID（可以恢复时）")
    remaining_todos: Optional[int] = Field(None, description="剩余待办事项数量")
    message: str = Field(..., description="提示消息")


class AgentExecutionHistoryItem(BaseModel):
    """Agent 执行历史项"""
    timestamp: datetime = Field(..., description="时间戳")
    node: Optional[str] = Field(None, description="执行的节点")
    state_summary: Dict[str, Any] = Field(..., description="状态摘要")


class AgentExecutionHistoryResponse(BaseModel):
    """Agent 执行历史响应"""
    history: List[AgentExecutionHistoryItem]
    total: int = Field(..., description="总记录数")


class CreateStrongInterruptRequest(BaseModel):
    """创建强中断请求"""
    thread_id: str = Field(..., description="Agent 线程 ID")
    reason: str = Field(..., description="中断原因")
    message: str = Field(..., description="给用户的消息")
    payload: Optional[Dict[str, Any]] = Field(None, description="额外数据")
    options: Optional[List[str]] = Field(None, description="选项列表（选择型中断）")


class CreateWeakInterruptRequest(BaseModel):
    """创建弱中断请求"""
    thread_id: str = Field(..., description="Agent 线程 ID")
    reason: str = Field(..., description="中断原因")
    message: str = Field(..., description="消息")
    todo_type: str = Field(..., description="待办事项类型")
    todo_data: Dict[str, Any] = Field(..., description="待办事项数据")


class UserInputForInterruptRequest(BaseModel):
    """用户输入以恢复中断的请求"""
    user_input: Any = Field(..., description="用户输入（可以是任何类型）")
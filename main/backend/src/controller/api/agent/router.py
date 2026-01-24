"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-25
描述: Agent SSE 路由接口
"""

import json
import asyncio
from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from base.pg.service import SessionDep
from controller.api.auth.router import get_current_user
from base.pg.entity import User
from .schema import PaperChatRequest
from agent.paper_chat_agent.agent import paper_chat_agent_graph, paper_chat_workflow
from agent.base.persistence import AgentPersistenceService
from agent.base.checkpointer import get_postgres_checkpointer_context
from typing import List, Dict, Any
from uuid import UUID

router = APIRouter(prefix="/agent/paper_chat", tags=["Agent"])

from uuid import uuid4

@router.get("/sessions")
async def get_paper_chat_sessions(
    paper_id: UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文的历史会话列表"""
    persistence_service = AgentPersistenceService(session)
    sessions = await persistence_service.get_agent_sessions_by_paper(
        paper_id=paper_id,
        user_id=current_user.id
    )
    return sessions

@router.get("/history")
async def get_chat_history(
    thread_id: str,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """获取会话历史消息"""
    async with get_postgres_checkpointer_context() as checkpointer:
        app = paper_chat_workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        state = await app.aget_state(config)
        
        if not state or not state.values:
            return []
            
        messages = state.values.get("messages", [])
        return [
            {
                "role": "user" if isinstance(m, HumanMessage) else "assistant" if isinstance(m, AIMessage) else "system",
                "content": m.content,
                "timestamp": getattr(m, "timestamp", None)
            }
            for m in messages
        ]

@router.delete("/sessions/{thread_id}")
async def delete_agent_session(
    thread_id: str,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """删除会话"""
    persistence_service = AgentPersistenceService(session)
    success = await persistence_service.delete_agent_session(thread_id, current_user.id)
    return {"success": success}

import logging

logger = logging.getLogger(__name__)

@router.post("/stream")
async def stream_paper_chat(
    req: PaperChatRequest,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """
    流式对话接口 (SSE)
    支持 Agentic RAG 模式: 自动检索、引用、思考
    """
    logger.info(f"Stream request received. ThreadID: {req.chat_session_id}, PaperID: {req.paper_id}")
    
    # 1. Config & Persistence
    # 注入 session 和 paper_id 供工具使用
    # 如果前端传递了 chat_session_id, 则使用它作为 thread_id; 否则生成随机的 (不持久化)
    thread_id = str(req.chat_session_id) if req.chat_session_id else str(uuid4())
    logger.info(f"Using thread_id: {thread_id}")
    
    # 确保 AgentSession 存在
    persistence_service = AgentPersistenceService(session)
    agent_session = await persistence_service.get_agent_session_by_thread(thread_id)
    
    if not agent_session:
        logger.info("Creating new AgentSession")
        # 生成标题 (取第一条用户消息的前30个字符)
        title = "新对话"
        first_user_msg = next((m for m in req.messages if m.get("role") == "user"), None)
        if first_user_msg:
             content = first_user_msg.get("content", "")
             if content:
                 title = content[:30] + "..." if len(content) > 30 else content

        await persistence_service.create_agent_session(
            user_id=current_user.id,
            agent_type="paper_chat",
            thread_id=thread_id,
            paper_id=req.paper_id,
            title=title
        )
    else:
        logger.info(f"Found existing AgentSession: {agent_session.title}")

    # 2. Construct State
    lc_messages = []
    for m in req.messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
        elif role == "system":
            lc_messages.append(SystemMessage(content=content))
            
    initial_state = {
        "messages": lc_messages,
        "paper_id": str(req.paper_id),
        # 其他字段由 Agent 内部填充
    }
    
    # 2. Config
    config = {
        "configurable": {
            "session": session,
            "paper_id": str(req.paper_id),
            "user_id": str(current_user.id),
            "thread_id": thread_id
        }
    }

    # 3. Stream Generator
    async def event_generator():
        logger.info("Starting event_generator")
        try:
            async with get_postgres_checkpointer_context() as checkpointer:
                logger.info("Checkpointer context acquired")
                # 动态编译带 Checkpointer 的图
                app = paper_chat_workflow.compile(checkpointer=checkpointer)
                logger.info("Graph compiled")
                
                # 使用 astream_events 获取详细事件 (Token 流 + 工具调用)
                async for event in app.astream_events(
                    initial_state, 
                    config=config, 
                    version="v2"
                ):
                    kind = event["event"]
                    logger.debug(f"Event received: {kind}")
                    
                    # Token Streaming
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            yield {
                                "event": "message",
                                "data": json.dumps({"content": content})
                            }
                            
                    # Tool Events
                    elif kind == "on_tool_start":
                         yield {
                            "event": "tool_start",
                            "data": json.dumps({
                                "tool": event["name"], 
                                "input": event["data"].get("input")
                            })
                        }
                    elif kind == "on_tool_end":
                         # 输出可能很长，视情况截断或全量
                         output = event["data"].get("output")
                         if output:
                             output_str = str(output)
                             # 限制长度避免 SSE 包过大
                             if len(output_str) > 2000:
                                 output_str = output_str[:2000] + "...(truncated)"
                                 
                             yield {
                                "event": "tool_end",
                                "data": json.dumps({
                                    "tool": event["name"], 
                                    "output": output_str
                                })
                            }
    
            # End of stream
            logger.info("Stream finished successfully")
            yield {"event": "done", "data": "[DONE]"}
            
        except Exception as e:
            logger.error(f"Error in event_generator: {e}", exc_info=True)
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())

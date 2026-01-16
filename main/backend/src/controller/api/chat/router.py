from typing import List, Optional, AsyncGenerator
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from loguru import logger
import asyncio
import json

from base.pg.service import get_current_user_id, SessionDep
from base.pg.entity import User
from controller.api.chat.schema import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionListResponse,
    ChatMessageResponse, ChatMessageListResponse, ChatMessageRequest,
    ChatSessionUpdate
)
from service.chat.chat_service import ChatService
from controller.response import Response
from agent.paper_chat_agent.agent import paper_chat_agent_graph
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sessions", response_model=Response[ChatSessionResponse])
async def create_session(
    session_in: ChatSessionCreate,
    session: SessionDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """创建新的聊天会话"""
    service = ChatService(session)
    new_session = await service.create_session(user_id, session_in)
    return Response.success(data=new_session)

@router.get("/sessions", response_model=Response[ChatSessionListResponse])
async def list_sessions(
    session: SessionDep,
    limit: int = 20,
    user_id: UUID = Depends(get_current_user_id)
):
    """获取会话列表"""
    service = ChatService(session)
    sessions = await service.list_sessions(user_id, limit)
    return Response.success(data={"sessions": sessions})

@router.get("/sessions/{session_id}", response_model=Response[ChatSessionResponse])
async def get_session(
    session_id: UUID,
    session: SessionDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """获取会话详情"""
    service = ChatService(session)
    chat_session = await service.get_session(session_id, user_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return Response.success(data=chat_session)

@router.patch("/sessions/{session_id}", response_model=Response[ChatSessionResponse])
async def update_session(
    session_id: UUID,
    session_in: ChatSessionUpdate,
    session: SessionDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """更新会话信息"""
    service = ChatService(session)
    updated_session = await service.update_session(session_id, user_id, session_in)
    if not updated_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return Response.success(data=updated_session)

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    session: SessionDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """删除会话"""
    service = ChatService(session)
    success = await service.delete_session(session_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return Response.success(message="Session deleted successfully")

@router.get("/sessions/{session_id}/messages", response_model=Response[ChatMessageListResponse])
async def get_history(
    session_id: UUID,
    session: SessionDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """获取会话历史消息"""
    # 验证 session 归属
    service = ChatService(session)
    chat_session = await service.get_session(session_id, user_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    messages = await service.get_messages(session_id)
    return Response.success(data={"messages": messages})
# TODO: 这里还是有问题,等后面搞Agent了再处理。
@router.post("/sessions/{session_id}/message")
async def send_message(
    session_id: UUID,
    request: ChatMessageRequest,
    session: SessionDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    发送消息并返回 SSE 流 (支持 Paper Chat Agent)
    """
    # 1. 验证 Session
    service = ChatService(session)
    chat_session = await service.get_session(session_id, user_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. 保存用户消息
    await service.save_message(session_id, "user", request.content)
    
    # 3. 准备 Agent 运行环境
    async def event_generator():
        yield f"event: metadata\ndata: {json.dumps({'run_id': str(uuid4()), 'session_id': str(session_id)})}\n\n"
        
        full_response = ""
        
        # 如果是 paper_chat，使用 Graph
        if chat_session.agent_type == "paper_chat" and chat_session.paper_id:
            try:
                # 准备状态
                # 需加载历史消息 (TODO: 优化为只加载最近 N 条)
                # 这里简化为只传当前消息
                state_input = {
                    "messages": [HumanMessage(content=request.content)],
                    "paper_id": str(chat_session.paper_id),
                    "chat_history": [] # 暂不加载历史
                }
                
                # 注意: service.session 是 AsyncSession，LangGraph 需要 config 传递依赖?
                # paper_chat_agent_graph 内部工具可能需要 DB access. 
                # 这里 config 传递 session 可能需要适配 checkpointer 或 tool.
                # 假设 graph 内部工具自行处理或通过 config 传递.
                # 之前的实现: config = {"configurable": {"session": session}}
                # 这里 service.session 就是 session.
                
                config = {"configurable": {"session": service.session}}
                
                async for event in paper_chat_agent_graph.astream_events(state_input, config=config, version="v1"):
                    kind = event["event"]
                    
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            full_response += content
                            yield f"event: token\ndata: {json.dumps(content)}\n\n"
                            
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                return
        else:
            # Mock 其他类型的 Agent
            mock_resp = f"Echo: {request.content} (Agent: {chat_session.agent_type})"
            full_response = mock_resp
            for word in mock_resp.split():
                yield f"event: token\ndata: {json.dumps(word + ' ')}\n\n"
                await asyncio.sleep(0.05)
        
        # 4. 保存 AI 回复
        # 注意: 此时 service.session 可能已过期或需要重新关联
        # 简单起见，我们假设 session 在 generator 结束前有效
        try:
            await service.save_message(session_id, "assistant", full_response)
        except Exception as e:
            logger.error(f"Failed to save AI response: {e}")
        
        yield f"event: finish\ndata: {json.dumps({'reason': 'stop'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

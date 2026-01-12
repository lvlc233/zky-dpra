from uuid import UUID, uuid4
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from loguru import logger
import asyncio
import json

from controller.api.chat.schema import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionListResponse,
    ChatMessageResponse, ChatMessageListResponse, ChatMessageRequest
)

# 临时 Mock 依赖
def get_current_user_id():
    return UUID("12345678-1234-5678-1234-567812345678")

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    session_in: ChatSessionCreate,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Implement DB create
    return {
        "id": uuid4(),
        "title": f"New Session {datetime.utcnow().strftime('%H:%M')}",
        "agent_type": session_in.agent_type,
        "created_at": datetime.utcnow()
    }

@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_sessions(
    limit: int = 20,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Implement DB list
    return {"sessions": []}

@router.get("/sessions/{session_id}/messages", response_model=ChatMessageListResponse)
async def get_history(
    session_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Implement DB list
    return {"messages": []}

@router.post("/sessions/{session_id}/message")
async def send_message(
    session_id: UUID,
    request: ChatMessageRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    发送消息并返回 SSE 流
    """
    logger.info(f"Chat message received: {request.content}")

    async def event_generator():
        # 1. Metadata
        yield f"event: metadata\ndata: {json.dumps({'run_id': str(uuid4()), 'session_id': str(session_id)})}\n\n"
        await asyncio.sleep(0.1)

        # 2. Token (Mock)
        response_text = f"Received: {request.content}. This is a mock streaming response."
        for word in response_text.split():
            yield f"event: token\ndata: {json.dumps(word + ' ')}\n\n"
            await asyncio.sleep(0.1)

        # 3. Finish
        yield f"event: finish\ndata: {json.dumps({'reason': 'stop'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

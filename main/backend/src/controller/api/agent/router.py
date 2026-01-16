"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14 19:45
更新时间: 2026-01-14 19:45
更新记录:
    [2026-01-14 19:45:v1.0.0:实现 Agent 状态持久化相关的 API 路由]
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body
from loguru import logger

from base.pg.service import get_current_user_id
from controller.response import Response
from service.agent.agent_state_service import AgentStateService, get_agent_state_service
from .schema import (
    SessionStateSummaryResponse,
    RestoreAgentSessionRequest,
    RestoreAgentSessionResponse,
    CompleteTodoRequest,
    CompleteTodoResponse,
    AgentExecutionHistoryResponse,
    CreateStrongInterruptRequest,
    CreateWeakInterruptRequest,
    UserInputForInterruptRequest
)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/sessions/{chat_session_id}/state", response_model=Response[SessionStateSummaryResponse])
async def get_session_state_summary(
    chat_session_id: UUID,
    service: AgentStateService = Depends(get_agent_state_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """获取会话状态摘要"""
    try:
        summary = await service.get_session_state_summary(user_id, chat_session_id)
        return Response.success(data=summary)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session state summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/{thread_id}/restore", response_model=Response[RestoreAgentSessionResponse])
async def restore_agent_session(
    thread_id: str,
    request: RestoreAgentSessionRequest,
    service: AgentStateService = Depends(get_agent_state_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """恢复 Agent 会话"""
    try:
        result = await service.restore_agent_session(
            user_id=user_id,
            thread_id=thread_id,
            resume_data=request.resume_data
        )
        return Response.success(data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore agent session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/todos/{todo_id}/complete", response_model=Response[CompleteTodoResponse])
async def complete_todo(
    todo_id: UUID,
    request: CompleteTodoRequest,
    service: AgentStateService = Depends(get_agent_state_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """完成待办事项"""
    try:
        result = await service.complete_todo_and_resume(
            user_id=user_id,
            todo_id=todo_id,
            result_data=request.result_data
        )
        return Response.success(data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete todo: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{thread_id}/history", response_model=Response[AgentExecutionHistoryResponse])
async def get_agent_execution_history(
    thread_id: str,
    limit: int = 50,
    service: AgentStateService = Depends(get_agent_state_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """获取 Agent 执行历史"""
    try:
        history = await service.get_agent_execution_history(
            user_id=user_id,
            thread_id=thread_id,
            limit=limit
        )
        return Response.success(data={
            "history": history,
            "total": len(history)
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent execution history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/interrupts/strong")
async def create_strong_interrupt(
    request: CreateStrongInterruptRequest,
    service: AgentStateService = Depends(get_agent_state_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """创建强中断（开发/测试用）"""
    # 注意：实际项目中，中断应该由 Agent 内部逻辑触发，而不是通过 API
    # 这个接口主要用于开发和测试
    try:
        # 验证会话归属
        agent_session = await service.persistence_service.get_agent_session_by_thread(request.thread_id)
        if not agent_session or agent_session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Agent session not found")

        # 创建中断（这里只是演示，实际应该通过 Agent 内部逻辑）
        logger.info(f"Creating strong interrupt for thread {request.thread_id}: {request.reason}")

        return Response.success(message="Interrupt created (demo)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create strong interrupt: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/interrupts/weak")
async def create_weak_interrupt(
    request: CreateWeakInterruptRequest,
    service: AgentStateService = Depends(get_agent_state_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """创建弱中断（开发/测试用）"""
    # 注意：实际项目中，弱中断应该由 Agent 内部逻辑触发
    try:
        # 验证会话归属
        agent_session = await service.persistence_service.get_agent_session_by_thread(request.thread_id)
        if not agent_session or agent_session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Agent session not found")

        # 创建弱中断（待办事项）
        todo = await service.persistence_service.create_todo(
            agent_session_id=agent_session.id,
            todo_type=request.todo_type,
            todo_data=request.todo_data
        )

        # 更新会话状态
        await service.persistence_service.update_agent_session_status(
            thread_id=request.thread_id,
            status="interrupted",
            interrupt_type="weak",
            interrupt_data={
                "reason": request.reason,
                "message": request.message
            }
        )

        return Response.success(data={
            "todo_id": todo.id,
            "message": "Weak interrupt created successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create weak interrupt: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/interrupts/{thread_id}/resume")
async def resume_from_interrupt_with_input(
    thread_id: str,
    request: UserInputForInterruptRequest,
    service: AgentStateService = Depends(get_agent_state_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """通过用户输入恢复中断"""
    try:
        result = await service.restore_agent_session(
            user_id=user_id,
            thread_id=thread_id,
            resume_data={"user_input": request.user_input}
        )

        if result["status"] == "resumed":
            return Response.success(data=result, message="Agent session resumed successfully")
        else:
            return Response.success(data=result, message="Failed to resume agent session")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume from interrupt: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
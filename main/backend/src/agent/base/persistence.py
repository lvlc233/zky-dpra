"""
开发者: LangGraphAgent
当前版本: v1.1.1
创建时间: 2026-01-14 18:00
更新时间: 2026-01-25 10:15
更新记录:
    [2026-01-14 18:00:v1.0.0:实现 Agent 持久化服务，集成 LangGraph checkpointer 和自定义持久化逻辑]
    [2026-01-25 10:00:v1.1.0:修复 AgentSession 持久化逻辑，支持 title 和 delete]
    [2026-01-25 10:15:v1.1.1:移除 AgentTodo 和 AgentSession 中不存在的字段，简化 CheckpointSaver]
"""

from typing import Any, Optional, Dict, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.checkpoint.base import BaseCheckpointSaver

from base.pg.entity import AgentSession


class AgentPersistenceService:
    """
    Agent 持久化服务
    负责管理 Agent 会话记录 (AgentSession)
    注意：具体的对话状态由 LangGraph 的 Checkpointer 管理，此处只管理会话元数据。
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_agent_session(
        self,
        user_id: UUID,
        agent_type: str, # 保留参数但忽略，因为表里没有
        thread_id: str,
        paper_id: Optional[UUID] = None,
        title: str = "New Chat"
    ) -> AgentSession:
        """创建 Agent 会话记录"""
        # 检查是否已存在 (避免重复创建)
        existing = await self.get_agent_session_by_thread(thread_id)
        if existing:
            return existing

        agent_session = AgentSession(
            user_id=user_id,
            thread_id=thread_id,
            paper_id=paper_id,
            title=title
        )
        self.session.add(agent_session)
        await self.session.commit()
        await self.session.refresh(agent_session)
        return agent_session

    async def delete_agent_session(self, thread_id: str, user_id: UUID) -> bool:
        """删除 Agent 会话"""
        stmt = select(AgentSession).where(
            AgentSession.thread_id == thread_id,
            AgentSession.user_id == user_id
        )
        result = await self.session.execute(stmt)
        agent_session = result.scalar_one_or_none()
        
        if agent_session:
            await self.session.delete(agent_session)
            await self.session.commit()
            return True
        return False

    async def update_agent_session_title(self, thread_id: str, title: str) -> Optional[AgentSession]:
        """更新会话标题"""
        agent_session = await self.get_agent_session_by_thread(thread_id)
        if agent_session:
            agent_session.title = title
            self.session.add(agent_session)
            await self.session.commit()
            await self.session.refresh(agent_session)
        return agent_session

    async def get_agent_session_by_thread(self, thread_id: str) -> Optional[AgentSession]:
        """通过 thread_id 获取 Agent 会话"""
        stmt = select(AgentSession).where(AgentSession.thread_id == thread_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_agent_sessions_by_paper(
        self,
        paper_id: UUID,
        user_id: UUID,
        limit: int = 50
    ) -> List[AgentSession]:
        """获取论文关联的所有 Agent 会话"""
        stmt = select(AgentSession).where(
            AgentSession.paper_id == paper_id,
            AgentSession.user_id == user_id
        ).order_by(desc(AgentSession.created_at)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class EnhancedCheckpointSaver:
    """
    增强的 Checkpoint 保存器 (简化版)
    目前仅作为 LangGraph checkpointer 的代理，不再处理额外的 Todo/Status 逻辑。
    """

    def __init__(
        self,
        checkpointer: BaseCheckpointSaver,
        persistence_service: AgentPersistenceService
    ):
        self.checkpointer = checkpointer
        self.persistence_service = persistence_service

    async def asave_checkpoint(
        self,
        thread_id: str,
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> None:
        """保存 checkpoint"""
        # 直接保存到 LangGraph checkpoint
        await self.checkpointer.aput(thread_id, checkpoint, metadata)

    async def arestore_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """恢复 checkpoint"""
        return await self.checkpointer.aget(thread_id)

    # 代理其他方法到原始 checkpointer
    def __getattr__(self, name):
        return getattr(self.checkpointer, name)

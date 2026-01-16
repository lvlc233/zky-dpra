"""
开发者: BackendAgent
当前版本: v1.0
创建时间: 2026年01月14日
描述: 聊天服务层，处理会话管理和消息存储
"""

from typing import List, Optional, Sequence
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException

from base.pg.entity import ChatSession, ChatMessage
from base.pg.service import SessionDep
from controller.api.chat.schema import ChatSessionCreate, ChatSessionUpdate

# TODO: 这里用仓储吗?而是直接用Service?按照规范来说应该用仓储吧。
class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, user_id: UUID, session_in: ChatSessionCreate) -> ChatSession:
        """创建新的聊天会话"""
        # 自动推断 agent_type
        agent_type = session_in.agent_type
        if session_in.paper_id:
            agent_type = "paper_chat"

        new_session = ChatSession(
            user_id=user_id,
            # TODO: 时间的问题要找个时间解决啊。
            title=f"Session {datetime.utcnow().strftime('%m-%d %H:%M')}",
            agent_type=agent_type,
            paper_id=session_in.paper_id
        )
        
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)
        return new_session

    async def list_sessions(self, user_id: UUID, limit: int = 20) -> Sequence[ChatSession]:
        """获取会话列表"""
        stmt = select(ChatSession).where(
            ChatSession.user_id == user_id
        ).order_by(desc(ChatSession.created_at)).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_session(self, session_id: UUID, user_id: UUID) -> Optional[ChatSession]:
        """获取单个会话"""
        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_session(self, session_id: UUID, user_id: UUID, session_in: ChatSessionUpdate) -> Optional[ChatSession]:
        """更新会话信息 (如标题)"""
        session = await self.get_session(session_id, user_id)
        if not session:
            return None
        
        if session_in.title is not None:
            session.title = session_in.title
            
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
        """删除会话"""
        # 首先检查是否存在
        session = await self.get_session(session_id, user_id)
        if not session:
            return False
        # TODO: 校验下吧。
        # 级联删除消息 (如果数据库未设置级联删除，则需手动删除)
        # 这里假设数据库外键有 ON DELETE CASCADE，或者手动删除
        # SQLModel/SQLAlchemy 默认不开启 ORM 级联，需手动处理
        msg_stmt = delete(ChatMessage).where(ChatMessage.session_id == session_id)
        await self.session.execute(msg_stmt)
        
        await self.session.delete(session)
        await self.session.commit()
        return True

    async def get_messages(self, session_id: UUID) -> Sequence[ChatMessage]:
        """获取会话消息历史"""
        stmt = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def save_message(self, session_id: UUID, role: str, content: str, sources: Optional[List[dict]] = None) -> ChatMessage:
        """保存消息"""
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources
        )
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg



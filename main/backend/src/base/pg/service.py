'''
开发者: BackendAgent
当前版本: v1.0_pg_service
创建时间: 2026年01月09日 16:00
更新时间: 2026年01月09日 16:00
更新记录:
    [2026年01月09日 16:00:v1.0_pg_service:实现数据库连接管理和Repository模式，封装Paper和Chunk的CRUD操作]
'''

from typing import  List, Optional, Annotated
from uuid import UUID


from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import select
from fastapi import Depends



from base.config import settings
from base.pg.entity import Paper, PaperChunk, PaperStatus, User


# Database Connection Management
# Ensure the database URL is async compatible (postgresql+asyncpg)
DB_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    DB_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session_factory = async_sessionmaker(
    engine, expire_on_commit=False
)


async def get_db():
    async with async_session_factory() as session:
        yield session
# 定义 SessionDep 类型别名
SessionDep = Annotated[AsyncSession, Depends(get_db)]


class PaperRepository:
    """论文相关的数据访问层"""

    @staticmethod
    async def create_paper(session: AsyncSession, paper: Paper) -> Paper:
        """创建论文记录"""
        session.add(paper)
        await session.commit()
        await session.refresh(paper)
        return paper

    @staticmethod
    async def get_paper_by_id(session: AsyncSession, paper_id: UUID) -> Optional[Paper]:
        """根据ID获取论文"""
        statement = select(Paper).where(Paper.id == paper_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_paper_status(
        session: AsyncSession, 
        paper_id: UUID, 
        status: PaperStatus, 
        error_message: Optional[str] = None
    ) -> Optional[Paper]:
        """更新论文状态"""
        paper = await PaperRepository.get_paper_by_id(session, paper_id)
        if paper:
            paper.status = status
            if error_message:
                paper.error_message = error_message
            session.add(paper)
            await session.commit()
            await session.refresh(paper)
        return paper

    @staticmethod
    async def update_paper_file_info(
        session: AsyncSession,
        paper_id: UUID,
        file_key: str,
        file_url: Optional[str] = None
    ) -> Optional[Paper]:
        """更新论文文件信息"""
        paper = await PaperRepository.get_paper_by_id(session, paper_id)
        if paper:
            paper.file_key = file_key
            if file_url:
                paper.file_url = file_url
            session.add(paper)
            await session.commit()
            await session.refresh(paper)
        return paper

    @staticmethod
    async def update_paper_metadata(
        session: AsyncSession,
        paper_id: UUID,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None
    ) -> Optional[Paper]:
        """更新论文元数据"""
        paper = await PaperRepository.get_paper_by_id(session, paper_id)
        if paper:
            if title:
                paper.title = title
            if authors:
                paper.authors = authors
            session.add(paper)
            await session.commit()
            await session.refresh(paper)
        return paper

    @staticmethod
    async def get_user_papers(
        session: AsyncSession,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> List[Paper]:
        """获取用户的论文列表"""
        statement = select(Paper).where(Paper.user_id == user_id).order_by(Paper.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def delete_paper(session: AsyncSession, paper_id: UUID) -> bool:
        """删除论文及其相关数据"""
        paper = await PaperRepository.get_paper_by_id(session, paper_id)
        if paper:
            await session.delete(paper)
            await session.commit()
            return True
        return False

    @staticmethod
    async def create_paper_chunks(session: AsyncSession, chunks: List[PaperChunk]) -> List[PaperChunk]:
        """批量创建论文切片"""
        for chunk in chunks:
            session.add(chunk)
        await session.commit()
        # await session.refresh(chunks) # refresh list might be slow, skip if not needed
        return chunks
    
    @staticmethod
    async def get_chunks_by_paper_id(session: AsyncSession, paper_id: UUID) -> List[PaperChunk]:
        """获取指定论文的所有切片"""
        statement = select(PaperChunk).where(PaperChunk.paper_id == paper_id).order_by(PaperChunk.chunk_index)
        result = await session.execute(statement)
        return result.scalars().all()


class UserRepository:
    """用户相关的数据访问层"""

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: UUID) -> Optional[User]:
        """根据ID获取用户"""
        statement = select(User).where(User.id == user_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(session: AsyncSession, user: User) -> User:
        """创建用户"""
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

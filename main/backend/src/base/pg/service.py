
import logging
from typing import AsyncGenerator, Optional, List, Annotated, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func, delete, update
from sqlalchemy.orm import selectinload
from fastapi import Depends

from base.config import settings
from base.pg.entity import User, Paper, Collection, CollectionPaper, PaperChunk, PaperSummary, Annotation, Note, MindMap, AgentSession, Job, SearchApiConfig, SystemModelConfig, SearchHistory
from common.model.enums import PaperStatus

logger = logging.getLogger(__name__)

# 1. 创建异步引擎
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    database_url,
    echo=False,  # Set to True for SQL query logging
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
)

# 2. 创建异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# 3. 获取数据库会话的依赖项
async def _get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Core session generator logic.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session.
    """
    async for session in _get_session():
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


class UserRepository:
    """用户相关的数据访问层"""

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: UUID) -> Optional[User]:
        statement = select(User).where(User.id == user_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_all_users_count(session: AsyncSession) -> int:
        statement = select(func.count()).select_from(User)
        result = await session.execute(statement)
        return result.scalar() or 0

    @staticmethod
    async def get_users_paged(
        session: AsyncSession, 
        offset: int = 0, 
        limit: int = 10,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        statement = select(User)
        if search:
            search_filter = f"%{search}%"
            statement = statement.where(
                (User.email.ilike(search_filter)) | 
                (User.full_name.ilike(search_filter))
            )
        
        # Get total count
        count_statement = select(func.count()).select_from(statement.subquery())
        total_result = await session.execute(count_statement)
        total_count = total_result.scalar() or 0
        
        # Get paged results
        statement = statement.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await session.execute(statement)
        users = list(result.scalars().all())
        
        return users, total_count

    @staticmethod
    async def delete_user(session: AsyncSession, user_id: UUID) -> bool:
        """级联删除用户及其所有关联资源"""
        from base.pg.entity import User, Paper, Collection, CollectionPaper, AgentSession, Note, Job, Annotation, PaperChunk, PaperSummary, MindMap, SearchHistory
        
        # 1. 获取该用户的所有论文ID
        paper_ids_stmt = select(Paper.id).where(Paper.user_id == user_id)
        paper_ids_result = await session.execute(paper_ids_stmt)
        paper_ids = [row[0] for row in paper_ids_result.fetchall()]
        
        if paper_ids:
            # 删除论文关联的子资源
            await session.execute(delete(Annotation).where(Annotation.paper_id.in_(paper_ids)))
            await session.execute(delete(PaperChunk).where(PaperChunk.paper_id.in_(paper_ids)))
            await session.execute(delete(PaperSummary).where(PaperSummary.paper_id.in_(paper_ids)))
            await session.execute(delete(MindMap).where(MindMap.paper_id.in_(paper_ids)))
            await session.execute(delete(CollectionPaper).where(CollectionPaper.paper_id.in_(paper_ids)))
        
        # 2. 获取该用户的所有收藏夹ID, 删除收藏夹-论文关联
        collection_ids_stmt = select(Collection.collection_id).where(Collection.user_id == user_id)
        collection_ids_result = await session.execute(collection_ids_stmt)
        collection_ids = [row[0] for row in collection_ids_result.fetchall()]
        if collection_ids:
            await session.execute(delete(CollectionPaper).where(CollectionPaper.collection_id.in_(collection_ids)))
        
        # 3. 删除用户级资源
        await session.execute(delete(Job).where(Job.user_id == user_id))
        await session.execute(delete(Note).where(Note.user_id == user_id))
        await session.execute(delete(SearchHistory).where(SearchHistory.user_id == user_id))
        await session.execute(delete(AgentSession).where(AgentSession.user_id == user_id))
        await session.execute(delete(Collection).where(Collection.user_id == user_id))
        
        if paper_ids:
            await session.execute(delete(Paper).where(Paper.user_id == user_id))
        
        # 4. 删除用户本身
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
        return True


class PaperRepository:
    """论文相关的数据访问层"""

    @staticmethod
    async def get_paper_by_id(session: AsyncSession, paper_id: UUID) -> Optional[Paper]:
        statement = select(Paper).where(Paper.id == paper_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
        
    @staticmethod
    async def get_paper_status(session: AsyncSession, paper_id: UUID) -> Optional[Paper]:
        """
        获取论文状态 (别名 get_paper_by_id)
        """
        return await PaperRepository.get_paper_by_id(session, paper_id)

    @staticmethod
    async def create_paper(session: AsyncSession, paper: Paper) -> Paper:
        # 兼容性修复：强制转换为 offset-naive 格式以匹配数据库配置 (TIMESTAMP WITHOUT TIME ZONE)
        if paper.published_at and paper.published_at.tzinfo is not None:
            paper.published_at = paper.published_at.replace(tzinfo=None)
            
        session.add(paper)
        await session.commit()
        await session.refresh(paper)
        return paper
    
    @staticmethod
    async def update_paper(session: AsyncSession, paper: Paper) -> Paper:
        session.add(paper)
        await session.commit()
        await session.refresh(paper)
        return paper

    @staticmethod
    async def update_paper_status(
        session: AsyncSession, 
        paper_id: UUID, 
        status: PaperStatus, 
        error_message: Optional[str] = None
    ) -> Optional[Paper]:
        statement = select(Paper).where(Paper.id == paper_id)
        result = await session.execute(statement)
        paper = result.scalar_one_or_none()
        
        if paper:
            paper.analysis_status = status.value
            if error_message:
                paper.error_message = error_message
            session.add(paper)
            await session.commit()
            await session.refresh(paper)
        return paper

    @staticmethod
    async def update_paper_metadata(
        session: AsyncSession, 
        paper_id: UUID, 
        title: Optional[str] = None, 
        authors: Optional[List[str]] = None,
        toc: Optional[List] = None,
        summary: Optional[str] = None,
        full_text: Optional[str] = None,
        published_at: Optional[datetime] = None,
        source: Optional[str] = None,
        source_id: Optional[str] = None
    ) -> Optional[Paper]:
        statement = select(Paper).where(Paper.id == paper_id)
        result = await session.execute(statement)
        paper = result.scalar_one_or_none()
        
        if paper:
            if title is not None:
                paper.title = title
            if authors is not None:
                paper.authors = authors
            if toc is not None:
                # Ensure toc is a list
                if isinstance(toc, list):
                    paper.toc = toc
                else:
                    logger.warning(f"TOC format invalid (expected list, got {type(toc)}), resetting to empty list")
                    paper.toc = []
            if summary is not None:
                paper.summary = summary
            if full_text is not None:
                paper.full_text = full_text
            if published_at is not None:
                # 兼容性修复：强制转换为 offset-naive 格式
                if published_at.tzinfo is not None:
                    published_at = published_at.replace(tzinfo=None)
                paper.published_at = published_at
            if source is not None:
                paper.source = source
            if source_id is not None:
                paper.source_ref = source_id
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
        statement = select(Paper).where(Paper.user_id == user_id).order_by(Paper.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def delete_paper(session: AsyncSession, paper_id: UUID) -> bool:
        statement = select(Paper).where(Paper.id == paper_id)
        result = await session.execute(statement)
        paper = result.scalar_one_or_none()
        
        if paper:
            # 1. 解除与收藏夹的关联 (CollectionPaper)
            await session.execute(delete(CollectionPaper).where(CollectionPaper.paper_id == paper_id))
            
            # 2. 删除关联的切片 (PaperChunk)
            await session.execute(delete(PaperChunk).where(PaperChunk.paper_id == paper_id))
            
            # 3. 删除关联的摘要 (PaperSummary)
            await session.execute(delete(PaperSummary).where(PaperSummary.paper_id == paper_id))
            
            # 4. 删除关联的标注 (Annotation)
            await session.execute(delete(Annotation).where(Annotation.paper_id == paper_id))
            
            # 5. 删除关联的笔记 (Note)
            await session.execute(delete(Note).where(Note.paper_id == paper_id))
            
            # 6. 删除关联的思维导图 (MindMap)
            await session.execute(delete(MindMap).where(MindMap.paper_id == paper_id))
            
            # 7. 解除与会话的关联 (AgentSession) - 设置为NULL以保留历史
            await session.execute(update(AgentSession).where(AgentSession.paper_id == paper_id).values(paper_id=None))
            
            # 8. 解除与任务的关联 (Job) - 设置为NULL以保留记录
            await session.execute(update(Job).where(Job.paper_id == paper_id).values(paper_id=None))

            # 9. 删除论文本身
            await session.delete(paper)
            await session.commit()
            return True
        return False

    @staticmethod
    async def create_paper_chunks(session: AsyncSession, chunks: List[PaperChunk]) -> None:
        session.add_all(chunks)
        await session.commit()

    @staticmethod
    async def get_all_papers_count(session: AsyncSession) -> int:
        statement = select(func.count()).select_from(Paper)
        result = await session.execute(statement)
        return result.scalar() or 0


class CollectionRepository:
    """收藏夹相关的数据访问层"""

    @staticmethod
    async def create_collection(session: AsyncSession, collection: Collection) -> Collection:
        """创建收藏夹"""
        session.add(collection)
        await session.commit()
        await session.refresh(collection)
        return collection

    @staticmethod
    async def get_collection_by_id(session: AsyncSession, collection_id: UUID) -> Optional[Collection]:
        """根据ID获取收藏夹"""
        statement = select(Collection).where(Collection.collection_id == collection_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_collections(
        session: AsyncSession, 
        user_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Collection]:
        """获取用户的收藏夹列表"""
        statement = select(Collection).where(Collection.user_id == user_id).order_by(Collection.updated_at.desc()).limit(limit).offset(offset)
        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def get_user_collections_with_counts(
        session: AsyncSession, 
        user_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Tuple]:
        """获取用户的收藏夹列表及其论文数量"""
        statement = (
            select(Collection, func.count(CollectionPaper.paper_id))
            .outerjoin(CollectionPaper, Collection.collection_id == CollectionPaper.collection_id)
            .where(Collection.user_id == user_id)
            .group_by(Collection.collection_id)
            .order_by(Collection.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(statement)
        return result.all()

    @staticmethod
    async def get_default_collection(session: AsyncSession, user_id: UUID) -> Optional[Collection]:
        statement = select(Collection).where(
            Collection.user_id == user_id,
            Collection.is_default.is_(True),
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_collection(session: AsyncSession, collection: Collection) -> Collection:
        """更新收藏夹"""
        session.add(collection)
        await session.commit()
        await session.refresh(collection)
        return collection

    @staticmethod
    async def delete_collection(session: AsyncSession, collection: Collection) -> bool:
        """删除收藏夹"""
        await session.delete(collection)
        await session.commit()
        return True

    @staticmethod
    async def add_paper_to_collection(
        session: AsyncSession, 
        collection_id: UUID, 
        paper_id: UUID
    ) -> CollectionPaper:
        """将论文添加到收藏夹"""
        # 检查是否已存在
        statement = select(CollectionPaper).where(
            CollectionPaper.collection_id == collection_id,
            CollectionPaper.paper_id == paper_id
        )
        result = await session.execute(statement)
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
            
        link = CollectionPaper(collection_id=collection_id, paper_id=paper_id)
        session.add(link)
        await session.commit()
        await session.refresh(link)
        return link

    @staticmethod
    async def remove_paper_from_collection(
        session: AsyncSession, 
        collection_id: UUID, 
        paper_id: UUID
    ) -> bool:
        """从收藏夹移除论文"""
        statement = select(CollectionPaper).where(
            CollectionPaper.collection_id == collection_id,
            CollectionPaper.paper_id == paper_id
        )
        result = await session.execute(statement)
        link = result.scalar_one_or_none()
        
        if link:
            await session.delete(link)
            await session.commit()
            return True
        return False

    @staticmethod
    async def remove_paper_from_user_collections(
        session: AsyncSession,
        user_id: UUID,
        paper_id: UUID
    ) -> int:
        """从用户的所有收藏夹中移除指定论文"""
        # Find collection_ids for this user
        subquery = select(Collection.collection_id).where(Collection.user_id == user_id)
        
        statement = delete(CollectionPaper).where(
            CollectionPaper.paper_id == paper_id,
            CollectionPaper.collection_id.in_(subquery)
        )
        result = await session.execute(statement)
        await session.commit()
        return result.rowcount

    @staticmethod
    async def get_collection_papers(
        session: AsyncSession, 
        collection_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[Paper]:
        """获取收藏夹内的论文列表"""
        # 使用 join 查询
        statement = (
            select(Paper)
            .join(CollectionPaper, Paper.id == CollectionPaper.paper_id)
            .where(CollectionPaper.collection_id == collection_id)
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(statement)
        return result.scalars().all()


class ReaderRepository:
    """阅读器相关的数据访问层"""

    @staticmethod
    async def get_annotations_by_paper(session: AsyncSession, paper_id: UUID, user_id: Optional[UUID] = None) -> List[Annotation]:
        statement = (
            select(Annotation)
            .where(Annotation.paper_id == paper_id)
        )
        if user_id is not None:
            # Check paper ownership or annotation ownership if needed. 
            # Usually annotations are tied to paper, and paper is tied to user.
            # But here we join Paper to check user_id if we want strict check.
            # Or just assume caller checked paper access.
            # Given previous implementation, let's join Paper to be safe.
            statement = statement.join(Paper).where(Paper.user_id == user_id)
            
        statement = statement.order_by(Annotation.created_at)
        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def get_notes_by_paper(session: AsyncSession, paper_id: UUID, user_id: UUID) -> List[Note]:
        statement = (
            select(Note)
            .where(Note.paper_id == paper_id, Note.user_id == user_id)
            .order_by(Note.created_at)
        )
        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def get_note_detail(session: AsyncSession, paper_id: UUID, note_id: UUID, user_id: UUID) -> Optional[Note]:
        statement = select(Note).where(
            Note.id == note_id,
            Note.paper_id == paper_id,
            Note.user_id == user_id
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_note_by_id(session: AsyncSession, note_id: UUID, user_id: UUID) -> Optional[Note]:
        statement = select(Note).where(Note.id == note_id, Note.user_id == user_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_summaries_by_paper(session: AsyncSession, paper_id: UUID, user_id: UUID) -> List[PaperSummary]:
        statement = (
            select(PaperSummary)
            .join(Paper)
            .where(PaperSummary.paper_id == paper_id, Paper.user_id == user_id)
        )
        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def get_summary_by_type(session: AsyncSession, paper_id: UUID, summary_type: str) -> Optional[PaperSummary]:
        statement = select(PaperSummary).where(
            PaperSummary.paper_id == paper_id,
            PaperSummary.summary_type == summary_type
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_mind_map_by_paper(session: AsyncSession, paper_id: UUID, user_id: UUID) -> Optional[MindMap]:
        statement = select(MindMap).join(Paper).where(
            MindMap.paper_id == paper_id,
            Paper.user_id == user_id
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_history_by_paper(session: AsyncSession, paper_id: UUID, user_id: UUID) -> List[AgentSession]:
        statement = (
            select(AgentSession)
            .where(AgentSession.paper_id == paper_id, AgentSession.user_id == user_id)
            .order_by(AgentSession.created_at)
        )
        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def get_session_detail(session: AsyncSession, paper_id: UUID, record_id: UUID, user_id: UUID) -> Optional[AgentSession]:
        statement = select(AgentSession).where(
            AgentSession.id == record_id,
            AgentSession.paper_id == paper_id,
            AgentSession.user_id == user_id
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
        
    @staticmethod
    async def create_annotation(session: AsyncSession, annotation: Annotation) -> Annotation:
        """创建标注"""
        session.add(annotation)
        await session.commit()
        await session.refresh(annotation)
        return annotation

    @staticmethod
    async def get_annotation_by_id(session: AsyncSession, annotation_id: UUID) -> Optional[Annotation]:
        """根据ID获取标注"""
        statement = select(Annotation).where(Annotation.id == annotation_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_annotation(session: AsyncSession, annotation: Annotation) -> Annotation:
        """更新标注"""
        session.add(annotation)
        await session.commit()
        await session.refresh(annotation)
        return annotation

    @staticmethod
    async def delete_annotation(session: AsyncSession, annotation: Annotation) -> bool:
        """删除标注"""
        await session.delete(annotation)
        await session.commit()
        return True


class JobRepository:
    """任务相关的数据访问层"""

    @staticmethod
    async def get_job_by_id(session: AsyncSession, job_id: UUID) -> Optional[Job]:
        statement = select(Job).where(Job.id == job_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_job_status(
        session: AsyncSession,
        job_id: UUID,
        status: str,
        stage: Optional[str] = None,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        end_at: Optional[datetime] = None
    ) -> Optional[Job]:
        statement = select(Job).where(Job.id == job_id)
        res = await session.execute(statement)
        job = res.scalar_one_or_none()

        if job:
            job.status = status
            if stage is not None:
                job.stage = stage
            if progress is not None:
                job.progress = progress
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            if end_at is not None:
                job.end_at = end_at
            
            session.add(job)
            await session.commit()
            await session.refresh(job)
        return job

    @staticmethod
    async def get_latest_job_by_paper_id(session: AsyncSession, paper_id: UUID) -> Optional[Job]:
        statement = select(Job).where(Job.paper_id == paper_id).order_by(Job.created_at.desc()).limit(1)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_primary_job_by_paper_id(session: AsyncSession, paper_id: UUID) -> Optional[Job]:
        """
        获取与论文状态最为相关的核心任务 (process_pdf 或 vectorize)
        优先级: 正在运行的任务 > 最新完成的任务
        """
        # 1. 优先查正在运行/排队的核心任务
        stmt = select(Job).where(
            Job.paper_id == paper_id,
            Job.type.in_(["process_pdf", "vectorize"]),
            Job.status.in_(["running", "queued", "pending"])
        ).order_by(Job.created_at.desc()).limit(1)
        res = await session.execute(stmt)
        active_job = res.scalar_one_or_none()
        if active_job:
            return active_job
            
        # 2. 如果没有运行中的，查最新的核心任务
        stmt = select(Job).where(
            Job.paper_id == paper_id,
            Job.type.in_(["process_pdf", "vectorize"])
        ).order_by(Job.created_at.desc()).limit(1)
        res = await session.execute(stmt)
        primary_job = res.scalar_one_or_none()
        if primary_job:
            return primary_job
            
        # 3. 如果连核心任务都没有，退回到绝对最新的任务 (如 summary, mind_map)
        return await JobRepository.get_latest_job_by_paper_id(session, paper_id)

    @staticmethod
    async def reset_interrupted_jobs(session: AsyncSession) -> None:
        """重置意外中断的任务"""
        # 将所有 running 状态的任务重置为 failed (或 queued)
        # 这里选择标记为 failed，因为 Arq 任务队列在重启后丢失，无法继续执行
        # 用户需要在前端手动重试
        statement = (
            update(Job)
            .where(Job.status == "running")
            .values(
                status="failed",
                error="System restarted, task interrupted.",
                end_at=datetime.now()
            )
        )
        await session.execute(statement)
        await session.commit()

    @staticmethod
    async def get_active_jobs_count(session: AsyncSession) -> int:
        """获取正在进行的任务数量"""
        statement = select(func.count()).select_from(Job).where(Job.status.in_(["running", "queued", "pending", "processing"]))
        result = await session.execute(statement)
        return result.scalar() or 0


class SearchApiConfigRepository:
    """全局搜索源配置相关的数据访问层"""

    @staticmethod
    async def get_all_configs(session: AsyncSession) -> List[SearchApiConfig]:
        statement = select(SearchApiConfig).order_by(SearchApiConfig.weight.desc())
        result = await session.execute(statement)
        return list(result.scalars().all())

    @staticmethod
    async def get_active_configs(session: AsyncSession) -> List[SearchApiConfig]:
        statement = select(SearchApiConfig).where(SearchApiConfig.is_active == True).order_by(SearchApiConfig.weight.desc())
        result = await session.execute(statement)
        return list(result.scalars().all())

    @staticmethod
    async def get_config_by_name(session: AsyncSession, api_name: str) -> Optional[SearchApiConfig]:
        statement = select(SearchApiConfig).where(SearchApiConfig.api_name == api_name)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert_config(session: AsyncSession, config_data: Dict[str, Any]) -> SearchApiConfig:
        api_name = config_data.get("api_name")
        statement = select(SearchApiConfig).where(SearchApiConfig.api_name == api_name)
        result = await session.execute(statement)
        config = result.scalar_one_or_none()

        if config:
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            config.updated_at = datetime.now()
        else:
            config = SearchApiConfig(**config_data)
            session.add(config)
        
        await session.commit()
        await session.refresh(config)
        return config

    @staticmethod
    async def delete_config(session: AsyncSession, api_name: str) -> bool:
        statement = delete(SearchApiConfig).where(SearchApiConfig.api_name == api_name)
        await session.execute(statement)
        await session.commit()
        return True


class SystemModelConfigRepository:
    """系统模型配置仓储层"""
    
    @staticmethod
    async def get_all_configs(session: AsyncSession) -> list[SystemModelConfig]:
        stmt = select(SystemModelConfig).order_by(SystemModelConfig.type)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_config_by_type(session: AsyncSession, config_type: str) -> Optional[SystemModelConfig]:
        stmt = select(SystemModelConfig).where(SystemModelConfig.type == config_type)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_config(session: AsyncSession, config_id: UUID, data: dict) -> Optional[SystemModelConfig]:
        stmt = select(SystemModelConfig).where(SystemModelConfig.id == config_id)
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()
        if config:
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            config.updated_at = datetime.now()
            await session.commit()
            await session.refresh(config)
        return config

    @staticmethod
    async def create_config(session: AsyncSession, config: SystemModelConfig) -> SystemModelConfig:
        session.add(config)
        await session.commit()
        await session.refresh(config)
        return config

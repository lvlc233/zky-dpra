from uuid import UUID
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from base.pg.entity import MindMap as MindMapEntity
from base.pg.service import ReaderRepository
from service.reader.schema import MindMapCreateDTO, MindMapUpdateDTO, MindMapDTO, MindMap, MindMapNode, MindMapEdge


class MindMapService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_mind_map_data(self, paper_id: UUID, user_id: UUID) -> Optional[MindMap]:
        mm = await self.get_mind_map_by_paper(paper_id, user_id)
        
        if mm and mm.graph_data:
            gd = mm.graph_data
            nodes = [MindMapNode(**n) for n in gd.get("nodes", [])]
            edges = [MindMapEdge(**e) for e in gd.get("edges", [])]
            return MindMap(nodes=nodes, edges=edges)

        # --- Auto-Trigger Logic ---
        from base.pg.entity import Job
        from sqlalchemy import select
        from loguru import logger
        
        # Check active jobs
        stmt = select(Job).where(
            Job.paper_id == paper_id,
            Job.type == "mind_map",
            Job.status.in_(["queued", "running"])
        )
        result = await self.session.execute(stmt)
        active_job = result.scalar_one_or_none()
        
        if not active_job:
            # No active job, trigger one
            try:
                from service.reader.job_service import JobService
                from controller.api.reader.schema import JobCreateRequest
                
                logger.info(f"Auto-triggering mind_map job for paper {paper_id}")
                job_service = JobService(self.session)
                # Create job
                await job_service.create_job(paper_id, JobCreateRequest(job_type="mind_map"), user_id)
                return MindMap(nodes=[], edges=[], system_notification="正在自动触发脑图生成任务，请稍候刷新...")
            except Exception as e:
                logger.error(f"Failed to auto-trigger mind_map job: {e}")
                return MindMap(nodes=[], edges=[])
        else:
             return MindMap(nodes=[], edges=[], system_notification="脑图任务正在生成中，请稍后...")

    async def get_mind_map_by_paper(self, paper_id: UUID, user_id: UUID) -> Optional[MindMapEntity]:
        """获取论文的思维导图"""
        return await ReaderRepository.get_mind_map_by_paper(self.session, paper_id, user_id)

    async def get_or_create_mind_map(self, paper_id: UUID, user_id: UUID, map_in: Optional[MindMapCreateDTO] = None) -> MindMapDTO:
        """获取或创建思维导图"""
        mind_map = await self.get_mind_map_by_paper(paper_id, user_id)
        if mind_map:
            return MindMapDTO.model_validate(mind_map)

        # 创建新的空导图或使用传入的数据
        initial_data = {}
        if map_in and map_in.graph_data:
            initial_data = map_in.graph_data.model_dump()
        else:
            initial_data = {"nodes": [], "edges": []}

        mind_map = MindMapEntity(
            paper_id=paper_id,
            user_id=user_id,
            graph_data=initial_data
        )
        self.session.add(mind_map)
        await self.session.commit()
        await self.session.refresh(mind_map)
        return MindMapDTO.model_validate(mind_map)

    async def update_mind_map(self, paper_id: UUID, user_id: UUID, map_in: MindMapUpdateDTO) -> Optional[MindMapDTO]:
        """更新思维导图数据"""
        mind_map = await self.get_mind_map_by_paper(paper_id, user_id)
        if not mind_map:
            return None
        
        mind_map.graph_data = map_in.graph_data.model_dump()
        mind_map.updated_at = datetime.now()
        
        self.session.add(mind_map)
        await self.session.commit()
        await self.session.refresh(mind_map)
        return MindMapDTO.model_validate(mind_map)

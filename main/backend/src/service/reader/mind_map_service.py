from uuid import UUID
from typing import Optional
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from base.pg.entity import MindMap
from service.reader.schema import MindMapCreate, MindMapUpdate, GraphData

class MindMapService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_mind_map_by_paper(self, paper_id: UUID, user_id: UUID) -> Optional[MindMap]:
        """获取论文的思维导图"""
        stmt = select(MindMap).where(MindMap.paper_id == paper_id, MindMap.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_mind_map(self, paper_id: UUID, user_id: UUID, map_in: Optional[MindMapCreate] = None) -> MindMap:
        """获取或创建思维导图"""
        mind_map = await self.get_mind_map_by_paper(paper_id, user_id)
        if mind_map:
            return mind_map

        # 创建新的空导图或使用传入的数据
        initial_data = {}
        if map_in and map_in.graph_data:
            initial_data = map_in.graph_data.model_dump()
        else:
            initial_data = {"nodes": [], "edges": []}

        mind_map = MindMap(
            paper_id=paper_id,
            user_id=user_id,
            graph_data=initial_data
        )
        self.session.add(mind_map)
        await self.session.commit()
        await self.session.refresh(mind_map)
        return mind_map

    async def update_mind_map(self, paper_id: UUID, user_id: UUID, map_in: MindMapUpdate) -> Optional[MindMap]:
        """更新思维导图数据"""
        mind_map = await self.get_mind_map_by_paper(paper_id, user_id)
        if not mind_map:
            return None
        
        mind_map.graph_data = map_in.graph_data.model_dump()
        mind_map.updated_at = datetime.now()
        
        self.session.add(mind_map)
        await self.session.commit()
        await self.session.refresh(mind_map)
        return mind_map

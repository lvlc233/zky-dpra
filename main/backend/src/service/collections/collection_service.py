
from typing import List, Optional, Annotated
from uuid import UUID
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from base.pg.service import CollectionRepository, PaperRepository, SessionDep
from base.pg.entity import Collection, Paper
from controller.api.collections.schema import (
    CollectionCreate, 
    CollectionUpdate, 
    CollectionResponse, 
    CollectionDetailResponse
)
from service.papers.schema import PaperDTO


class CollectionService:
    """
    收藏夹服务层
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    def _collection_to_response(self, collection: Collection) -> CollectionResponse:
        """实体转响应模型"""
        return CollectionResponse.model_validate(collection)

    def _paper_to_dto(self, paper: Paper) -> PaperDTO:
        """Paper实体转DTO"""
        # 注意: 这里的转换逻辑应与PaperService保持一致
        return PaperDTO(
            id=paper.id,
            user_id=paper.user_id,
            title=paper.title,
            authors=paper.authors,
            abstract=paper.abstract,
            file_key=paper.file_key,
            file_url=paper.file_url,
            status=paper.status,
            error_message=paper.error_message,
            created_at=paper.created_at
        )

    async def create_collection(self, user_id: UUID, data: CollectionCreate) -> CollectionResponse:
        """创建收藏夹"""
        collection = Collection(
            user_id=user_id,
            name=data.name,
            description=data.description
        )
        created = await CollectionRepository.create_collection(self.session, collection)
        return self._collection_to_response(created)

    async def get_user_collections(
        self, 
        user_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[CollectionResponse]:
        """获取用户收藏夹列表"""
        collections = await CollectionRepository.get_user_collections(
            self.session, user_id, limit, offset
        )
        return [self._collection_to_response(c) for c in collections]

    async def get_collection_detail(self, collection_id: UUID, user_id: UUID) -> Optional[CollectionDetailResponse]:
        """获取收藏夹详情（包含论文列表）"""
        collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
        if not collection or collection.user_id != user_id:
            return None
        
        # 获取关联的论文
        papers = await CollectionRepository.get_collection_papers(self.session, collection_id)
        
        response = CollectionDetailResponse.model_validate(collection)
        response.papers = [self._paper_to_dto(p) for p in papers]
        return response

    async def update_collection(
        self, 
        collection_id: UUID, 
        user_id: UUID, 
        data: CollectionUpdate
    ) -> Optional[CollectionResponse]:
        """更新收藏夹"""
        collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
        if not collection or collection.user_id != user_id:
            return None

        if data.name is not None:
            collection.name = data.name
        if data.description is not None:
            collection.description = data.description
        
        collection.updated_at = datetime.now()
        updated = await CollectionRepository.update_collection(self.session, collection)
        return self._collection_to_response(updated)

    async def delete_collection(self, collection_id: UUID, user_id: UUID) -> bool:
        """删除收藏夹"""
        collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
        if not collection or collection.user_id != user_id:
            return False
        
        return await CollectionRepository.delete_collection(self.session, collection)

    async def add_paper_to_collection(
        self, 
        collection_id: UUID, 
        paper_id: UUID, 
        user_id: UUID
    ) -> bool:
        """添加论文到收藏夹"""
        # 1. 检查收藏夹是否存在且属于该用户
        collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
        if not collection or collection.user_id != user_id:
            return False
            
        # 2. 检查论文是否存在
        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        if not paper:
            return False
            
        # 3. 添加关联
        await CollectionRepository.add_paper_to_collection(self.session, collection_id, paper_id)
        return True

    async def remove_paper_from_collection(
        self, 
        collection_id: UUID, 
        paper_id: UUID, 
        user_id: UUID
    ) -> bool:
        """从收藏夹移除论文"""
        # 1. 检查收藏夹权限
        collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
        if not collection or collection.user_id != user_id:
            return False
            
        return await CollectionRepository.remove_paper_from_collection(self.session, collection_id, paper_id)


def get_collection_service(session: SessionDep) -> CollectionService:
    """依赖注入工厂"""
    return CollectionService(session)

CollectionServiceDep = Annotated[CollectionService, Depends(get_collection_service)]

'''
开发者: BackendAgent
当前版本: v1.0
创建时间: 2026年01月14日
'''
from typing import List, Optional, Annotated
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from base.pg.service import SessionDep, ReaderRepository
from base.pg.entity import Layer, Annotation
from service.reader.schema import (
    LayerCreate, LayerResponse, LayerListResponse, LayerUpdate,
    AnnotationCreate, AnnotationResponse, AnnotationUpdate
)

class ReaderService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_layers_by_paper(self, paper_id: UUID) -> LayerListResponse:
        layers = await ReaderRepository.get_layers_by_paper(self.session, paper_id)
        # Ensure conversion to Pydantic models works
        # layers is List[Layer Entity]
        # LayerListResponse expects List[LayerResponse]
        return LayerListResponse(layers=[LayerResponse.model_validate(l) for l in layers])

    async def create_layer(self, paper_id: UUID, user_id: UUID, data: LayerCreate) -> LayerResponse:
        layer = Layer(
            paper_id=paper_id,
            user_id=user_id,
            name=data.name,
            type=data.type,
            visible=data.visible
        )
        created = await ReaderRepository.create_layer(self.session, layer)
        return LayerResponse.model_validate(created)

    async def update_layer(self, layer_id: UUID, data: LayerUpdate) -> Optional[LayerResponse]:
        layer = await ReaderRepository.get_layer_by_id(self.session, layer_id)
        if not layer:
            return None
        
        if data.name is not None:
            layer.name = data.name
        if data.visible is not None:
            layer.visible = data.visible
            
        updated = await ReaderRepository.update_layer(self.session, layer)
        return LayerResponse.model_validate(updated)

    async def delete_layer(self, layer_id: UUID) -> bool:
        layer = await ReaderRepository.get_layer_by_id(self.session, layer_id)
        if not layer:
            return False
        return await ReaderRepository.delete_layer(self.session, layer)

    async def create_annotation(self, layer_id: UUID, data: AnnotationCreate) -> AnnotationResponse:
        # Verify layer exists? (Optional, FK constraint handles it, but better for error msg)
        # Assuming FK constraint will raise error if layer_id invalid.
        
        anno = Annotation(
            layer_id=layer_id,
            type=data.type,
            rects=data.rects,
            content=data.content,
            color=data.color
        )
        created = await ReaderRepository.create_annotation(self.session, anno)
        return AnnotationResponse.model_validate(created)

    async def update_annotation(self, anno_id: UUID, data: AnnotationUpdate) -> Optional[AnnotationResponse]:
        anno = await ReaderRepository.get_annotation_by_id(self.session, anno_id)
        if not anno:
            return None
        
        if data.content is not None:
            anno.content = data.content
        if data.color is not None:
            anno.color = data.color
            
        updated = await ReaderRepository.update_annotation(self.session, anno)
        return AnnotationResponse.model_validate(updated)

    async def delete_annotation(self, anno_id: UUID) -> bool:
        anno = await ReaderRepository.get_annotation_by_id(self.session, anno_id)
        if not anno:
            return False
        return await ReaderRepository.delete_annotation(self.session, anno)


def get_reader_service(session: SessionDep) -> ReaderService:
    return ReaderService(session)


ReaderServiceDep = Annotated[ReaderService, Depends(get_reader_service)]


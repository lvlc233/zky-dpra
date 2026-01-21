from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from base.pg.service import ReaderRepository
from service.reader.schema import View, Annotation, Rect

class ViewService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_views(self, paper_id: UUID, user_id: UUID) -> List[View]:
        layers = await ReaderRepository.get_layers_by_paper(self.session, paper_id, user_id)
        
        views = []
        for layer in layers:
            annotations = []
            for ann in layer.annotations:
                # Parse rects (List[dict] -> List[Rect])
                rects_list = []
                if ann.rects:
                    for r in ann.rects:
                        try:
                            rects_list.append(Rect(**r))
                        except:
                            pass
                
                annotations.append(Annotation(
                    id=ann.id,
                    type=ann.type,
                    rect=rects_list,
                    content=ann.content,
                    color=ann.color
                ))
            
            views.append(View(
                id=layer.id,
                name=layer.name,
                visible=layer.visible,
                annotations=annotations
            ))
            
        return views

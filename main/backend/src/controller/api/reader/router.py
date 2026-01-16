from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from service.reader.summary_service import SummaryService
from service.reader.note_service import NoteService
from service.reader.mind_map_service import MindMapService
from service.reader.reader_service import ReaderService
from service.reader.schema import (
    LayerCreate, LayerResponse, LayerListResponse, LayerUpdate,
    AnnotationCreate, AnnotationResponse, AnnotationUpdate,
    SummaryCreate, SummaryResponse,
    NoteCreate, NoteResponse, NoteUpdate,
    MindMapCreate, MindMapUpdate, MindMapResponse
)
from base.pg.service import SessionDep
from controller.api.auth.router import get_current_user
from base.pg.entity import User
from controller.response import Response

router = APIRouter(prefix="/reader", tags=["reader"])

@router.post("/papers/{paper_id}/summary", response_model=Response[SummaryResponse])
async def generate_summary(
    paper_id: UUID,
    summary_in: SummaryCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """生成或获取论文摘要"""
    summary_service = SummaryService(session)
    summary = await summary_service.get_or_create_summary(paper_id, summary_in)
    return Response.success(data=summary)

# --- Layers ---

@router.get("/papers/{paper_id}/layers", response_model=Response[LayerListResponse])
async def get_paper_layers(
    paper_id: UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文的所有图层"""
    service = ReaderService(session)
    layers = await service.get_layers_by_paper(paper_id)
    return Response.success(data=layers)

@router.post("/papers/{paper_id}/layers", response_model=Response[LayerResponse])
async def create_layer(
    paper_id: UUID,
    layer_in: LayerCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """创建新图层"""
    service = ReaderService(session)
    layer = await service.create_layer(paper_id, current_user.id, layer_in)
    return Response.success(data=layer)

@router.put("/layers/{layer_id}", response_model=Response[LayerResponse])
async def update_layer(
    layer_id: UUID,
    layer_in: LayerUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """更新图层"""
    service = ReaderService(session)
    updated = await service.update_layer(layer_id, layer_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Layer not found")
    return Response.success(data=updated)

@router.delete("/layers/{layer_id}")
async def delete_layer(
    layer_id: UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """删除图层"""
    service = ReaderService(session)
    success = await service.delete_layer(layer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Layer not found")
    return Response.success(message="Layer deleted successfully")

# --- Annotations ---

@router.post("/layers/{layer_id}/annotations", response_model=Response[AnnotationResponse])
async def create_annotation(
    layer_id: UUID,
    anno_in: AnnotationCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """添加标注"""
    # 这里可以添加额外的权限检查，确保 layer 属于当前用户或可见
    service = ReaderService(session)
    annotation = await service.create_annotation(layer_id, anno_in)
    return Response.success(data=annotation)

@router.put("/annotations/{anno_id}", response_model=Response[AnnotationResponse])
async def update_annotation(
    anno_id: UUID,
    anno_in: AnnotationUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """更新标注"""
    service = ReaderService(session)
    updated = await service.update_annotation(anno_id, anno_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return Response.success(data=updated)

@router.delete("/annotations/{anno_id}")
async def delete_annotation(
    anno_id: UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """删除标注"""
    service = ReaderService(session)
    success = await service.delete_annotation(anno_id)
    if not success:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return Response.success(msg="Annotation deleted successfully")

# --- Notes ---

@router.get("/papers/{paper_id}/notes", response_model=Response[list[NoteResponse]])
async def get_paper_notes(
    paper_id: UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文的笔记列表"""
    note_service = NoteService(session)
    notes = await note_service.get_notes_by_paper(paper_id, current_user.id)
    return Response.success(data=notes)

@router.post("/papers/{paper_id}/notes", response_model=Response[NoteResponse])
async def create_note(
    paper_id: UUID,
    note_in: NoteCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """创建新笔记"""
    note_service = NoteService(session)
    note = await note_service.create_note(paper_id, current_user.id, note_in)
    return Response.success(data=note)

@router.put("/notes/{note_id}", response_model=Response[NoteResponse])
async def update_note(
    note_id: UUID,
    note_in: NoteUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """更新笔记"""
    note_service = NoteService(session)
    updated = await note_service.update_note(note_id, current_user.id, note_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Note not found")
    return Response.success(data=updated)

@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """删除笔记"""
    note_service = NoteService(session)
    success = await note_service.delete_note(note_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return Response.success(message="Note deleted successfully")

# --- Mind Maps ---

@router.get("/papers/{paper_id}/graph", response_model=Response[MindMapResponse])
async def get_paper_mind_map(
    paper_id: UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """获取论文的思维导图"""
    mm_service = MindMapService(session)
    # 获取或创建空导图
    mm = await mm_service.get_or_create_mind_map(paper_id, current_user.id)
    return Response.success(data=mm)

@router.put("/papers/{paper_id}/graph", response_model=Response[MindMapResponse])
async def update_paper_mind_map(
    paper_id: UUID,
    map_in: MindMapUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """更新论文的思维导图"""
    mm_service = MindMapService(session)
    updated = await mm_service.update_mind_map(paper_id, current_user.id, map_in)
    if not updated:
        # 理论上 get_or_create 保证了存在，但为了安全
        updated = await mm_service.get_or_create_mind_map(paper_id, current_user.id, MindMapCreate(graph_data=map_in.graph_data))
    return Response.success(data=updated)

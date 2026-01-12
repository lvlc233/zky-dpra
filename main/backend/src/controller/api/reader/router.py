from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from controller.api.reader.schema import (
    LayerCreate, LayerResponse, LayerListResponse,
    AnnotationCreate, AnnotationResponse, AnnotationUpdate
)
# from controller.api.auth.router import get_current_user # 需要解决循环导入或重构依赖

# 临时 Mock 依赖
def get_current_user_id():
    return UUID("12345678-1234-5678-1234-567812345678")

router = APIRouter(tags=["reader"])

# --- Layers ---

@router.get("/papers/{paper_id}/layers", response_model=LayerListResponse)
async def get_paper_layers(
    paper_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Implement DB query
    return {"layers": []}

@router.post("/papers/{paper_id}/layers", response_model=LayerResponse)
async def create_layer(
    paper_id: UUID,
    layer_in: LayerCreate,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Implement DB create
    return {
        "id": uuid4(),
        "paper_id": paper_id,
        "user_id": user_id,
        "name": layer_in.name,
        "type": layer_in.type,
        "visible": layer_in.visible,
        "created_at": datetime.utcnow(),
        "annotations": []
    }

# --- Annotations ---

@router.post("/layers/{layer_id}/annotations", response_model=AnnotationResponse)
async def create_annotation(
    layer_id: UUID,
    anno_in: AnnotationCreate,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Implement DB create
    return {
        "id": uuid4(),
        "layer_id": layer_id,
        **anno_in.model_dump(),
        "created_at": datetime.utcnow()
    }

@router.put("/annotations/{anno_id}", response_model=AnnotationResponse)
async def update_annotation(
    anno_id: UUID,
    anno_in: AnnotationUpdate,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Implement DB update
    return {
        "id": anno_id,
        "layer_id": uuid4(), # Mock
        "type": "highlight",
        "rects": [],
        "content": anno_in.content,
        "color": anno_in.color,
        "created_at": datetime.utcnow()
    }

@router.delete("/annotations/{anno_id}")
async def delete_annotation(
    anno_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Implement DB delete
    return {"success": True}

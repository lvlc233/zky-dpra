
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from controller.api.collections.schema import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    CollectionDetailResponse,
    AddPaperRequest
)
from service.collections.collection_service import CollectionServiceDep
from controller.api.auth.router import get_current_user
from base.pg.entity import User

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    data: CollectionCreate,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """创建收藏夹"""
    return await service.create_collection(current_user.id, data)


@router.get("", response_model=List[CollectionResponse])
async def get_collections(
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    """获取我的收藏夹列表"""
    return await service.get_user_collections(current_user.id, limit, offset)


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection_detail(
    collection_id: UUID,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """获取收藏夹详情"""
    collection = await service.get_collection_detail(collection_id, current_user.id)
    if not collection:
        raise HTTPException(status_code=404, detail="收藏夹不存在或无权访问")
    return collection


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: UUID,
    data: CollectionUpdate,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """更新收藏夹信息"""
    collection = await service.update_collection(collection_id, current_user.id, data)
    if not collection:
        raise HTTPException(status_code=404, detail="收藏夹不存在或无权访问")
    return collection

@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: UUID,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """删除收藏夹"""
    success = await service.delete_collection(collection_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="收藏夹不存在或无权访问")


@router.post("/{collection_id}/papers", status_code=status.HTTP_201_CREATED)
async def add_paper_to_collection(
    collection_id: UUID,
    data: AddPaperRequest,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """添加论文到收藏夹"""
    success = await service.add_paper_to_collection(collection_id, data.paper_id, current_user.id)
    if not success:
        # 这里可能是收藏夹不存在，或者论文不存在。简单起见返回400或404
        raise HTTPException(status_code=400, detail="操作失败：收藏夹不存在、无权访问或论文不存在")
    return {"message": "添加成功"}


@router.delete("/{collection_id}/papers/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_paper_from_collection(
    collection_id: UUID,
    paper_id: UUID,
    service: CollectionServiceDep,
    current_user: User = Depends(get_current_user)
):
    """从收藏夹移除论文"""
    success = await service.remove_paper_from_collection(collection_id, paper_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="移除失败：关联不存在或无权访问")

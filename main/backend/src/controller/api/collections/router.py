
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header

from controller.api.collections.schema import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    CollectionDetailResponse,
    AddPaperRequest
)
from service.collections.collection_service import CollectionServiceDep

router = APIRouter(prefix="/collections", tags=["collections"])


def get_current_user_id(x_user_id: str | None = Header(default=None)) -> UUID:
    """获取当前用户ID (Mock)"""
    if not x_user_id:
        return UUID("12345678-1234-5678-1234-567812345678")
    return UUID(x_user_id)


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    data: CollectionCreate,
    service: CollectionServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """创建收藏夹"""
    return await service.create_collection(user_id, data)

# TODO: 这里可能需要后续提取到搜索的设置中,暂时先这样子也没问题。
@router.get("", response_model=List[CollectionResponse])
async def get_collections(
    service: CollectionServiceDep,
    user_id: UUID = Depends(get_current_user_id),
    limit: int = 100,
    offset: int = 0
):
    """获取我的收藏夹列表"""
    return await service.get_user_collections(user_id, limit, offset)


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection_detail(
    collection_id: UUID,
    service: CollectionServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """获取收藏夹详情"""
    collection = await service.get_collection_detail(collection_id, user_id)
    if not collection:
        raise HTTPException(status_code=404, detail="收藏夹不存在或无权访问")
    return collection


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: UUID,
    data: CollectionUpdate,
    service: CollectionServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """更新收藏夹信息"""
    collection = await service.update_collection(collection_id, user_id, data)
    if not collection:
        raise HTTPException(status_code=404, detail="收藏夹不存在或无权访问")
    return collection

# TODO: 可能需要提炼删除收藏夹的请求模型。
@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: UUID,
    service: CollectionServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """删除收藏夹"""
    success = await service.delete_collection(collection_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="收藏夹不存在或无权访问")


@router.post("/{collection_id}/papers", status_code=status.HTTP_201_CREATED)
async def add_paper_to_collection(
    collection_id: UUID,
    data: AddPaperRequest,
    service: CollectionServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """添加论文到收藏夹"""
    success = await service.add_paper_to_collection(collection_id, data.paper_id, user_id)
    if not success:
        # 这里可能是收藏夹不存在，或者论文不存在。简单起见返回400或404
        raise HTTPException(status_code=400, detail="操作失败：收藏夹不存在、无权访问或论文不存在")
    return {"message": "添加成功"}


@router.delete("/{collection_id}/papers/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_paper_from_collection(
    collection_id: UUID,
    paper_id: UUID,
    service: CollectionServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """从收藏夹移除论文"""
    success = await service.remove_paper_from_collection(collection_id, paper_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="移除失败：关联不存在或无权访问")

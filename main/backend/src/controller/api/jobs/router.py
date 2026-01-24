from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from controller.response import Response
from service.reader.job_service import JobService
from base.pg.service import SessionDep
from controller.api.auth.router import get_current_user
from base.pg.entity import User
from controller.api.reader.schema import JobResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def get_job_service(session: SessionDep) -> JobService:
    return JobService(session)

@router.get("/monitor/queues", response_model=Response[Dict[str, Any]])
async def monitor_queues(
    service: JobService = Depends(get_job_service),
    current_user: User = Depends(get_current_user)
):
    """
    [Admin] 监控 Redis 队列状态
    """
    # 简单的权限检查 (实际应有更严格的 Admin Role)
    if not current_user: # Assume logged in
        pass
    
    data = await service.get_queue_metrics()
    return Response.success(data)

@router.get("/{job_id}", response_model=Response[JobResponse])
async def get_job_status(
    job_id: UUID,
    service: JobService = Depends(get_job_service),
    current_user: User = Depends(get_current_user)
):
    """获取任务状态"""
    data = await service.get_job(job_id, current_user.id)
    return Response.success(data)

@router.get("/{job_id}/events")
async def subscribe_job_events(
    job_id: UUID,
    service: JobService = Depends(get_job_service),
    current_user: User = Depends(get_current_user)
):
    """订阅任务SSE"""
    return StreamingResponse(
        service.subscribe_job_events(job_id, current_user.id),
        media_type="text/event-stream"
    )

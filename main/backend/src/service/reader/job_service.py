import asyncio
import json
import hashlib
from datetime import datetime
from typing import List, AsyncGenerator, Optional, Any, Dict
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
import redis.asyncio as redis

from base.pg.entity import Job, Paper
from base.config import settings
from worker.tasks import task_queue
from service.reader.schema import Job as JobDTO, JobResult
from controller.api.reader.schema import JobCreateRequest, JobResponse, SSEDataEnvelope, JobEventPayload


class JobService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_jobs(self, paper_id: UUID, user_id: UUID) -> List[JobDTO]:
        # Job does not have user_id, join Paper
        stmt = (
            select(Job)
            .join(Paper)
            .where(Job.paper_id == paper_id, Paper.user_id == user_id)
            .order_by(Job.created_at.desc())
        )
        result = await self.session.execute(stmt)
        jobs = result.scalars().all()
        
        items = [
            JobDTO(
                id=j.id,
                job_type=j.type,
                status=j.status,
                progress=float(j.progress) if j.progress is not None else 0.0,
                stage=j.stage,
                error_message=j.error,
                created_at=j.created_at,
                completed_at=j.end_at,
                result=j.result # Assuming result is stored as JSON and compatible with JobResult
            ) for j in jobs
        ]
        return items

    async def create_job(self, paper_id: UUID, req: JobCreateRequest, user_id: UUID) -> JobResponse:
        # Check paper permission
        stmt = select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
        result = await self.session.execute(stmt)
        paper = result.scalar_one_or_none()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Calculate params_hash
        params_str = json.dumps(req.params, sort_keys=True) if req.params else ""
        params_hash = hashlib.md5(params_str.encode()).hexdigest()

        # Create Job
        new_job = Job(
            id=uuid4(),
            user_id=user_id,
            paper_id=paper_id,
            type=req.job_type,
            status="queued",
            progress=0,
            params_hash=params_hash,
            created_at=datetime.now()
        )
        self.session.add(new_job)
        await self.session.commit()
        await self.session.refresh(new_job)
        
        # Trigger background task
        try:
            if req.job_type == "parse_text":
                await task_queue.enqueue_parse_text(str(paper_id), str(new_job.id))
            elif req.job_type == "vectorize":
                await task_queue.enqueue_vectorize(str(paper_id), str(new_job.id))
            elif req.job_type == "summary":
                await task_queue.enqueue_summary(str(paper_id), str(new_job.id))
            elif req.job_type == "mind_map":
                await task_queue.enqueue_mind_map(str(paper_id), str(new_job.id))
            elif req.job_type == "chat":
                await task_queue.enqueue_chat(str(paper_id), str(new_job.id), req.params.get("message", ""))
            else:
                from loguru import logger
                logger.warning(f"Unsupported job type: {req.job_type}")
        except Exception as e:
             # log error but return success as job is created
             print(f"Failed to enqueue job: {e}")
        
        # Map entity to response
        return JobResponse(
            id=new_job.id,
            job_type=new_job.type,
            status=new_job.status,
            progress=new_job.progress,
            created_at=new_job.created_at,
            result=new_job.result,
            error_message=new_job.error
        )

    async def re_enqueue_job(self, job_id: UUID) -> bool:
        """
        重新入队任务（用于恢复僵尸任务）
        Arq 保证幂等性：如果任务 ID 已在队列中，不会重复添加。
        """
        stmt = select(Job).where(Job.id == job_id)
        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return False
            
        try:
            # Update status in DB
            job.status = "queued"
            job.error = None
            job.end_at = None
            job.progress = 0
            await self.session.commit()

            if job.type == "parse_text":
                await task_queue.enqueue_parse_text(str(job.paper_id), str(job.id))
            elif job.type == "vectorize":
                await task_queue.enqueue_vectorize(str(job.paper_id), str(job.id))
            elif job.type == "summary":
                await task_queue.enqueue_summary(str(job.paper_id), str(job.id))
            elif job.type == "mind_map":
                await task_queue.enqueue_mind_map(str(job.paper_id), str(job.id))
            elif job.type == "chat":
                await task_queue.enqueue_chat(str(job.paper_id), str(job.id), "")
            else:
                return False
            return True
        except Exception as e:
            print(f"Failed to re-enqueue job {job_id}: {e}")
            return False

    async def get_job(self, job_id: UUID, user_id: UUID) -> JobResponse:
        # Join Paper to check user permission
        stmt = (
            select(Job)
            .join(Paper)
            .where(Job.id == job_id, Paper.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse(
            id=job.id,
            job_type=job.type,
            status=job.status,
            progress=job.progress,
            created_at=job.created_at,
            result=job.result,
            error_message=job.error
        )

    async def subscribe_job_events(self, job_id: UUID, user_id: UUID) -> AsyncGenerator[str, None]:
        # 1. Check permission & Get current status
        job_response = await self.get_job(job_id, user_id)
        
        # Yield current status immediately
        yield self._format_sse(
            "start", 
            job_id, 
            job_response.status, 
            job_response.progress or 0, 
            "Checking status...", 
            result=job_response.result,
            error=job_response.error_message
        )
        
        if job_response.status in ["succeeded", "failed"]:
            yield self._format_sse("end", job_id, job_response.status, job_response.progress or 0, "Job already finished")
            return

        # 2. Subscribe to Redis
        redis_url = settings.arq_redis_url
        # Use redis.asyncio.from_url
        r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        pubsub = r.pubsub()
        channel = f"job_progress:{job_id}"
        await pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    # data format: {"status": ..., "stage": ..., "progress": ..., "error": ..., "result": ...}
                    
                    yield self._format_sse(
                        "progress", 
                        job_id, 
                        data.get("status", "running"), 
                        data.get("progress", 0), 
                        data.get("stage", ""),
                        result=data.get("result"),
                        error=data.get("error")
                    )
                    
                    if data.get("status") in ["succeeded", "failed"]:
                         yield self._format_sse("end", job_id, data.get("status"), data.get("progress"), "Job finished")
                         break
        except Exception as e:
             yield self._format_sse("error", job_id, "failed", 0, str(e))
        finally:
            await pubsub.unsubscribe(channel)
            await r.close()

    async def get_queue_metrics(self) -> Dict[str, Any]:
        """
        获取 Redis 队列监控指标
        """
        redis_url = settings.arq_redis_url
        r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        
        metrics = {
            "queues": {}
        }
        
        try:
            # 1. 扫描所有队列键 (arq:queue, pdf_processing, etc.)
            # Arq 使用 List 结构存储队列
            queue_keys = ['arq:queue', 'pdf_processing', 'embeddings', 'llm_tasks']
            
            for q in queue_keys:
                length = await r.llen(q)
                metrics["queues"][q] = length
                
            # 2. 获取正在处理的任务 (Arq Sets)
            # arq:in_progress (Set of job_ids)
            in_progress_count = await r.scard('arq:in_progress')
            metrics["in_progress_total"] = in_progress_count
            
            # 3. 获取失败任务 (ZSet)
            # arq:result:* (Keys) - Hard to count all without scan
            # But we can check retry sets if any
            
        except Exception as e:
            metrics["error"] = str(e)
        finally:
            await r.close()
            
        return metrics

    def _format_sse(self, state: str, job_id: UUID, status: str, progress: float, stage: str, result: Any = None, error: str = None) -> str:
        payload = JobEventPayload(
            job_id=job_id,
            type="unknown", # Should retrieve type from job if possible, or pass it in
            status=status,
            progress=progress,
            stage=stage,
            result=result,
            error=error
        )
        envelope = SSEDataEnvelope(
            state=state,
            payload=payload
        )
        
        # Use lowercase event names matching frontend expectations
        # Map "error" to "job_error" to avoid conflict with native SSE error event
        event_name = state.lower()
        if event_name == "error":
            event_name = "job_error"
            
        return f"id: {uuid4()}\nevent: {event_name}\ndata: {envelope.model_dump_json()}\n\n"

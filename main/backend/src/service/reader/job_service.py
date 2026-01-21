from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from base.pg.entity import Job, Paper
from service.reader.schema import Job as JobDTO, JobResult


class JobService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_jobs(self, paper_id: UUID, user_id: UUID) -> List[JobDTO]:
        # Job does not have user_id, join Paper
        stmt = (
            select(Job)
            .join(Paper)
            .where(Job.paper_id == paper_id, Paper.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        jobs = result.scalars().all()
        
        items = [
            JobDTO(
                id=j.id,
                job_type=j.job_type,
                status=j.status,
                progress=float(j.progress) / 100.0 if j.progress is not None else 0.0,
                stage=j.stage,
                error_message=j.error_message,
                created_at=j.created_at,
                completed_at=j.completed_at,
                result=None # TODO: Implement result parsing logic
            ) for j in jobs
        ]
        return items

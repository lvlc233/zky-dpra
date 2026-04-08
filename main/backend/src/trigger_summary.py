
import asyncio
from uuid import UUID
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import Paper, Job
from service.reader.job_service import JobService
from controller.api.reader.schema import JobCreateRequest

async def trigger_summary():
    async with async_session_factory() as session:
        # Get the latest paper
        stmt = select(Paper).order_by(Paper.created_at.desc()).limit(1)
        result = await session.execute(stmt)
        paper = result.scalar_one_or_none()
        
        if not paper:
            print("No papers found.")
            return

        print(f"Triggering summary for paper: {paper.id} ({paper.title})")
        
        # Use JobService
        job_service = JobService(session)
        req = JobCreateRequest(job_type="summary")
        resp = await job_service.create_job(paper.id, req, paper.user_id)
        
        print(f"Job triggered via JobService: {resp.id}")

if __name__ == "__main__":
    asyncio.run(trigger_summary())

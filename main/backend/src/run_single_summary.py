
import asyncio
from uuid import UUID
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import Paper, Job
from worker.tasks import summary_task
from loguru import logger

async def run_single():
    async with async_session_factory() as session:
        # Get the latest failed summary job or paper
        stmt = select(Job).where(Job.type == "summary").order_by(Job.created_at.desc()).limit(1)
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            print("No summary jobs found.")
            return

        print(f"Running summary_task for paper: {job.paper_id}, Job: {job.id}")
        
        # Mock ctx
        ctx = {'redis': None}
        
        # Run the task directly
        result = await summary_task(ctx, str(job.paper_id), str(job.id))
        print(f"Task result: {result}")

if __name__ == "__main__":
    asyncio.run(run_single())

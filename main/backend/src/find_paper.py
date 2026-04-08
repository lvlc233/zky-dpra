
import asyncio
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import Paper, Job

async def list_all():
    async with async_session_factory() as session:
        stmt = select(Paper).order_by(Paper.created_at.desc())
        result = await session.execute(stmt)
        papers = result.scalars().all()
        print(f"Total Papers Found: {len(papers)}")
        for p in papers:
            print(f"ID: {p.id} | Status: {p.analysis_status} | Title: {p.title}")
            
            stmt_job = select(Job).where(Job.paper_id == p.id).order_by(Job.created_at.desc())
            res_job = await session.execute(stmt_job)
            jobs = res_job.scalars().all()
            for j in jobs:
                print(f"  Job: {j.id} | Type: {j.type} | Status: {j.status} | Progress: {j.progress}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(list_all())

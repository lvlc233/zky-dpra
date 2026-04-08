
import asyncio
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import Paper, Job

async def find_all():
    async with async_session_factory() as session:
        stmt = select(Paper)
        result = await session.execute(stmt)
        papers = result.scalars().all()
        print(f"Total Papers: {len(papers)}")
        for i, p in enumerate(papers):
            print(f"{i+1}. {p.title[:40]}... | Status: {p.analysis_status} | ID: {p.id}")
            
            # Jobs
            stmt_job = select(Job).where(Job.paper_id == p.id).order_by(Job.created_at.desc())
            res_job = await session.execute(stmt_job)
            jobs = res_job.scalars().all()
            for j in jobs:
                print(f"   - Job: {j.type} | Status: {j.status} | Progress: {j.progress}")

if __name__ == "__main__":
    asyncio.run(find_all())

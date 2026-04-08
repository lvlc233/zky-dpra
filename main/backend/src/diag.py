
import asyncio
import json
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import Paper, Job

async def diag():
    async with async_session_factory() as session:
        # Get last 10 papers
        stmt = select(Paper).order_by(Paper.created_at.desc()).limit(1)
        res = await session.execute(stmt)
        p = res.scalar_one_or_none()
        if p:
            print(f"TITLE: {repr(p.title)}")
            print(f"STATUS: {repr(p.analysis_status)}")
            print(f"ID: {p.id}")
            
            stmt_job = select(Job).where(Job.paper_id == p.id).order_by(Job.created_at.desc())
            res_job = await session.execute(stmt_job)
            jobs = res_job.scalars().all()
            for j in jobs:
                print(f"  JOB: {j.id} | Type: {j.type} | Status: {j.status} | Progress: {j.progress}")
        else:
            print("No papers found")

if __name__ == "__main__":
    asyncio.run(diag())

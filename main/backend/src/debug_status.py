import asyncio
import os
from uuid import UUID
from sqlmodel import select
from dotenv import load_dotenv

# Load .env before imports that use settings
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from base.pg.service import async_session_factory
from base.pg.entity import Paper, Job

async def debug_paper(title_part):
    async with async_session_factory() as session:
        # 1. Find paper by title
        stmt = select(Paper).where(Paper.title.ilike(f"%{title_part}%"))
        result = await session.execute(stmt)
        papers = result.scalars().all()
        
        for p in papers:
            print(f"Paper: {p.title} ({p.id})")
            print(f"  Status: {p.analysis_status}")
            print(f"  Created At: {p.created_at}")
            
            # 2. Get all jobs for this paper
            stmt_jobs = select(Job).where(Job.paper_id == p.id).order_by(Job.created_at.desc())
            result_jobs = await session.execute(stmt_jobs)
            jobs = result_jobs.scalars().all()
            
            print(f"  Jobs ({len(jobs)}):")
            for j in jobs:
                print(f"    - Type: {j.type}, Status: {j.status}, Stage: {j.stage}, Progress: {j.progress}, Created: {j.created_at}")

if __name__ == "__main__":
    import sys
    title = sys.argv[1] if len(sys.argv) > 1 else "Coupled Control"
    asyncio.run(debug_paper(title))

import asyncio
import os
import sys
from uuid import UUID

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__name__))
src_dir = os.path.join(current_dir, "backend", "src")
sys.path.append(src_dir)

async def check_jobs():
    from base.pg.service import async_session_factory
    from base.pg.entity import Job
    from sqlalchemy import select, desc
    
    async with async_session_factory() as session:
        stmt = select(Job).where(Job.type == 'mind_map').order_by(desc(Job.created_at)).limit(5)
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        print(f"{'ID':<40} | {'Type':<12} | {'Status':<10} | {'Error'}")
        print("-" * 120)
        for job in jobs:
            error_msg = str(job.error) if job.error else "None"
            print(f"{str(job.id):<40} | {job.type:<12} | {job.status:<10} | {error_msg}")

if __name__ == "__main__":
    asyncio.run(check_jobs())

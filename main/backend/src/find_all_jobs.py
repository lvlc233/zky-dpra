
import asyncio
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import Job, Paper

async def find_all():
    async with async_session_factory() as session:
        # Get last 20 jobs
        stmt = select(Job).order_by(Job.created_at.desc()).limit(20)
        res = await session.execute(stmt)
        jobs = res.scalars().all()
        
        print(f"{'Job ID':<40} | {'Type':<12} | {'Status':<10} | {'Paper ID'}")
        print("-" * 80)
        for j in jobs:
            print(f"{str(j.id):<40} | {j.type:<12} | {j.status:<10} | {str(j.paper_id)}")
            # Try to get paper title
            if j.paper_id:
                p_stmt = select(Paper).where(Paper.id == j.paper_id)
                p_res = await session.execute(p_stmt)
                p = p_res.scalar_one_or_none()
                if p:
                    print(f"   -> Paper: {p.title}")
                else:
                    print(f"   -> Paper NOT FOUND in papers table!")

if __name__ == "__main__":
    asyncio.run(find_all())

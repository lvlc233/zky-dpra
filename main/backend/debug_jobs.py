
import asyncio
from uuid import UUID
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import Job

async def check():
    async with async_session_factory() as session:
        stmt = select(Job).order_by(Job.created_at.desc()).limit(10)
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        for job in jobs:
            print(f"ID: {job.id}")
            print(f"  Type: {job.type}")
            print(f"  Status: {job.status}")
            print(f"  Error: {job.error}")
            print("-" * 20)

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.join(os.getcwd(), "src"))
    asyncio.run(check())

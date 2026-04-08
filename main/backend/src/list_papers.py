
import asyncio
from sqlmodel import select
from base.pg.service import async_session_factory
from base.pg.entity import Paper

async def list_papers():
    async with async_session_factory() as session:
        stmt = select(Paper).order_by(Paper.created_at.desc()).limit(10)
        result = await session.execute(stmt)
        papers = result.scalars().all()
        for p in papers:
            print(f"[{p.analysis_status}] {p.title} ({p.id})")

if __name__ == "__main__":
    asyncio.run(list_papers())

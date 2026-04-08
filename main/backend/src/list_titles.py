
import asyncio
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import Paper

async def list_all():
    async with async_session_factory() as session:
        stmt = select(Paper)
        res = await session.execute(stmt)
        papers = res.scalars().all()
        print(f"Total Papers: {len(papers)}")
        for p in papers:
            print(f"[{p.analysis_status}] {p.title}")

if __name__ == "__main__":
    asyncio.run(list_all())

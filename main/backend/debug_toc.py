import asyncio
import sys
import os
from sqlalchemy import select
from uuid import UUID

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

from base.pg.service import async_session_factory
from base.pg.entity import Paper

async def check_toc():
    async with async_session_factory() as session:
        # 获取最近更新的一篇论文
        stmt = select(Paper).order_by(Paper.updated_at.desc()).limit(1)
        result = await session.execute(stmt)
        paper = result.scalar_one_or_none()
        
        if paper:
            print(f"Paper ID: {paper.id}")
            print(f"Title: {paper.title}")
            print(f"TOC Type: {type(paper.toc)}")
            print(f"TOC Content: {paper.toc}")
        else:
            print("No papers found.")

if __name__ == "__main__":
    asyncio.run(check_toc())

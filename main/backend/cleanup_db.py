
import asyncio
import os
import sys
from sqlalchemy import delete

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

from base.pg.service import async_session_factory
from base.pg.entity import PaperSummary

async def cleanup_corrupted_summaries():
    async with async_session_factory() as session:
        # Delete summaries containing "Connection error" or "发生错误"
        # Since these are now saved as content due to the previous bugged fix
        stmt = delete(PaperSummary).where(
            PaperSummary.content.like("%Connection error%") | 
            PaperSummary.content.like("%发生错误%")
        )
        result = await session.execute(stmt)
        await session.commit()
        print(f"Successfully deleted {result.rowcount} corrupted summaries.")

if __name__ == "__main__":
    asyncio.run(cleanup_corrupted_summaries())

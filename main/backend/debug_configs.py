
import asyncio
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import SystemModelConfig

async def check():
    async with async_session_factory() as session:
        stmt = select(SystemModelConfig)
        result = await session.execute(stmt)
        configs = result.scalars().all()
        for c in configs:
            print(f"Type: {c.type}, Provider: {c.provider}, Model: {c.model_name}, API Key: {c.api_key[:10] if c.api_key else 'None'}...")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.join(os.getcwd(), "src"))
    asyncio.run(check())

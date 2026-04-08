import asyncio
import os
import sys
from uuid import UUID

# Ensure src is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from base.pg.service import async_session_factory
from base.pg.entity import SystemModelConfig
from sqlalchemy import select

async def main():
    async with async_session_factory() as session:
        stmt = select(SystemModelConfig).where(SystemModelConfig.type == 'summary')
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()
        if config:
            print(f"Summary Config Found:")
            print(f"  Provider: {config.provider}")
            print(f"  Model Name: {config.model_name}")
            print(f"  Base URL: {config.base_url}")
            print(f"  API Key Length: {len(config.api_key) if config.api_key else 0}")
            print(f"  API Key Prefix: {config.api_key[:10] if config.api_key else 'None'}")
            if config.api_key and "*" in config.api_key:
                print("  WARNING: API Key contains asterisks!")
        else:
            print("Summary Config NOT FOUND in database!")

if __name__ == "__main__":
    asyncio.run(main())

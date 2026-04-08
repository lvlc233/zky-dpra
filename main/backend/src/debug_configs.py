
import asyncio
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import SystemModelConfig, User

async def check_configs():
    async with async_session_factory() as session:
        # Check system configs
        stmt = select(SystemModelConfig)
        result = await session.execute(stmt)
        configs = result.scalars().all()
        print("--- System Model Configs ---")
        for c in configs:
            mask_key = c.api_key[:6] + "..." if c.api_key else "None"
            print(f"Type: {c.config_type}, Provider: {c.provider}, Model: {c.model_name}, BaseURL: {c.base_url}, APIKey: {mask_key}")
        
        # Check user settings for a sample user if needed
        # stmt = select(User).limit(5)
        # result = await session.execute(stmt)
        # users = result.scalars().all()
        # for u in users:
        #     print(f"User: {u.email}, Settings: {u.settings}")

if __name__ == "__main__":
    asyncio.run(check_configs())

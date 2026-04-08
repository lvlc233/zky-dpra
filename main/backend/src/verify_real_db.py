
import asyncio
import os
from sqlalchemy import text
from base.pg.service import async_session_factory, engine

async def verify_configs():
    print(f"Connecting to: {engine.url}")
    async with async_session_factory() as session:
        try:
            result = await session.execute(text("SELECT * FROM system_model_config;"))
            configs = result.fetchall()
            print(f"Found {len(configs)} configs in system_model_config:")
            for c in configs:
                 # Assuming columns: config_type, model_provider, model_name, base_url, api_key, etc.
                 # Let's use index if we don't know names accurately from the print
                 print(f" - {c}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_configs())

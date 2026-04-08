import asyncio
import os
import sys

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), "src"))

from base.pg.service import SearchApiConfigRepository, async_session_factory

async def check():
    async with async_session_factory() as session:
        configs = await SearchApiConfigRepository.get_all_configs(session)
        print("\n--- Current Search API Configurations ---")
        if not configs:
            print("No configurations found.")
        for c in configs:
            key_status = "SET" if c.api_key and c.api_key.strip() else "EMPTY"
            print(f"API: {c.api_name:18} | Active: {str(c.is_active):5} | Key: {key_status:5} | Weight: {c.weight}")
        print("------------------------------------------\n")

if __name__ == "__main__":
    asyncio.run(check())

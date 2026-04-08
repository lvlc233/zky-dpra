import asyncio
import os
import sys
import json
from uuid import UUID

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__name__))
src_dir = os.path.join(current_dir, "backend", "src")
sys.path.append(src_dir)

async def debug_config():
    from base.pg.service import async_session_factory
    from base.pg.entity import User, SystemModelConfig, SearchApiConfig
    from sqlalchemy import select
    
    async with async_session_factory() as session:
        # 1. Check System Model Configs (LLM)
        print("\n=== System Model Configs (LLM) ===")
        stmt = select(SystemModelConfig)
        result = await session.execute(stmt)
        configs = result.scalars().all()
        for c in configs:
            print(f"Type: {c.type:<10} | Provider: {c.provider:<10} | Model: {c.model_name:<20} | Key: {c.api_key[:4]}...{c.api_key[-4:] if c.api_key else ''}")

        # 2. Check Search API Configs
        print("\n=== Search API Configs ===")
        stmt = select(SearchApiConfig)
        result = await session.execute(stmt)
        search_configs = result.scalars().all()
        for c in search_configs:
            print(f"Name: {c.api_name:<10} | Active: {c.is_active:<5} | Key: {c.api_key[:4]}...{c.api_key[-4:] if c.api_key else ''}")

        # 3. Check User Settings
        print("\n=== User Settings ===")
        stmt = select(User).limit(5)
        result = await session.execute(stmt)
        users = result.scalars().all()
        for u in users:
            print(f"User: {u.email:<15} ({u.id})")
            settings = u.settings if isinstance(u.settings, dict) else (u.settings.model_dump() if u.settings else {})
            # print(json.dumps(settings, indent=2, ensure_ascii=False))
            # Just check if keys exist
            if settings:
                print(f"  AI Reader Items: {len(settings.get('ai_reader_settings', []))}")
                for item in settings.get('ai_reader_settings', []):
                    print(f"    - {item.get('type')}: Key={item.get('api_key')[:4] if item.get('api_key') else 'Empty'}")

if __name__ == "__main__":
    asyncio.run(debug_config())


import asyncio
from uuid import uuid4
from sqlalchemy import text
from base.pg.service import async_session_factory, engine

async def populate_configs():
    print(f"Connecting to: {engine.url}")
    async with async_session_factory() as session:
        try:
            # Use SiliconFlow defaults as seen in .env
            sf_key = "sk-dtjmwtsffddmuznojosfzqqiidhvezgtrmowbfdrbuyfonzl"
            sf_url = "https://api.siliconflow.cn/v1"
            model = "deepseek-ai/DeepSeek-V3"

            configs = [
                ("chat", "openai", model, sf_url, sf_key),
                ("summary", "openai", model, sf_url, sf_key),
                ("mind_map", "openai", model, sf_url, sf_key)
            ]
            
            for config_type, provider, model_name, url, key in configs:
                stmt = text("""
                    INSERT INTO system_model_config (id, config_type, provider, model_name, base_url, api_key, is_active, created_at, updated_at)
                    VALUES (:id, :type, :provider, :model, :url, :key, true, now(), now())
                    ON CONFLICT (config_type) DO UPDATE 
                    SET provider = :provider, model_name = :model, base_url = :url, api_key = :key, updated_at = now();
                """)
                await session.execute(stmt, {
                    "id": uuid4(),
                    "type": config_type,
                    "provider": provider,
                    "model": model_name,
                    "url": url,
                    "key": key
                })
            
            await session.commit()
            print("Successfully populated system_model_config with SiliconFlow defaults.")
        except Exception as e:
            print(f"Error populating configs: {e}")

if __name__ == "__main__":
    asyncio.run(populate_configs())

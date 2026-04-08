
import asyncio
from sqlalchemy import text
from base.pg.service import engine

async def check_table():
    async with engine.connect() as conn:
        try:
            result = await conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'system_model_config');"))
            exists = result.scalar()
            print(f"Table 'system_model_config' exists: {exists}")
            
            # Also check columns if exists
            if exists:
                result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'system_model_config';"))
                cols = result.fetchall()
                print("Columns:")
                for c in cols:
                    print(f" - {c[0]} ({c[1]})")
        except Exception as e:
            print(f"Error checking table: {e}")

if __name__ == "__main__":
    asyncio.run(check_table())

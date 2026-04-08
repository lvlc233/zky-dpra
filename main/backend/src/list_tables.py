
import asyncio
from sqlalchemy import text
from base.pg.service import engine

async def list_tables():
    async with engine.connect() as conn:
        try:
            # Check alembic_version
            res = await conn.execute(text("SELECT version_num FROM alembic_version;"))
            version = res.scalar()
            print(f"Alembic current version in DB: {version}")
            
            # List all tables in public schema
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
            tables = result.fetchall()
            print("Tables in 'public' schema:")
            for t in tables:
                print(f" - {t[0]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_tables())

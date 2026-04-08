import asyncio
from uuid import uuid4
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from base.pg.entity import SearchApiConfig
from base.config import settings

async def seed():
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    engine = create_async_engine(database_url)
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_factory() as session:
        # Check OpenAlex
        stmt = select(SearchApiConfig).where(SearchApiConfig.api_name == "OpenAlex")
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            print("Adding OpenAlex config...")
            config = SearchApiConfig(
                id=uuid4(),
                api_name="OpenAlex",
                api_key="",
                is_active=True,
                weight=8,
                description="OpenAlex: Open and free index of scholarly works."
            )
            session.add(config)
        else:
            print("OpenAlex config already exists.")

        # Check CORE
        stmt = select(SearchApiConfig).where(SearchApiConfig.api_name == "CORE")
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            print("Adding CORE config...")
            config = SearchApiConfig(
                id=uuid4(),
                api_name="CORE",
                api_key="",
                is_active=True,
                weight=6,
                description="CORE: Aggregating open access papers from repositories."
            )
            session.add(config)
        else:
            print("CORE config already exists.")
            
        await session.commit()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(seed())

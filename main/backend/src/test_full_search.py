import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from service.search.search_service import SearchService
from controller.api.search.schema import SearchRequest
from base.config import settings
from uuid import UUID

async def test_full_search():
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    engine = create_async_engine(database_url)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_factory() as session:
        service = SearchService(session)
        # Mock user ID (System Admin from previous logs)
        user_id = UUID('caa717cb-b497-41ea-bb9d-27857e9088b3')
        
        request = SearchRequest(
            query="Large Language Models",
            limit=5,
            page=1
        )
        
        print("Starting aggregated search...")
        # We need api_configs. SearchService.search_papers fetches them if not provided.
        # But we can just call _search_external directly for testing if we mock configs.
        from service.setting.schema import SearchApiConfigInfo
        configs = [
            SearchApiConfigInfo(api_name="OpenAlex", is_active=True, weight=10, api_key=""),
            SearchApiConfigInfo(api_name="arXiv", is_active=True, weight=9, api_key=""),
            SearchApiConfigInfo(api_name="Crossref", is_active=True, weight=1, api_key="")
        ]
        
        result = await service._search_external(user_id, request, configs)
        print(f"Total results: {result.total}")
        for i, item in enumerate(result.items):
            print(f"{i+1}. [{item.source}] {item.title}")
            print(f"   URL: {item.url}")

if __name__ == "__main__":
    asyncio.run(test_full_search())

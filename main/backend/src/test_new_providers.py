import asyncio
from service.papers.open_alex_service import OpenAlexProvider

async def test():
    print("Testing OpenAlex (OA Only)...")
    oa = OpenAlexProvider()
    results, total = await oa.search_papers("Deep Learning", max_results=5)
    print(f"OpenAlex total: {total}")
    for i, p in enumerate(results):
        print(f"{i+1}. {p.title}")
        print(f"   - PDF: {p.pdf_url}")
        print(f"   - Paper URL: {p.paper_url}")

if __name__ == "__main__":
    asyncio.run(test())

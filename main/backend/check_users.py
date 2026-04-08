import asyncio
from sqlalchemy import text
from base.pg.service import async_session_factory

async def check():
    async with async_session_factory() as session:
        result = await session.execute(text('SELECT email FROM "users"'))
        emails = [row[0] for row in result.all()]
        print(f"EMAILS: {emails}")

if __name__ == "__main__":
    import os
    import sys
    # Add src to path
    sys.path.append(os.path.join(os.getcwd(), "src"))
    asyncio.run(check())

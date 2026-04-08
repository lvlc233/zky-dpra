import asyncio
import os
import sys

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from base.pg.service import async_session_factory
from base.pg.entity import User
from sqlalchemy import select

async def main():
    emails = ['admin@drap.com', 'admin@example.com']
    async with async_session_factory() as session:
        for email in emails:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                print(f"Setting {email} as admin...")
                user.is_admin = True
                session.add(user)
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())

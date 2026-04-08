import asyncio
from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import User

async def update_admin_flag():
    async with async_session_factory() as session:
        statement = select(User).where(User.email == 'admin@drap.com')
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if user:
            print(f"Updating user {user.email} (Current is_admin: {user.is_admin})")
            user.is_admin = True
            session.add(user)
            await session.commit()
            print("Successfully set is_admin = True for admin@drap.com")
        else:
            print("User admin@drap.com not found")

if __name__ == "__main__":
    import sys
    import os
    # Add src to path
    sys.path.append(os.path.join(os.getcwd(), 'src'))
    asyncio.run(update_admin_flag())

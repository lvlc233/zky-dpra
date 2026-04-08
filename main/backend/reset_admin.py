import asyncio
import os
import sys
from uuid import UUID
from sqlalchemy import text

async def reset():
    from base.pg.service import async_session_factory
    from common.security import get_password_hash
    
    email = "admin@drap.com"
    new_password = "admin123"
    hashed_password = get_password_hash(new_password)
    
    async with async_session_factory() as session:
        # Check if user exists
        result = await session.execute(text('SELECT id FROM "users" WHERE email = :email'), {"email": email})
        user_row = result.one_or_none()
        
        if user_row:
            user_id = user_row[0]
            await session.execute(
                text('UPDATE "users" SET hashed_password = :hp, is_admin = True WHERE id = :id'),
                {"hp": hashed_password, "id": user_id}
            )
            print(f"Password reset and admin flag set for {email}")
        else:
            # Create user if it doesn't exist
            from base.pg.entity import User
            from service.setting.schema import Settings
            from datetime import datetime
            import uuid
            
            new_user = User(
                id=uuid.uuid4(),
                email=email,
                hashed_password=hashed_password,
                full_name="Admin",
                is_active=True,
                is_admin=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                settings=Settings()
            )
            session.add(new_user)
            print(f"Created new admin user with admin flag: {email}")
        
        await session.commit()

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.path.join(os.getcwd(), "src"))
    asyncio.run(reset())

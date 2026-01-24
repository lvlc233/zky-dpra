
import sys
import asyncio
from unittest.mock import MagicMock, patch

# Mock dependencies
sys.modules['pgvector'] = MagicMock()
sys.modules['pgvector.sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.ext.asyncio'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.orm.attributes'] = MagicMock()
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['fastapi'] = MagicMock()
sys.modules['base.pg.service'] = MagicMock()
sys.modules['loguru'] = MagicMock()

# Now we can define User mock manually since entity.py import would fail or be mocked
class User:
    def __init__(self, id, email, password_hash):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.settings = None

# Mock SettingService imports
with patch.dict('sys.modules', {
    'base.pg.entity': MagicMock(),
    'base.config': MagicMock(),
}):
    # We need to import SettingService, but it imports entity.py.
    # We can try to rely on mocked modules, but entity.py is local.
    # Let's mock base.pg.entity.User with our User class
    sys.modules['base.pg.entity'].User = User
    
    # We also need Settings schema. 
    # Schema imports are simple (pydantic), should be fine.
    
    # Import SettingService
    # We need to set up path
    sys.path.append('g:\\work\\project\\bishe\\Agent\\DeepPaperResearcher\\zky\\zky-dpra\\main\\backend\\src')
    from service.setting.setting_service import SettingService

async def test_settings():
    # Mock DB session
    session = MagicMock()
    
    # Mock User with settings as dict
    user = User(id="uid", email="test@test.com", password_hash="hash")
    user.settings = {
        "ai_reader_settings": [
            {"type": "chat", "config": {"foo": "bar"}}
        ]
    }
    
    # Mock UserRepository
    service = SettingService(session)
    service._get_user = MagicMock(return_value=asyncio.Future())
    service._get_user.return_value.set_result(user)
    
    # Call get_settings
    settings = await service.get_settings(user.id)
    
    print(f"Type of settings: {type(settings)}")
    print(f"Content of settings: {settings}")
    
    try:
        print(f"Accessing via dot: {settings.ai_reader_settings}")
    except AttributeError as e:
        print(f"Dot access failed: {e}")
        
    try:
        print(f"Accessing via dict: {settings['ai_reader_settings']}")
    except Exception as e:
        print(f"Dict access failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_settings())

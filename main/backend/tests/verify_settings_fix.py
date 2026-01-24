
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

# Mock User
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
    sys.modules['base.pg.entity'].User = User
    sys.path.append('g:\\work\\project\\bishe\\Agent\\DeepPaperResearcher\\zky\\zky-dpra\\main\\backend\\src')
    from service.setting.setting_service import SettingService
    from service.setting.schema import Settings

async def test_settings_fix():
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
    print(f"Is instance of Settings: {isinstance(settings, Settings)}")
    
    # Verify we can access via dot
    try:
        print(f"Accessing via dot: {settings.ai_reader_settings}")
    except AttributeError as e:
        print(f"Dot access failed: {e}")
        
    # Verify dict access (should fail now)
    try:
        print(f"Accessing via dict: {settings['ai_reader_settings']}")
    except Exception as e:
        print(f"Dict access failed as expected: {e}")

if __name__ == "__main__":
    asyncio.run(test_settings_fix())

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient

from base.pg.entity import User
from controller.api.app import app
from controller.api.auth.router import get_current_user
from service.auth.auth_service import get_auth_service

# --- Service Tests ---

@pytest.mark.asyncio
async def test_update_user_settings_service():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    
    mock_user = User(
        id=uuid4(), 
        email="test@example.com", 
        hashed_password="pw",
        settings={"theme": "light"}
    )
    
    # Mock get_user_by_id in UserRepository (called by service.get_user)
    with patch("base.pg.service.UserRepository.get_user_by_id", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user
        
        from service.auth.auth_service import AuthService
        service = AuthService(session)
        
        new_settings = {"theme": "dark", "language": "en"}
        updated_user = await service.update_user_settings(mock_user.id, new_settings)
        
        assert updated_user.settings["theme"] == "dark"
        assert updated_user.settings["language"] == "en"
        session.add.assert_called()
        session.commit.assert_called()

# --- Controller Tests ---

@pytest.fixture
def mock_user_obj():
    return User(
        id=uuid4(), 
        email="test@example.com", 
        hashed_password="pw",
        settings={"theme": "light"}
    )

@pytest.fixture
def client(mock_user_obj):
    async def mock_get_current_user():
        return mock_user_obj
        
    async def mock_get_auth_service():
        mock_service = MagicMock()
        mock_service.session = AsyncMock()
        # Mock update_user_settings to return user with updated settings
        async def mock_update(uid, data):
            mock_user_obj.settings.update(data)
            return mock_user_obj
        mock_service.update_user_settings = AsyncMock(side_effect=mock_update)
        return mock_service

    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_auth_service] = mock_get_auth_service
    
    yield TestClient(app)
    
    app.dependency_overrides.clear()

def test_update_settings_api(client):
    payload = {
        "settings": {
            "theme": "dark",
            "language": "en"
        }
    }
    
    response = client.put("/api/v1/users/settings", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["theme"] == "dark"
    assert data["language"] == "en"

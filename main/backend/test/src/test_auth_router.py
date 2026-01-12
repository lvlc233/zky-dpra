'''
开发者: BackendAgent
当前版本: v1.1_test_auth
创建时间: 2026-01-12 13:30:00
更新时间: 2026-01-12 14:45:00
更新记录: 
    [2026-01-12 14:45:00:v1.1_test_auth:适配新异常处理机制与Service下沉逻辑]
    [2026-01-12 13:30:00:v1.0_test_auth:创建 Auth 模块集成测试]
'''

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock
from uuid import uuid4, UUID
from datetime import datetime

# Adjust path to include src if needed, usually pytest handles this or we set PYTHONPATH
# Assuming running from main/backend
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from controller.api.app import app
from service.auth.auth_service import AuthService, get_auth_service
from base.pg.entity import User
from common.security import create_access_token
from common.model.errors import AuthenticationError, BusinessError

client = TestClient(app, raise_server_exceptions=False)

# Mock Data
MOCK_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
MOCK_USER = User(
    id=MOCK_USER_ID,
    email="test@example.com",
    hashed_password="hashed_secret",
    full_name="Test User",
    is_active=True,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)

# Mock Service
mock_auth_service = AsyncMock(spec=AuthService)
mock_auth_service.authenticate_user.return_value = MOCK_USER
mock_auth_service.create_user.return_value = MOCK_USER
mock_auth_service.get_user.return_value = MOCK_USER
mock_auth_service.get_user_by_token.return_value = MOCK_USER

async def override_get_auth_service():
    return mock_auth_service

# Apply override
app.dependency_overrides[get_auth_service] = override_get_auth_service

def test_login_success():
    # Reset mock
    mock_auth_service.authenticate_user.side_effect = None
    mock_auth_service.authenticate_user.return_value = MOCK_USER
    
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password"}
    )
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["code"] == 200
    data = json_resp["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"

def test_login_failure():
    # Mock failure with Exception
    mock_auth_service.authenticate_user.side_effect = AuthenticationError("Incorrect email or password")
    
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "wrong"}
    )
    
    # Global exception handler returns 401 status code
    assert response.status_code == 401
    json_resp = response.json()
    assert json_resp["code"] == 401
    assert json_resp["message"] == "Incorrect email or password"
    
    # Reset side effect
    mock_auth_service.authenticate_user.side_effect = None
    mock_auth_service.authenticate_user.return_value = MOCK_USER

def test_register_success():
    # Reset mock
    mock_auth_service.create_user.side_effect = None
    mock_auth_service.create_user.return_value = MOCK_USER
    
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "password", "full_name": "New User"}
    )
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["code"] == 200
    assert json_resp["data"]["email"] == "test@example.com" # Returns mock user

def test_register_failure():
    # Mock failure with Exception
    mock_auth_service.create_user.side_effect = BusinessError("Email already registered")
    
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "existing@example.com", "password": "password"}
    )
    
    # Global exception handler returns 400 status code for BusinessError
    assert response.status_code == 400
    json_resp = response.json()
    assert json_resp["code"] == 400
    assert json_resp["message"] == "Email already registered"
    
    # Reset side effect
    mock_auth_service.create_user.side_effect = None
    mock_auth_service.create_user.return_value = MOCK_USER

def test_read_users_me():
    # Ensure get_user_by_token returns MOCK_USER
    mock_auth_service.get_user_by_token.return_value = MOCK_USER
    
    # Generate a valid token for the mock user
    token = create_access_token(subject=MOCK_USER_ID)
    
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["code"] == 200
    assert json_resp["data"]["email"] == "test@example.com"
    assert json_resp["data"]["id"] == str(MOCK_USER_ID)

def test_read_users_me_invalid_token():
    # Mock failure for invalid token in Service
    mock_auth_service.get_user_by_token.side_effect = AuthenticationError("Could not validate credentials")
    
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    
    # Reset side effect
    mock_auth_service.get_user_by_token.side_effect = None
    mock_auth_service.get_user_by_token.return_value = MOCK_USER

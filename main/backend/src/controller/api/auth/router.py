from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger

from controller.api.auth.schema import UserCreate, UserLogin, Token, UserResponse, UserSettings
# 假设有一个 UserService 处理业务逻辑
# from service.user.user_service import UserService

# 临时 Mock 依赖
router = APIRouter(prefix="/auth", tags=["auth"])

# TODO: 实现真正的 UserService 和 JWT 工具
class MockUserService:
    async def authenticate_user(self, email, password):
        if email == "test@example.com" and password == "password":
            return {"id": UUID("12345678-1234-5678-1234-567812345678"), "email": email, "full_name": "Test User", "is_active": True, "created_at": datetime.utcnow()}
        return None

    async def create_user(self, user: UserCreate):
        return {"id": UUID("12345678-1234-5678-1234-567812345678"), "email": user.email, "full_name": user.full_name, "is_active": True, "created_at": datetime.utcnow()}

    async def get_user(self, user_id: UUID):
        return {"id": user_id, "email": "test@example.com", "full_name": "Test User", "is_active": True, "created_at": datetime.utcnow()}

def get_user_service():
    return MockUserService()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), service=Depends(get_user_service)):
    # 简单 Mock，实际应解析 JWT
    return await service.get_user(UUID("12345678-1234-5678-1234-567812345678"))

@router.post("/login", response_model=Token)
async def login(
    form_data: UserLogin, # 也可以兼容 OAuth2PasswordRequestForm
    service: MockUserService = Depends(get_user_service)
):
    user = await service.authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Generate real JWT
    return {
        "access_token": "fake-jwt-token",
        "token_type": "bearer",
        "user": user
    }

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    service: MockUserService = Depends(get_user_service)
):
    # TODO: Check if user exists
    user = await service.create_user(user_in)
    return user

# Users router can be merged here or separate
users_router = APIRouter(prefix="/users", tags=["users"])

@users_router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@users_router.put("/settings")
async def update_settings(
    settings: UserSettings,
    current_user: UserResponse = Depends(get_current_user)
):
    # TODO: Update user settings in DB
    return {"settings": settings}

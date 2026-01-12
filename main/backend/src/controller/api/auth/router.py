'''
开发者: BackendAgent
当前版本: v1.0_auth_router
创建时间: 2026-01-12 13:15:00
更新时间: 2026-01-12 13:15:00
更新记录: 
    [2026-01-12 13:15:00:v1.0_auth_router:实现真实的认证路由，接入AuthService和JWT]
'''
# 主要就是生成一个jwt

from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession


from base.pg.entity import User
from service.auth.auth_service import AuthService,AuthServiceDep
from common.security import create_access_token
from controller.response import Response
from controller.api.auth.schema import UserCreate, UserLogin, Token, UserResponse, UserSettings


router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])

# OAuth2 Scheme
# 笔记: 这个可以获取请求头中的Authorization字段,简单来说就是获取token 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")




async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    service: AuthServiceDep
) -> User:
    """
    获取当前登录用户 (Dependency)
    从请求头中->从数据库中。
    
    Logic delegated to AuthService.
    """
    return await service.get_user_by_token(token)

# TODO: 接入第三方登录 (Google/GitHub), 计划单独开设 /auth/oauth/{provider} 接口

@router.post("/login", response_model=Response[Token])
async def login(
    form_data: UserLogin, # 支持 JSON Body
    service: AuthServiceDep
):
    """
    用户登录
    """
    # 数据库验证 (失败会抛出 AuthenticationError)
    user = await service.authenticate_user(form_data.email, form_data.password)
    
    # 生成 Token
    access_token = create_access_token(subject=user.id)
    
    return Response.success(data=Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    ))

@router.post("/register", response_model=Response[UserResponse])
async def register(
    user_in: UserCreate,
    service: AuthServiceDep
):
    """
    用户注册
    """
    # 失败会抛出 BusinessError
    user = await service.create_user(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name
    )
    
    return Response.success(data=UserResponse.model_validate(user))

@users_router.get("/me", response_model=Response[UserResponse])
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return Response.success(data=UserResponse.model_validate(current_user))

# 注意：users_router 需要在 app.py 中注册，或者这里合并
# 为方便起见，router 和 users_router 可以在 app.py 分别注册

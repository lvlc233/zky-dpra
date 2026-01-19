'''
开发者: BackendAgent
当前版本: v1.2_auth_login_set_cookie_response
创建时间: 2026-01-12 13:15:00
更新时间: 2026-01-17 23:11:00
更新记录: 
    [2026-01-12 13:15:00:v1.0_auth_router:实现真实的认证路由，接入AuthService和JWT]
    [2026-01-17 22:44:00:v1.1_auth_cookie_fallback:认证依赖支持从Cookie读取access_token，兼容浏览器直接打开PDF资源]
    [2026-01-17 23:11:00:v1.2_auth_login_set_cookie_response:登录接口改为显式 JSONResponse 设置 cookie，避免 Set-Cookie 丢失]
'''
# 主要就是生成一个jwt

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from base.pg.entity import User
from base.config import settings
from service.auth.auth_service import AuthServiceDep
from common.security import create_access_token
from controller.response import Response
from controller.api.auth.schema import UserCreate, UserLogin, Token, UserResponse


router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])

# OAuth2 Scheme
# 笔记: 这个可以获取请求头中的Authorization字段,简单来说就是获取token 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)



# 这里甚至直接用Entity..算了,所有的数据模型的问题都后面再说吧。
# 这里的鉴权这样子对吗?注入到其他的接口中,进行验证?->是标准的,可以用,这里就是解析jwt的数据解析出user_id,从请求头中。
async def get_current_user(
    request: Request,
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    service: AuthServiceDep
) -> User:
    """
    获取当前登录用户 (Dependency)
    从请求头中->从数据库中。
    
    Logic delegated to AuthService.
    """
    resolved_token = token
    if not resolved_token:
        resolved_token = request.cookies.get("access_token")

    if not resolved_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return await service.get_user_by_token(resolved_token)

# TODO: 为什么还要有个for_file的?上传文件的问题卡在了什么地方嘛?
async def get_current_user_for_file(
    request: Request,
    service: AuthServiceDep,
    token: Optional[str] = None,
    header_token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
) -> User:
    resolved_token = token or header_token or request.cookies.get("access_token")
    if not resolved_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return await service.get_user_by_token(resolved_token)

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

    payload = Response.success(data=Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )).model_dump(mode="json")

    resp = JSONResponse(status_code=status.HTTP_200_OK, content=payload)
    resp.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expiration_minutes * 60,
        path="/",
    )

    return resp

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
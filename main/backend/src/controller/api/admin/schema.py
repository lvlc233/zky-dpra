from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

class UserAdminResponse(BaseModel):
    """管理员视角的用户信息响应模型"""
    id: UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

class UserAdminListResponse(BaseModel):
    """用户列表分页响应"""
    users: List[UserAdminResponse]
    total: int

class UserCreateRequest(BaseModel):
    """创建用户请求"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False

class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class PasswordResetRequest(BaseModel):
    """管理员重置密码请求"""
    new_password: str

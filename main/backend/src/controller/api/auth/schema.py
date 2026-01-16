from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str
#  TODO:为什么要在鉴权这里,搞一个更新用户设置?有问题吧
class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    settings: Optional[dict] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class UserSettings(BaseModel):
    theme: Optional[str] = "light"
    language: Optional[str] = "zh"
    # 其他设置...
#  TODO:为什么要在鉴权这里,搞一个更新用户设置?有问题吧
class UserSettingsUpdate(BaseModel):
    settings: UserSettings

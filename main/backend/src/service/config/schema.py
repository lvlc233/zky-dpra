from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field

class ConfigCategoryRead(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]

class ConfigDefinitionRead(BaseModel):
    id: UUID
    category_id: Optional[UUID]
    key: str
    name: str
    description: Optional[str]
    value_type: str
    default_value: Optional[Dict[str, Any]]
    options: Optional[List[Dict[str, Any]]]
    scope: str
    is_public: bool

class UserConfigValueRead(BaseModel):
    config_key: str
    value: Any

class UserConfigUpdate(BaseModel):
    value: Any

class BatchConfigUpdate(BaseModel):
    configs: Dict[str, Any]

class UserSettingsResponse(BaseModel):
    settings: Dict[str, Any]

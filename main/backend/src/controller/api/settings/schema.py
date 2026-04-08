from typing import List

from pydantic import BaseModel

from service.setting.schema import AIReaderSettings, SystemSettings, AgentSettings, SystemStats


class AIReaderSettingsRequest(BaseModel):
    items: List[AIReaderSettings]


class AIReaderSettingsResponse(BaseModel):
    items: List[AIReaderSettings]


class AgentSettingsRequest(BaseModel):
    agent_settings: AgentSettings


class AgentSettingsResponse(BaseModel):
    agent_settings: AgentSettings


class SystemSettingsRequest(BaseModel):
    system_settings: SystemSettings


class SystemSettingsResponse(BaseModel):
    system_settings: SystemSettings


from service.setting.schema import SearchApiConfigInfo

class SearchApiConfigUpdate(BaseModel):
    api_name: str
    api_key: str | None = None
    weight: int = 0
    is_active: bool = True

class SearchApiConfigListResponse(BaseModel):
    configs: List[SearchApiConfigInfo]


class SystemStatsResponse(BaseModel):
    stats: SystemStats

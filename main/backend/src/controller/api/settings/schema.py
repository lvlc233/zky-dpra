from typing import List

from pydantic import BaseModel

from service.setting.schema import AIReaderSettings, SystemSettings, AgentSettings


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

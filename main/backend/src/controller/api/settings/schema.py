from typing import List

from pydantic import BaseModel

from service.setting.schema import AIReaderSettings, SystemSettings


class AIReaderSettingsRequest(BaseModel):
    items: List[AIReaderSettings]


class AIReaderSettingsResponse(BaseModel):
    items: List[AIReaderSettings]


class SystemSettingsRequest(BaseModel):
    system_settings: SystemSettings


class SystemSettingsResponse(BaseModel):
    system_settings: SystemSettings

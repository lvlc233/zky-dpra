"""
开发者: BackendAgent(python)
当前版本: v1.3_settings_schema_refactor
创建时间: 2026-01-14 19:20:00
更新时间: 2026-01-21 23:15:00
更新记录:
    [2026-01-14 19:20:00:v1.0_config_schema:初始化配置读取与更新模型]
    [2026-01-20 12:25:00:v1.1_config_schema:补充Settings模型供认证响应复用]
    [2026-01-20 12:46:00:v1.2_settings_schema_alignment:对齐统一架构 Settings 模型]
    [2026-01-21 23:15:00:v1.3_settings_schema_refactor:根据最新架构文档重构 Settings 模型]

变更说明:
    注释者: BackendAgent(python)
    注释时间: 2026-01-21 23:15:00
    使用说明: 供 /settings 模块接口与 Auth 响应复用
    实现概要: 定义搜索配置、AI 阅读配置、系统设置等结构化 DTO
    变更原因: 以统一架构文档为标准替换旧配置模型
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SearchSetting(BaseModel):
    match_analysis_status: Literal['unprocessed', 'processing', 'processed', 'error', ''] = ''
    min_date: Optional[datetime] = None  # 最小的上传时间
    max_date: Optional[datetime] = None  # 最大的上传时间
    limit: int = 10  # 每页返回的论文数量


class AIReaderSettings(BaseModel):
    type: Literal['chat', 'summary', 'mind_map']  # 配置类型 :[chat,总结,脑图]
    llm_name: str = ""  # 模型名
    provider: str = ""  # 供应商
    api_key: str = ""  # API 密钥
    base_url: str = ""  # base_url
    config: Dict[str, Any] = Field(default_factory=dict)  # 其他配置内容


class SystemSettings(BaseModel):
    system_colour: Literal['light', 'dark'] = 'light'  # 系统颜色 明亮|暗黑


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ai_reader_settings: List[AIReaderSettings] = Field(default_factory=list)
    search_settings: SearchSetting = Field(default_factory=SearchSetting)
    system_settings: SystemSettings = Field(default_factory=SystemSettings)

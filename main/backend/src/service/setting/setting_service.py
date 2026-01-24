"""
配置服务实现。

开发者: BackendAgent
当前版本: v1.3_setting_service_refactor
创建时间: 2026-01-14 19:00:00
更新时间: 2026-01-21 23:20:00
更新记录:
    [2026-01-14 19:00:00:v1.0_config_service:初始化配置服务]
    [2026-01-20 12:46:00:v1.1_setting_service_alignment:对齐统一架构 Settings 服务]
    [2026-01-21 23:20:00:v1.3_setting_service_refactor:根据最新架构文档重构 Settings 服务]

变更说明:
    注释者: BackendAgent(python)
    注释时间: 2026-01-21 23:20:00
    使用说明: Settings 服务供 /settings 模块与 Auth 响应读取用户设置
    实现概要: 基于 User.settings JSON 持久化，提供结构化读写与掩码处理
    变更原因: 以统一架构文档为标准替换旧配置服务
"""

from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from base.pg.entity import User
from base.pg.service import UserRepository
from service.setting.schema import (
    AIReaderSettings,
    SearchSetting,
    Settings,
    SystemSettings,
    AgentSettings,
)


class SettingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_user(self, user_id: UUID) -> User:
        user = await UserRepository.get_user_by_id(self.db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        return user

    def _mask_api_key(self, api_key: str) -> str:
        """
        掩盖API密钥,显示前4位和后4位,中间用****替换
        """
        if not api_key:
            return ""
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return f"{api_key[:4]}****{api_key[-4:]}"

    def _is_masked(self, api_key: str) -> bool:
        """
        检查API密钥是否被掩盖
        """
        return "****" in api_key

    async def _save_settings(self, user: User, settings: Settings) -> Settings:
        user.settings = settings
        flag_modified(user, "settings")
        await UserRepository.update_user(self.db, user)
        return settings

    async def get_settings(self, user_id: UUID) -> Settings:
        user = await self._get_user(user_id)
        if not user.settings:
            return Settings()
        
        # Ensure we return a Pydantic model, not a dict
        if isinstance(user.settings, dict):
            return Settings(**user.settings)
            
        return user.settings

    # --- Search Settings ---

    async def get_search_settings(self, user_id: UUID) -> SearchSetting:
        settings = await self.get_settings(user_id)
        return settings.search_settings

    async def update_search_settings(self, user_id: UUID, data: SearchSetting) -> SearchSetting:
        user = await self._get_user(user_id)
        settings = user.settings or Settings()
        settings.search_settings = data
        await self._save_settings(user, settings)
        return settings.search_settings

    # --- Agent Settings ---

    async def get_agent_settings(self, user_id: UUID) -> AgentSettings:
        settings = await self.get_settings(user_id)
        # Mask keys
        agent_settings = AgentSettings(**settings.agent_settings.model_dump())
        agent_settings.embedding_api_key = self._mask_api_key(agent_settings.embedding_api_key)
        agent_settings.rag_api_key = self._mask_api_key(agent_settings.rag_api_key)
        return agent_settings

    async def update_agent_settings(self, user_id: UUID, data: AgentSettings) -> AgentSettings:
        user = await self._get_user(user_id)
        current_settings = user.settings or Settings()
        
        # Handle masking: if key is masked (****), keep original
        if self._is_masked(data.embedding_api_key):
            data.embedding_api_key = current_settings.agent_settings.embedding_api_key
        if self._is_masked(data.rag_api_key):
            data.rag_api_key = current_settings.agent_settings.rag_api_key
            
        current_settings.agent_settings = data
        await self._save_settings(user, current_settings)
        return data

    # --- AI Reader Settings ---

    async def get_ai_reader_settings(self, user_id: UUID) -> List[AIReaderSettings]:
        settings = await self.get_settings(user_id)
        masked_items: List[AIReaderSettings] = []
        for item in settings.ai_reader_settings:
            # 创建副本以避免修改原始对象（虽然在这里是新建对象）
            masked_item = AIReaderSettings(
                **item.model_dump(),
            )
            # 掩盖 API Key
            masked_item.api_key = self._mask_api_key(item.api_key)
            
            # 掩盖 config 中的 embedding_api_key
            if 'embedding_api_key' in masked_item.config:
                masked_item.config['embedding_api_key'] = self._mask_api_key(masked_item.config['embedding_api_key'])
            
            masked_items.append(masked_item)
        return masked_items

    async def update_ai_reader_settings(self, user_id: UUID, items: List[AIReaderSettings]) -> List[AIReaderSettings]:
        user = await self._get_user(user_id)
        settings = user.settings or Settings()
        
        # 处理 API Key：如果新提交的 Key 是掩码格式，则保留旧 Key
        # 需要匹配 items，可以通过 type 来匹配
        old_items_map = {item.type: item for item in settings.ai_reader_settings}
        
        new_items: List[AIReaderSettings] = []
        for item in items:
            old_item = old_items_map.get(item.type)
            
            if self._is_masked(item.api_key):
                # 尝试从旧设置中找到对应的真实 Key
                if old_item:
                    item.api_key = old_item.api_key
                else:
                    # 如果没有旧项且提交了掩码（不应发生），则设为空或保持原样
                    item.api_key = ""
            
            # 处理 config 中的 embedding_api_key
            if 'embedding_api_key' in item.config and self._is_masked(item.config['embedding_api_key']):
                if old_item and 'embedding_api_key' in old_item.config:
                    item.config['embedding_api_key'] = old_item.config['embedding_api_key']
                else:
                    item.config['embedding_api_key'] = ""
                    
            new_items.append(item)
            
        settings.ai_reader_settings = new_items
        await self._save_settings(user, settings)
        
        return await self.get_ai_reader_settings(user_id)

    # --- System Settings ---

    async def get_system_settings(self, user_id: UUID) -> SystemSettings:
        settings = await self.get_settings(user_id)
        return settings.system_settings

    async def update_system_settings(self, user_id: UUID, data: SystemSettings) -> SystemSettings:
        user = await self._get_user(user_id)
        settings = user.settings or Settings()
        settings.system_settings = data
        await self._save_settings(user, settings)
        return settings.system_settings

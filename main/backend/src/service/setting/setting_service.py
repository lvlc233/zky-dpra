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

import time
import psutil
from typing import Any, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import text

from base.pg.service import UserRepository, PaperRepository, JobRepository, SearchApiConfigRepository, SystemModelConfigRepository
from base.pg.entity import User, SearchApiConfig, SystemModelConfig
from base.redis.service import RedisService
from service.setting.schema import (
    AIReaderSettings,
    SearchSetting,
    Settings,
    SystemSettings,
    AgentSettings,
    SearchApiConfigInfo,
    SystemStats,
    ServiceStatus
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
        logger.info(f"Updating agent settings for user {user_id}: {data}")
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
        logger.info(f"Updating AI reader settings for user {user_id}: {new_items}")
        
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

    # --- Search API Configs ---
    
    async def get_all_search_api_configs(self, user_id: UUID) -> List[SearchApiConfigInfo]:
        configs = await SearchApiConfigRepository.get_all_configs(self.db)
        
        masked_configs: List[SearchApiConfigInfo] = []
        for config in configs:
            masked_config = SearchApiConfigInfo(
                api_name=config.api_name,
                api_key=self._mask_api_key(config.api_key),
                weight=config.weight,
                is_active=config.is_active
            )
            masked_configs.append(masked_config)
            
        return masked_configs

    async def update_search_api_config(
        self, user_id: UUID, api_name: str, api_key: str, weight: int, is_active: bool
    ) -> SearchApiConfigInfo:
        # Check permission (optional, handled in router)
        
        # Get existing to handle masking
        existing = await SearchApiConfigRepository.get_config_by_name(self.db, api_name)
        
        final_api_key = api_key
        if self._is_masked(api_key):
            if existing:
                final_api_key = existing.api_key
            else:
                final_api_key = ""

        config_data = {
            "api_name": api_name,
            "api_key": final_api_key,
            "weight": weight,
            "is_active": is_active
        }
        
        config = await SearchApiConfigRepository.upsert_config(self.db, config_data)
        
        return SearchApiConfigInfo(
            api_name=config.api_name,
            api_key=self._mask_api_key(config.api_key),
            weight=config.weight,
            is_active=config.is_active
        )
        
    async def delete_search_api_config(self, user_id: UUID, api_name: str) -> bool:
        return await SearchApiConfigRepository.delete_config(self.db, api_name)

    async def get_system_stats(self) -> SystemStats:
        """获取系统实时运行统计数据"""
        # 1. 数据库统计 (PostgreSQL)
        user_count = await UserRepository.get_all_users_count(self.db)
        paper_count = await PaperRepository.get_all_papers_count(self.db)
        job_count = await JobRepository.get_active_jobs_count(self.db)

        service_statuses: list[ServiceStatus] = []

        # 2. 检查 PostgreSQL 延迟
        start_time = time.time()
        pg_ok = False
        try:
            await self.db.execute(text("SELECT 1"))
            pg_ok = True
        except Exception as e:
            logger.error(f"Monitoring: PostgreSQL check failed: {e}")
        pg_latency = (time.time() - start_time) * 1000
        service_statuses.append(ServiceStatus(name="PostgreSQL", status=pg_ok, latency=round(pg_latency, 2)))

        # 3. 检查 Redis 状态
        start_time = time.time()
        redis_ok = False
        try:
            client = RedisService.get_client()
            await client.ping()
            redis_ok = True
        except Exception as e:
            logger.error(f"Monitoring: Redis check failed: {e}")
        redis_latency = (time.time() - start_time) * 1000
        service_statuses.append(ServiceStatus(name="Redis", status=redis_ok, latency=round(redis_latency, 2)))


        # 5. 系统负载
        system_load = psutil.cpu_percent(interval=None)

        return SystemStats(
            user_count=user_count,
            paper_count=paper_count,
            api_request_count=job_count,
            system_load=system_load,
            service_statuses=service_statuses
        )

    async def get_effective_model_config(self, user_id: Optional[UUID], config_type: str) -> dict[str, Any]:
        """
        获取生效的模型配置 (优先级: 用户自定义 > 系统全局配置 > 默认硬编码值)
        """
        # 1. 寻找用户设置
        user_model_setting = None
        if user_id:
            try:
                user_settings = await self.get_settings(user_id)
                
                # 将 chat/summary/mind_map 统称为 AI 阅读设置中的对应项
                if config_type in ["chat", "summary", "mind_map"]:
                    for item in user_settings.ai_reader_settings:
                        if item.type == config_type:
                            user_model_setting = item
                            break
                elif config_type == "embedding":
                    # embedding 映射到 agent_settings
                    user_model_setting = user_settings.agent_settings
            except Exception as e:
                logger.warning(f"Failed to load user settings for {user_id}: {e}")

        # 2. 寻找系统全局配置
        system_config = await SystemModelConfigRepository.get_config_by_type(self.db, config_type)

        # 3. 合并逻辑 (优先级: 系统全局配置 > 用户自定义 > 默认硬编码值)
        # 默认值
        effective_config: dict[str, Any] = {
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "",
            "base_url": "",
            "system_prompt": "",
            "temperature": 0.7,
            "max_tokens": 4000,
            "config": {}
        }

        # 1. 应用用户设置 (作为基础覆盖)
        if user_model_setting:
            user_data = user_model_setting.model_dump()
            if user_data.get("provider"):
                effective_config["provider"] = user_data["provider"]
            
            if config_type in ["chat", "summary", "mind_map"]:
                if user_data.get("llm_name"):
                    effective_config["model_name"] = user_data["llm_name"]
            elif config_type == "embedding":
                if user_data.get("embedding_model"):
                    effective_config["model_name"] = user_data["embedding_model"]
            
            if user_data.get("api_key"):
                effective_config["api_key"] = user_data["api_key"]
            elif user_data.get("embedding_api_key"):
                effective_config["api_key"] = user_data["embedding_api_key"]
                
            if user_data.get("base_url"):
                effective_config["base_url"] = user_data["base_url"]
            elif user_data.get("embedding_base_url"):
                effective_config["base_url"] = user_data["embedding_base_url"]
            
            u_config = user_data.get("config", {})
            if u_config:
                effective_config["config"].update(u_config)
                if "temperature" in u_config:
                    effective_config["temperature"] = u_config["temperature"]
                if u_config.get("system_prompt"):
                    effective_config["system_prompt"] = u_config["system_prompt"]
                if "max_tokens" in u_config:
                    effective_config["max_tokens"] = u_config["max_tokens"]

        # 2. 应用系统全局配置 (最高优先级，直接覆盖用户设置)
        if system_config:
            if system_config.provider:
                effective_config["provider"] = system_config.provider
            if system_config.model_name:
                effective_config["model_name"] = system_config.model_name
            if system_config.api_key:
                effective_config["api_key"] = system_config.api_key
            if system_config.base_url:
                effective_config["base_url"] = system_config.base_url
            if system_config.system_prompt:
                # 系统提示词可以采取追加模式，或者直接覆盖。这里选择如果系统有，则覆盖。
                effective_config["system_prompt"] = system_config.system_prompt
            if system_config.temperature is not None:
                effective_config["temperature"] = system_config.temperature
            if system_config.max_tokens is not None:
                effective_config["max_tokens"] = system_config.max_tokens

        # 归一化 base_url: 确保 SiliconFlow 等提供商的 URL 以 /v1 结尾 (如果客户端库需要)
        if effective_config.get("base_url") and "siliconflow.cn" in effective_config["base_url"]:
            if not effective_config["base_url"].endswith("/v1") and not effective_config["base_url"].endswith("/v1/"):
                 effective_config["base_url"] = effective_config["base_url"].rstrip("/") + "/v1"

        logger.info(f"Effective config for {config_type}: model={effective_config.get('model_name')}, provider={effective_config.get('provider')}, base_url={effective_config.get('base_url')}, has_api_key={bool(effective_config.get('api_key'))}")
        return effective_config

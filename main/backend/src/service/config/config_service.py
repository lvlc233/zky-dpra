"""
配置服务实现。

开发者: BackendAgent
当前版本: v1.0_config_service
创建时间: 2026-01-14 19:00:00
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from base.pg.entity import ConfigCategory, ConfigDefinition, UserConfigValue, User


class ConfigService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.CACHE_TTL = 3600  # 1 hour
        self.CACHE_PREFIX = "user_config:"

    async def _get_cache_key(self, user_id: UUID) -> str:
        return f"{self.CACHE_PREFIX}{str(user_id)}"

    async def get_user_settings(self, user_id: UUID) -> Dict[str, Any]:
        """
        获取用户的所有配置。
        优先级: UserConfigValue > ConfigDefinition.default_value
        """
        cache_key = await self._get_cache_key(user_id)

        # 1. Try Cache
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to read config cache for user {user_id}: {e}")

        # 2. Query Definitions (System Defaults)
        definitions = (await self.db.exec(select(ConfigDefinition))).all()
        config_map = {}
        definition_map = {}
        
        for d in definitions:
            # Handle JSON default value
            default_val = d.default_value
            # if isinstance(default_val, str):
            #     try:
            #         default_val = json.loads(default_val)
            #     except:
            #         pass
            config_map[d.key] = default_val
            definition_map[d.id] = d.key

        # 3. Query User Overrides
        user_values = (await self.db.exec(
            select(UserConfigValue)
            .where(UserConfigValue.user_id == user_id)
        )).all()

        for uv in user_values:
            key = definition_map.get(uv.config_id)
            if key:
                # Handle JSON value
                val = uv.value
                # if isinstance(val, str):
                #     try:
                #         val = json.loads(val)
                #     except:
                #         pass
                config_map[key] = val

        # 4. Cache Result
        try:
            await self.redis.setex(cache_key, self.CACHE_TTL, json.dumps(config_map))
        except Exception as e:
            logger.warning(f"Failed to set config cache for user {user_id}: {e}")

        return config_map

    async def update_user_setting(self, user_id: UUID, key: str, value: Any) -> Dict[str, Any]:
        """
        更新单个配置项。
        """
        # 1. Validate Key
        definition = self.db.exec(
            select(ConfigDefinition).where(ConfigDefinition.key == key)
        ).first()

        if not definition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Config key '{key}' not found"
            )

        # 2. Validate Scope
        if definition.scope == "system":
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot modify system config '{key}'"
            )

        # 3. Update or Insert
        user_value = self.db.exec(
            select(UserConfigValue)
            .where(UserConfigValue.user_id == user_id)
            .where(UserConfigValue.config_id == definition.id)
        ).first()

        if user_value:
            user_value.value = value
            user_value.updated_at = datetime.now()
            self.db.add(user_value)
        else:
            user_value = UserConfigValue(
                user_id=user_id,
                config_id=definition.id,
                value=value
            )
            self.db.add(user_value)

        self.db.commit()
        
        # 4. Invalidate Cache
        await self.redis.delete(await self._get_cache_key(user_id))

        return await self.get_user_settings(user_id)

    async def batch_update_user_settings(self, user_id: UUID, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量更新配置。
        """
        # Pre-fetch all definitions involved
        keys = list(settings.keys())
        definitions = self.db.exec(
            select(ConfigDefinition).where(ConfigDefinition.key.in_(keys))
        ).all()
        
        definition_map = {d.key: d for d in definitions}
        
        # Pre-fetch existing user values
        existing_values = self.db.exec(
            select(UserConfigValue)
            .where(UserConfigValue.user_id == user_id)
            .where(UserConfigValue.config_id.in_([d.id for d in definitions]))
        ).all()
        
        existing_value_map = {uv.config_id: uv for uv in existing_values}
        
        for key, value in settings.items():
            definition = definition_map.get(key)
            if not definition:
                logger.warning(f"Skipping unknown config key: {key}")
                continue
            
            if definition.scope == "system":
                logger.warning(f"Skipping system config key: {key}")
                continue

            user_value = existing_value_map.get(definition.id)
            
            if user_value:
                user_value.value = value
                user_value.updated_at = datetime.now()
                self.db.add(user_value)
            else:
                user_value = UserConfigValue(
                    user_id=user_id,
                    config_id=definition.id,
                    value=value
                )
                self.db.add(user_value)
        
        self.db.commit()
        
        # Invalidate Cache
        await self.redis.delete(await self._get_cache_key(user_id))
        
        return await self.get_user_settings(user_id)

    async def get_agent_config(self, user_id: UUID, agent_name: str) -> Dict[str, Any]:
        """
        获取 Agent 专属配置。
        """
        all_settings = await self.get_user_settings(user_id)
        # TODO: Filter logic based on naming convention?
        # For now, return all settings, let Agent decide what to use.
        return all_settings

    async def init_default_configs(self):
        """
        初始化系统默认配置（幂等操作）。
        """
        # Example defaults from design doc
        defaults = [
            # System
            ("system.llm", "llm.model", "LLM Model", "string", {"value": "gpt-4-turbo"}, "system"),
            ("system.llm", "llm.temperature", "Temperature", "number", {"value": 0.7}, "system"),
            ("system.search", "search.timeout", "Search Timeout", "number", {"value": 30}, "system"),
            
            # User UI
            ("user.ui", "ui.theme", "Theme", "string", {"value": "light"}, "user"),
            ("user.ui", "ui.language", "Language", "string", {"value": "zh"}, "user"),
            ("user.ui", "ui.font_size", "Font Size", "string", {"value": "16px"}, "user"),
            
            # Agent Behavior
            ("agent.behavior", "agent.search_depth", "Search Depth", "number", {"value": 3}, "user"),
            ("agent.behavior", "agent.summary_length", "Summary Length", "string", {"value": "medium"}, "user"),

            # Search Settings (Extracted from generic)
            ("search.config", "search.enable_deep_reasoning", "Enable Deep Reasoning", "boolean", {"value": False}, "user"),
            ("search.config", "search.enable_auto_summary", "Auto Generate Summary", "boolean", {"value": True}, "user"),
            ("search.config", "search.default_sort_by", "Default Sort Order", "string", {"value": "relevance"}, "user"),
            ("search.config", "search.max_results", "Max Results Per Page", "number", {"value": 10}, "user"),
        ]
        
        for cat_code, key, name, v_type, default_val, scope in defaults:
            # Ensure Category
            category = (await self.db.exec(select(ConfigCategory).where(ConfigCategory.code == cat_code))).first()
            if not category:
                category = ConfigCategory(code=cat_code, name=cat_code)
                self.db.add(category)
                await self.db.commit()
                await self.db.refresh(category)
            
            # Ensure Definition
            definition = (await self.db.exec(select(ConfigDefinition).where(ConfigDefinition.key == key))).first()
            if not definition:
                definition = ConfigDefinition(
                    category_id=category.id,
                    key=key,
                    name=name,
                    value_type=v_type,
                    default_value=default_val, # JSONB expects dict
                    scope=scope,
                    is_public=True
                )
                self.db.add(definition)
        
        await self.db.commit()

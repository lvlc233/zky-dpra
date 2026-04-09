"""
开发者: BackendAgent
创建时间: 2026年04月09日
描述: 翻译服务，调用 LLM 进行翻译
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Tuple

from service.setting.setting_service import SettingService

class TranslateService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_llm(self, user_id: UUID) -> Tuple[ChatOpenAI, str]:
        """根据用户配置获取 LLM 实例"""
        setting_service = SettingService(self.session)
        config = await setting_service.get_effective_model_config(user_id, 'translate')
        
        # 如果未找到 translate 配置，退化使用 chat
        if not config or not config.get("api_key"):
            logger.warning("未找到 translate 的有效配置，尝试使用 chat 配置作为后备方案。")
            config = await setting_service.get_effective_model_config(user_id, 'chat')
            
        if config and config.get("api_key"):
             return ChatOpenAI(
                 model=config.get("model_name", "gpt-4o-mini"),
                 temperature=config.get("temperature", 0.0), # 翻译通常temperature设置更低
                 api_key=config.get("api_key"),
                 base_url=config.get("base_url") or None
             ), config.get("system_prompt")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统模型配置缺失，请前往管理后台配置 translate 或 chat 模型。"
        )

    async def translate_text(self, paper_id: UUID, user_id: UUID, text: str) -> str:
        llm, user_system_prompt = await self._get_llm(user_id)
        
        # 默认系统提示词
        system_prompt = user_system_prompt or "你是一个精确的翻译助手。请将用户提供的文本翻译为中文（如果原文已经是中文，请尝试将其翻译为英文）。请直接返回翻译结果，不要带任何多余的解释和说明。"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{text}")
        ])

        chain = prompt | llm
        
        try:
            response = await chain.ainvoke({"text": text})
            return response.content
        except Exception as e:
            logger.error(f"翻译生成失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Translation failed: {str(e)}"
            )

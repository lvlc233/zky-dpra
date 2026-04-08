'''
开发者: BackendAgent
当前版本: v1.2_embedding_service_pure_api
创建时间: 2026年01月08日 15:30
更新时间: 2026年04月06日 17:20
更新记录:
    [2026年01月08日 15:30:v1.0_embedding_service:创建文本向量化服务，支持OpenAI和Ollama模型]
    [2026年01月09日 16:20:v1.1_embedding_service:新增本地ONNX模型(BGE-M3)支持及SiliconFlow云端回退机制]
    [2026年04月06日 17:20:v1.2_embedding_service_pure_api:移除本地模型和复杂回退，仅保留OpenAI兼容接口，实现极简架构]
'''

from abc import ABC, abstractmethod
from typing import List, Optional

from openai import AsyncOpenAI
from loguru import logger

from base.config import settings


class BaseEmbeddingModel(ABC):
    """文本嵌入模型基类"""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """嵌入维度"""
        pass


class OpenAIEmbeddingModel(BaseEmbeddingModel):
    """OpenAI兼容接口的文本嵌入模型 (支持OpenAI, SiliconFlow, DeepSeek等)"""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: Optional[str] = None
    ):
        self.model_name = model
        self.base_url = base_url
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"OpenAI兼容嵌入模型初始化: {model}, base_url={base_url}")

    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        try:
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI文本嵌入失败: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        if not texts:
            return []
        try:
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            # 保证返回顺序与输入一致
            embeddings = [None] * len(texts)
            for data in response.data:
                embeddings[data.index] = data.embedding
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI批量嵌入失败: {e}")
            raise

    @property
    def dimension(self) -> int:
        """嵌入维度 (尝试根据模型名称猜测，或默认1024)"""
        name_lower = self.model_name.lower()
        if "bge-m3" in name_lower:
            return 1024
        if "text-embedding-3-small" in name_lower:
            return 1536
        if "text-embedding-ada-002" in name_lower:
            return 1536
        return 1024  # 默认通用维度


class EmbeddingService:
    """文本向量化服务 (仅支持 OpenAI 兼容 API)"""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        初始化嵌入服务。
        如果参数缺失，将尝试从 settings 获取默认值。
        """
        self.provider = provider or "openai"
        self.model_name = model_name or settings.openai_embedding_model
        
        # 补全配置逻辑 (如果外部未传入)
        final_model = model_name
        final_api_key = api_key
        final_base_url = base_url

        if not final_model:
            if self.provider == "siliconflow":
                final_model = settings.siliconflow_embedding_model
            else:
                final_model = "text-embedding-ada-002"
        
        if not final_api_key:
            if self.provider == "siliconflow":
                final_api_key = settings.siliconflow_api_key
            else:
                final_api_key = settings.openai_api_key

        if not final_base_url and self.provider == "siliconflow":
            final_base_url = settings.siliconflow_base_url

        if not final_api_key:
            logger.warning(f"EmbeddingService: API Key 未配置 (Provider: {self.provider})")

        self.primary_model = OpenAIEmbeddingModel(
            model=final_model,
            api_key=final_api_key,
            base_url=final_base_url
        )

    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        return await self.primary_model.embed_text(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        return await self.primary_model.embed_batch(texts)


# 辅助函数: 快捷调用
async def embed_batch(
    texts: List[str], 
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs # 忽略多余参数
) -> List[List[float]]:
    """
    极简批量向量化入口
    """
    service = EmbeddingService(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url
    )
    return await service.embed_batch(texts)

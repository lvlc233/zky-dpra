"""
开发者: LangGraphAgent
当前版本: v1.1.0
创建时间: 2026-01-25
描述: 论文检索服务，提供基于 pgvector 的混合检索 (Hybrid Search) 能力
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, or_
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from base.pg.entity import PaperChunk
from service.setting.setting_service import SettingService

class RetrievalService:
    def __init__(self, session: AsyncSession, user_id: Optional[UUID] = None):
        self.session = session
        self.user_id = user_id
        self.embeddings = None

    async def _get_embeddings_model(self) -> OpenAIEmbeddings:
        """动态获取 Embedding 模型"""
        if self.embeddings:
            return self.embeddings
            
        api_key = None
        base_url = None
        model_name = "text-embedding-3-small"
        
        # 尝试从用户配置获取
        if self.user_id:
            try:
                setting_service = SettingService(self.session)
                settings = await setting_service.get_settings(self.user_id)
                
                # 优先检查 Search Settings 中的 OpenAI 配置
                search_settings = settings.search_settings
                # 注意: SearchSetting schema 中没有 provider/api_key 字段，
                # 只有 AgentSettings 或 AIReaderSettings 有。
                # 检查 AgentSettings
                if hasattr(settings, 'agent_settings') and settings.agent_settings:
                    agent_settings = settings.agent_settings
                    if agent_settings.embedding_provider == 'openai':
                        if agent_settings.embedding_api_key:
                             api_key = agent_settings.embedding_api_key
                        if agent_settings.embedding_base_url:
                             base_url = agent_settings.embedding_base_url
                             
                # 或者检查 AIReaderSettings (fallback)
                elif hasattr(settings, 'ai_reader_settings') and settings.ai_reader_settings:
                     target_setting = next((s for s in settings.ai_reader_settings if s.provider == 'openai'), None)
                     if target_setting:
                         if target_setting.api_key:
                             api_key = target_setting.api_key
                         if target_setting.base_url:
                             base_url = target_setting.base_url

            except Exception as e:
                logger.warning(f"Failed to load user settings for embeddings: {e}")
        
        # 初始化
        # 如果 api_key 仍为 None，OpenAIEmbeddings 会尝试读取环境变量
        self.embeddings = OpenAIEmbeddings(
            model=model_name,
            api_key=api_key, 
            base_url=base_url
        )
        return self.embeddings

    async def _get_embedding(self, text: str) -> List[float]:
        model = await self._get_embeddings_model()
        return await model.aembed_query(text)

    async def retrieve_chunks(
        self, 
        paper_id: str | UUID, 
        query: str, 
        limit: int = 5,
        hybrid: bool = True
    ) -> List[Document]:
        """
        检索特定论文的片段 (混合检索策略)
        
        Args:
            paper_id: 论文 ID
            query: 用户查询
            limit: 返回数量
            hybrid: 是否开启混合检索 (Vector + Keyword)
        
        Returns:
            List[Document]: LangChain Document 对象列表
        """
        if isinstance(paper_id, str):
            paper_id = UUID(paper_id)
            
        try:
            query_embedding = await self._get_embedding(query)
            
            # 1. 向量检索 (Semantic Search)
            # 使用 cosine distance
            semantic_stmt = (
                select(PaperChunk)
                .where(PaperChunk.paper_id == paper_id)
                .order_by(PaperChunk.embedding.cosine_distance(query_embedding))
                .limit(limit * 2) # 取多一点用于 RRF
            )
            semantic_results = (await self.session.execute(semantic_stmt)).scalars().all()
            
            if not hybrid:
                return [
                    Document(
                        page_content=c.content,
                        metadata={
                            "id": str(c.id),
                            "page": c.page_number,
                            "score": 1.0 # Placeholder
                        }
                    ) for c in semantic_results[:limit]
                ]

            # 2. 关键词检索 (Keyword Search)
            # 使用 ilike 简单模拟，或者 to_tsvector 如果数据库支持
            # 这里为了通用性先用 ilike OR 匹配
            # split query into terms
            terms = query.split()
            conditions = [PaperChunk.content.ilike(f"%{term}%") for term in terms if len(term) > 1]
            
            keyword_results = []
            if conditions:
                keyword_stmt = (
                    select(PaperChunk)
                    .where(PaperChunk.paper_id == paper_id)
                    .where(or_(*conditions))
                    .limit(limit * 2)
                )
                keyword_results = (await self.session.execute(keyword_stmt)).scalars().all()
            
            # 3. RRF Fusion
            # Simple RRF: score = 1 / (k + rank)
            k = 60
            scores = {}
            
            # Process Semantic
            for rank, doc in enumerate(semantic_results):
                doc_id = doc.id
                if doc_id not in scores:
                    scores[doc_id] = {"doc": doc, "score": 0.0}
                scores[doc_id]["score"] += 1.0 / (k + rank + 1)
                
            # Process Keyword
            for rank, doc in enumerate(keyword_results):
                doc_id = doc.id
                if doc_id not in scores:
                    scores[doc_id] = {"doc": doc, "score": 0.0}
                scores[doc_id]["score"] += 1.0 / (k + rank + 1)
            
            # Sort by score
            sorted_docs = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
            
            final_chunks = [item["doc"] for item in sorted_docs[:limit]]
            
            return [
                Document(
                    page_content=c.content,
                    metadata={
                        "id": str(c.id),
                        "page": c.page_number,
                        "chunk_index": c.chunk_index
                    }
                ) for c in final_chunks
            ]
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}", exc_info=True)
            return []

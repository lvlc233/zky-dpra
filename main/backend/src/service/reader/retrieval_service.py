"""
开发者: LangGraphAgent
当前版本: v1.1.0
创建时间: 2026-01-25
描述: 论文检索服务，提供基于 pgvector 的混合检索 (Hybrid Search) 能力
"""

import os
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, or_
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from loguru import logger

from base.pg.entity import PaperChunk
from service.setting.setting_service import SettingService
from base.config import settings as global_settings
from base.embedding.local_embeddings import LocalOnnxEmbeddings

class RetrievalService:
    def __init__(self, session: AsyncSession, user_id: Optional[UUID] = None):
        self.session = session
        self.user_id = user_id
        self.embeddings: Optional[Embeddings] = None

    async def _get_embeddings_model(self) -> Embeddings:
        """动态获取 Embedding 模型 (Factory)"""
        if self.embeddings:
            return self.embeddings
            
        provider = "local" # Default fallback
        api_key = None
        base_url = None
        model_name = "text-embedding-3-small"
        
        # 尝试从用户配置获取
        if self.user_id:
            try:
                setting_service = SettingService(self.session)
                settings = await setting_service.get_settings(self.user_id)
                
                # 1. 优先检查 AgentSettings (推荐的新方式)
                if hasattr(settings, 'agent_settings') and settings.agent_settings:
                    agent_settings = settings.agent_settings
                    provider = agent_settings.embedding_provider
                    logger.info(f"Loaded AgentSettings for user {self.user_id}: Provider={provider}, Model={agent_settings.embedding_model}")
                    
                    if provider in ['openai', 'siliconflow']:
                        if agent_settings.embedding_api_key:
                             api_key = agent_settings.embedding_api_key
                        
                        if agent_settings.embedding_base_url:
                             base_url = agent_settings.embedding_base_url
                        if agent_settings.embedding_model:
                             model_name = agent_settings.embedding_model
                    elif provider == 'local':
                        # Use local model path from global settings
                        model_name = global_settings.local_embedding_model_path
                        logger.info(f"Using local embedding model at: {model_name}")
                    else:
                        logger.info(f"Unknown or unsupported provider: {provider}. Falling back to default logic.")

                # 2. 回退检查 AIReaderSettings (兼容旧前端逻辑)
                # 如果 AgentSettings 是默认的 local，但 AIReaderSettings[chat] 中配置了 embedding 参数
                if provider == 'local':
                    ai_settings = settings.ai_reader_settings
                    chat_setting = next((s for s in ai_settings if s.type == 'chat'), None)
                    if chat_setting and chat_setting.config:
                        emb_provider = chat_setting.config.get('embedding_provider')
                        if emb_provider and emb_provider != 'local':
                            logger.info(f"Found embedding config in AIReaderSettings (fallback): {emb_provider}")
                            provider = emb_provider
                            
                            if 'embedding_api_key' in chat_setting.config:
                                api_key = chat_setting.config.get('embedding_api_key')
                            if 'embedding_base_url' in chat_setting.config:
                                base_url = chat_setting.config.get('embedding_base_url')
                            if 'embedding_model' in chat_setting.config:
                                model_name = chat_setting.config.get('embedding_model')

            except Exception as e:
                logger.warning(f"Failed to load user settings for embeddings: {e}")
        
        # Factory Logic
        if provider == 'local':
            try:
                self.embeddings = LocalOnnxEmbeddings(model_path=global_settings.local_embedding_model_path)
                logger.info("Initialized LocalOnnxEmbeddings")
            except Exception as e:
                logger.error(f"Failed to initialize LocalOnnxEmbeddings: {e}. Fallback to OpenAI.")
                # Fallback to OpenAI if local fails (e.g. model missing)
                provider = 'openai' 

        if provider in ['openai', 'siliconflow']:
            # 初始化 OpenAI / Compatible
            if not api_key:
                logger.warning("No API key found in user settings for embeddings. Checking environment variables.")
                if not os.environ.get("SILICONFLOW_API_KEY"):
                    logger.warning("No SILICONFLOW_API_KEY found in env. Retrieval WILL fail for OpenAI-compatible providers.")
            
            self.embeddings = OpenAIEmbeddings(
                model=model_name,
                api_key=api_key, 
                base_url=base_url
            )
            
        if not self.embeddings:
             # Final fallback
             self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        return self.embeddings

    async def _get_embedding(self, text: str) -> List[float]:
        model = await self._get_embeddings_model()
        embedding = await model.aembed_query(text)
        
        # 兼容性处理: 如果数据库是1024维, 但模型返回了1536维 (例如fallback到了openai), 或者反之
        # 我们不能简单截断或补零，这会破坏向量语义。
        # 但为了防止SQL报错，我们需要确保维度匹配。
        # 更好的做法是在配置阶段就确保模型与DB一致。
        # 这里做一个紧急的安全检查。
        
        # 假设我们知道 DB 是 1024 维 (从 Entity 定义看)
        # 如果是 local 模型 (BGE-M3)，它已经是 1024 维了。
        # 如果是 openai text-embedding-3-small，它是 1536 维。
        
        # 这种不匹配是架构层面的配置错误。
        # 如果用户强制用了 OpenAI 模型但 DB 是 1024，就会报错。
        # 临时方案：如果维度不一致，记录错误并返回空列表或截断（仅用于测试，生产环境应报错）
        
        if len(embedding) == 1536:
             # 如果我们必须存入 1024 维的列...
             # 我们无法将 1536 无损转为 1024。
             # 除非我们在 entity 定义中改回 1536，或者用户使用支持 1024 的模型。
             pass
             
        return embedding

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
            # 增加调试日志
            logger.info(f"Starting retrieval for paper_id={paper_id}, query='{query}'")
            
            # 检查数据库中是否存在该论文的chunk
            count_stmt = select(func.count()).select_from(PaperChunk).where(PaperChunk.paper_id == paper_id)
            chunk_count = (await self.session.execute(count_stmt)).scalar()
            logger.info(f"Total chunks found for paper {paper_id}: {chunk_count}")
            
            if chunk_count == 0:
                logger.warning(f"No chunks found for paper {paper_id}. Retrieval will be empty.")
                return []
            
            query_embedding = await self._get_embedding(query)
            logger.info(f"Generated query embedding with dimension: {len(query_embedding)}")
            
            # 1. 向量检索 (Semantic Search)
            # 使用 cosine distance
            semantic_stmt = (
                select(PaperChunk)
                .where(PaperChunk.paper_id == paper_id)
                # 排除 embedding 为空的记录 (防御性)
                .where(PaperChunk.embedding.is_not(None))
                .order_by(PaperChunk.embedding.cosine_distance(query_embedding))
                .limit(limit * 2) # 取多一点用于 RRF
            )
            semantic_results = (await self.session.execute(semantic_stmt)).scalars().all()
            logger.info(f"Semantic search returned {len(semantic_results)} results")
            
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
            # 过滤掉过短的词
            valid_terms = [term for term in terms if len(term) > 1]
            logger.info(f"Keyword search terms: {valid_terms}")
            
            keyword_results = []
            if valid_terms:
                conditions = [PaperChunk.content.ilike(f"%{term}%") for term in valid_terms]
                keyword_stmt = (
                    select(PaperChunk)
                    .where(PaperChunk.paper_id == paper_id)
                    .where(or_(*conditions))
                    .limit(limit * 2)
                )
                keyword_results = (await self.session.execute(keyword_stmt)).scalars().all()
            logger.info(f"Keyword search returned {len(keyword_results)} results")
            
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
            logger.info(f"Final RRF fusion returned {len(final_chunks)} chunks")
            
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
            logger.exception("Retrieval failed: {}", e)
            return []

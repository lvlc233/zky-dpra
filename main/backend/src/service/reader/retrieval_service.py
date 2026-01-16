"""
开发者: BackendAgent
当前版本: v1.0
创建时间: 2026年01月14日
描述: 论文检索服务，负责基于向量相似度检索论文切片
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc
from loguru import logger
from langchain_core.documents import Document

from base.pg.entity import PaperChunk
from base.embedding.embedding_service import EmbeddingService

# TODO: 有点意义不明,拒绝通过。
class RetrievalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_service = EmbeddingService()

    async def retrieve_chunks(self, paper_id: UUID, query: str, limit: int = 5) -> List[Document]:
        """
        检索指定论文的相关切片
        """
        try:
            # 1. 获取查询向量
            # 注意: EmbeddingService 可能需要初始化，这里假设它内部处理了
            if not self.embedding_service.primary_model:
                # 尝试重新初始化或报错，这里简单处理
                self.embedding_service._init_models()
                
            query_embedding = await self.embedding_service.primary_model.embed_text(query)
            
            # 2. 向量检索
            # 使用 pgvector 的 cosine_distance (<=>) 操作符
            stmt = select(PaperChunk).where(
                PaperChunk.paper_id == paper_id
            ).order_by(
                PaperChunk.embedding.cosine_distance(query_embedding)
            ).limit(limit)
            
            result = await self.session.execute(stmt)
            chunks = result.scalars().all()
            
            # 3. 转换为 LangChain Document
            documents = []
            for chunk in chunks:
                doc = Document(
                    page_content=chunk.content,
                    metadata={
                        "chunk_id": str(chunk.id),
                        "paper_id": str(chunk.paper_id),
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index
                    }
                )
                documents.append(doc)
                
            return documents
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            # 降级策略: 如果向量检索失败，可以尝试简单的文本匹配或返回空
            return []

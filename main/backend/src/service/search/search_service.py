import logging
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_, and_, String

from fastapi import Depends, HTTPException, status

from base.pg.service import SessionDep
from base.pg.entity import Paper, PaperChunk, SearchHistory, User
from controller.api.search.schema import SearchRequest, SearchFilter, SearchResponse, SearchedPaperMetaResponse
from service.papers.schema import PaperMeta
from service.papers.paper_service import PaperServiceDep
from service.papers.arxiv_service import ArxivService
from common.model.enums import PaperStatus

logger = logging.getLogger(__name__)
# TODO: 相关说明已经在schema中标注了。
class SearchService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_embedding(self, text: str) -> List[float]:
        """
        获取文本向量 (Mock)
        TODO: 对接真实 Embedding 服务
        """
        import random
        # 1536 dim for OpenAI compatibility
        return [random.random() for _ in range(1536)]

    def _ensure_naive(self, dt: Optional[datetime]) -> Optional[datetime]:
        """
        Ensure datetime is naive (no timezone).
        If aware, convert to local time and strip timezone to match DB (datetime.now() behavior).
        """
        if dt is None:
            return None
        if dt.tzinfo is not None:
            return dt.astimezone(None).replace(tzinfo=None)
        return dt

    async def search_papers(
        self, 
        user_id: UUID, 
        request: SearchRequest,
        arxiv_service: Optional[ArxivService] = None
    ) -> SearchedPaperMetaResponse:
        """
        执行论文搜索
        支持文本匹配和语义搜索
        支持本地搜索和外部源搜索(arXiv)
        """
        logger.info(f"Processing search request. User: {user_id}, Query: '{request.query}', Filters: {request.filters}")

        # 0. 检查是否为外部源搜索
        is_external = False
        # 兼容旧逻辑: filters.source == 'arxiv'
        if request.filters and request.filters.source and request.filters.source.lower() == 'arxiv':
            is_external = True
        # 新逻辑: enable_web_search 开关
        if request.enable_web_search:
            is_external = True
            
        if is_external and arxiv_service and request.query:
            logger.info("Executing external search (Arxiv) as requested.")
            return await self._search_external(user_id, request, arxiv_service)

        # 1. 本地搜索 - 构建基础查询
        logger.info("Executing local search.")
        query = select(Paper).where(
            Paper.user_id == user_id,
            Paper.analysis_status != PaperStatus.FAILED.value
        )

        # 2. 语义搜索或关键词匹配
        if request.enable_semantic_search and request.query:
            embedding = await self._get_embedding(request.query)
            # 语义搜索: 查找最相似的 Chunk 所属的 Paper
            # 注意: 这里逻辑简化，直接 Join 并按距离排序
            # 真实场景可能需要先筛选 Chunk 再聚合 Paper
            query = query.join(PaperChunk).order_by(
                PaperChunk.embedding.cosine_distance(embedding)
            )
            # 由于一对多，需要去重。但 distinct 与 order_by 冲突处理较麻烦
            # 这里简单处理: 不去重，直接返回 Chunk 对应的 Paper (可能会有重复)，
            # 或者在应用层去重。
            # 为了演示，我们假设只返回最相关的一个 Chunk 对应的 Paper 列表 (可能会重复)
            # 更好的做法是 subquery
        elif request.query:
            # 关键词匹配
            search_term = f"%{request.query}%"
            
            # 构建 OR 条件列表
            conditions = []
            
            # 默认必须匹配至少一个字段，如果没有指定任何 match_*，则默认匹配标题和摘要
            # 但前端通常会传默认值
            
            if request.match_title:
                conditions.append(Paper.title.ilike(search_term))
            
            # TODO: Author is JSON array, ilike might not work directly on JSONB in all PGs or ORMs easily without cast
            # assuming authors is stored as JSON/JSONB. casting to text for search.
            if request.match_author:
                # 简单处理: cast authors to text
                conditions.append(func.cast(Paper.authors, String).ilike(search_term))
                
            if request.match_abstract and Paper.summary:
                conditions.append(Paper.summary.ilike(search_term))
                
            if request.match_source:
                conditions.append(Paper.source.ilike(search_term))
            
            # 如果没有启用任何匹配，兜底匹配标题
            if not conditions:
                 conditions.append(Paper.title.ilike(search_term))
            
            query = query.where(or_(*conditions))
            
            query = query.order_by(desc(Paper.created_at))
        else:
             # 无关键词，默认按时间倒序
             query = query.order_by(desc(Paper.created_at))

        # 3. 应用高级过滤器 (Common)
        # 优先使用 published_at 进行时间过滤，如果 published_at 为空则使用 created_at
        
        # 3.1 处理 filters 中的日期 (通常来自搜索栏)
        if request.filters:
            start_date = self._ensure_naive(request.filters.start_date)
            end_date = self._ensure_naive(request.filters.end_date)
            
            if start_date:
                query = query.where(
                    or_(
                        Paper.published_at >= start_date,
                        and_(Paper.published_at == None, Paper.created_at >= start_date)
                    )
                )
            if end_date:
                query = query.where(
                    or_(
                        Paper.published_at <= end_date,
                        and_(Paper.published_at == None, Paper.created_at <= end_date)
                    )
                )
            if request.filters.status:
                # 兼容旧数据的状态查询
                status_val = request.filters.status.value
                if status_val == PaperStatus.PENDING.value:
                    query = query.where(Paper.analysis_status.in_(['pending', 'unprocessed']))
                elif status_val == PaperStatus.COMPLETED.value:
                    query = query.where(Paper.analysis_status.in_(['completed', 'processed']))
                elif status_val == PaperStatus.FAILED.value:
                    query = query.where(Paper.analysis_status.in_(['failed', 'error']))
                else:
                    query = query.where(Paper.analysis_status == status_val)

        # 3.2 处理 Settings 中的日期 (min_date/max_date)
        min_date = self._ensure_naive(request.min_date)
        max_date = self._ensure_naive(request.max_date)
        
        if min_date:
             query = query.where(
                or_(
                    Paper.published_at >= min_date,
                    and_(Paper.published_at == None, Paper.created_at >= min_date)
                )
            )
        if max_date:
             query = query.where(
                or_(
                    Paper.published_at <= max_date,
                    and_(Paper.published_at == None, Paper.created_at <= max_date)
                )
            )
        
        # 应用 match_analysis_status 过滤
        if request.match_analysis_status:
            # 统一处理新旧状态映射
            target_status = request.match_analysis_status
            if target_status == 'unprocessed' or target_status == PaperStatus.PENDING.value:
                query = query.where(Paper.analysis_status.in_(['pending', 'unprocessed']))
            elif target_status == 'processed' or target_status == PaperStatus.COMPLETED.value:
                query = query.where(Paper.analysis_status.in_(['completed', 'processed']))
            elif target_status == 'error' or target_status == PaperStatus.FAILED.value:
                query = query.where(Paper.analysis_status.in_(['failed', 'error']))
            else:
                query = query.where(Paper.analysis_status == target_status)

        # 4. 计算总数 (Simplified for semantic search performance)
        # count_stmt = select(func.count()).select_from(query.subquery())
        # total = (await self.session.execute(count_stmt)).scalar_one()
        # 暂且简单处理 total，如果是语义搜索，total 可能不准确或者是 limit
        total = 0 
        
        # 5. 分页与执行
        if not request.enable_semantic_search:
             # 非语义搜索计算 Total
             count_stmt = select(func.count()).select_from(query.subquery())
             total = (await self.session.execute(count_stmt)).scalar_one()
             
             query = query.offset((request.page - 1) * request.limit).limit(request.limit)
             result = await self.session.execute(query)
             papers = result.scalars().all()
        else:
             # 语义搜索分页
             # 直接 limit (语义搜索通常是 TopK)
             query = query.limit(request.limit).offset((request.page - 1) * request.limit)
             result = await self.session.execute(query)
             papers = result.scalars().all()
             # 去重 (保持顺序)
             seen = set()
             unique_papers = []
             for p in papers:
                 if p.id not in seen:
                     unique_papers.append(p)
                     seen.add(p.id)
             papers = unique_papers
             total = len(papers) # Mock total for semantic search

        # 6. 记录搜索历史
        query_id = await self._save_search_history(user_id, request, total)

        # 转换 convert to PaperMeta
        items = []
        for p in papers:
            items.append(PaperMeta(
                paper_id=p.id,
                url=None, # TODO: generate url
                title=p.title,
                authors=p.authors if p.authors else [],
                summary=p.summary,
                published_at=p.published_at if p.published_at else p.created_at,
                source=p.source if p.source else 'local',
                tags=[],
                references_number=None,
                is_bookmarked=True
            ))

        # Fallback to Arxiv if local search is empty and source is not explicitly 'local'
        if total == 0 and (not request.filters or not request.filters.source) and arxiv_service and request.query:
            logger.info("Local search returned 0 results and source not strictly 'local'. Falling back to Arxiv.")
            return await self._search_external(user_id, request, arxiv_service)

        return SearchedPaperMetaResponse(
            total=total,
            items=items,
            query_id=query_id
        )

    async def _search_external(self, user_id: UUID, request: SearchRequest, arxiv_service: ArxivService) -> SearchedPaperMetaResponse:
        """Helper method for external search"""
        
        # Build query with field filters (ti, au, abs)
        query_parts = []
        base_query = request.query
        
        # If no specific field is selected, search all (default behavior)
        # Or if all are selected, search all?
        # Typically if user selects "Title" only, we use ti:query
        # If "Title" and "Author", we use (ti:query OR au:query)
        
        field_conditions = []
        if request.match_title:
            field_conditions.append(f"ti:{base_query}")
        if request.match_author:
            field_conditions.append(f"au:{base_query}")
        if request.match_abstract:
            field_conditions.append(f"abs:{base_query}")
            
        # If specific fields are selected, join them with OR
        if field_conditions:
            # Wrap in parens if multiple
            if len(field_conditions) > 1:
                content_query = f"({' OR '.join(field_conditions)})"
            else:
                content_query = field_conditions[0]
        else:
            # Fallback to all fields if none selected (though frontend usually defaults to all)
            content_query = f"all:{base_query}"

        # Apply Date Filters
        final_query = content_query
        if request.min_date or request.max_date:
            # Format: YYYYMMDDHHMM
            min_str = request.min_date.strftime("%Y%m%d%H%M") if request.min_date else "190001010000"
            max_str = request.max_date.strftime("%Y%m%d%H%M") if request.max_date else "209912312359"
            
            # Append date filter with AND
            final_query = f"{final_query} AND submittedDate:[{min_str} TO {max_str}]"
            
        logger.info(f"Constructed ArXiv query: {final_query}")

        start = (request.page - 1) * request.limit
        results, total_count = await arxiv_service.search_papers(final_query, start=start, max_results=request.limit)
        
        # Check if papers exist locally
        source_refs = []
        titles = []
        for p in results:
            if p.paper_url:
                 # Extract ID from last part of URL (e.g. http://arxiv.org/abs/2103.00020v1)
                 parts = p.paper_url.split('/')
                 if parts:
                     source_refs.append(parts[-1])
                     # Also try without version if possible
            elif p.source_id:
                source_refs.append(p.source_id)
                
            titles.append(p.title)
            
        existing_map = {} # key: source_ref or title, value: paper_id
        
        if source_refs or titles:
            conditions = []
            if source_refs:
                conditions.append(Paper.source_ref.in_(source_refs))
            if titles:
                 conditions.append(Paper.title.in_(titles))
            
            if conditions:
                stmt = select(Paper.id, Paper.source_ref, Paper.title).where(
                    Paper.user_id == user_id,
                    or_(*conditions)
                )
                db_results = await self.session.execute(stmt)
                for row in db_results:
                    p_id, p_ref, p_title = row
                    if p_ref:
                        existing_map[p_ref] = p_id
                    if p_title:
                        existing_map[p_title] = p_id

        items = []
        for p in results:
            arxiv_id = None
            if p.paper_url:
                arxiv_id = p.paper_url.split('/')[-1]
            elif p.source_id:
                arxiv_id = p.source_id

            existing_id = existing_map.get(arxiv_id) or existing_map.get(p.title)

            items.append(PaperMeta(
                paper_id=existing_id, 
                url=p.pdf_url,
                title=p.title,
                authors=p.authors,
                summary=p.abstract,
                published_at=p.published_date,
                source='arXiv',
                tags=p.categories,
                references_number=None,
                is_bookmarked=True if existing_id else False
            ))
        
        # 记录历史
        await self._save_search_history(user_id, request, len(items))
        
        return SearchedPaperMetaResponse(
            items=items,
            total=total_count,
            query_id=None 
        )

    async def _save_search_history(self, user_id: UUID, request: SearchRequest, total: int) -> Optional[UUID]:
        try:
            history = SearchHistory(
                user_id=user_id,
                query=request.query, 
                filters=request.filters.model_dump() if request.filters else None,
                # result_count removed as it is not in Entity
            )
            self.session.add(history)
            await self.session.commit()
            await self.session.refresh(history)
            return history.id
        except Exception as e:
            logger.error(f"Failed to save search history: {e}")
            return None

    async def get_search_history(
        self, 
        user_id: UUID, 
        limit: int = 10
    ) -> List[SearchHistory]:
        """获取最近搜索历史"""
        stmt = select(SearchHistory).where(
            SearchHistory.user_id == user_id
        ).order_by(desc(SearchHistory.created_at)).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def clear_search_history(self, user_id: UUID) -> int:
        """清空搜索历史"""
        # delete 语句
        from sqlalchemy import delete
        stmt = delete(SearchHistory).where(SearchHistory.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount


async def get_search_service(session: SessionDep) -> SearchService:
    return SearchService(session)

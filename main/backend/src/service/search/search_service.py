import logging
from typing import List, Optional, Tuple, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_, and_, String

from fastapi import Depends, HTTPException, status

from base.pg.service import SessionDep, SearchApiConfigRepository, JobRepository
from base.pg.entity import Paper, PaperChunk, SearchHistory, SearchApiConfig
from controller.api.search.schema import SearchRequest, SearchedPaperMetaResponse
from service.papers.schema import PaperMeta, PaperInfo
from service.papers.arxiv_service import ArxivService
from base.arxiv.client import ArxivClient
from base.arxiv.parser import ArxivXmlParser
from service.papers.semantic_scholar_service import SemanticScholarProvider
from service.papers.crossref_service import CrossrefProvider
from service.papers.open_alex_service import OpenAlexProvider
from service.papers.core_service import CoreProvider
from service.setting.schema import SearchApiConfigInfo
from common.model.enums import PaperStatus

logger = logging.getLogger(__name__)
# TODO: 相关说明已经在schema中标注了。
class SearchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.providers = {
            "arXiv": ArxivService(ArxivClient(), ArxivXmlParser()),
            "Semantic Scholar": SemanticScholarProvider(),
            "Crossref": CrossrefProvider(),
            "OpenAlex": OpenAlexProvider(),
            "CORE": CoreProvider()
        }

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
        api_configs: List[SearchApiConfigInfo] = None
    ) -> SearchedPaperMetaResponse:
        """
        执行论文搜索
        支持文本匹配和语义搜索
        支持本地搜索和外部源搜索的平滑合并
        """
        logger.info(f"Processing search request. User: {user_id}, Query: '{request.query}', Filters: {request.filters}")

        # 0. 获取配置 (用于可能的外部搜索)
        if not api_configs and request.enable_web_search:
            db_configs = await SearchApiConfigRepository.get_active_configs(self.session)
            api_configs = [
                SearchApiConfigInfo(
                    api_name=c.api_name,
                    api_key=c.api_key,
                    weight=c.weight,
                    is_active=c.is_active
                ) for c in db_configs
            ]

        # 1. 本地搜索 - 构建基础查询
        logger.info("Executing local search.")
        local_query = select(Paper).where(
            Paper.user_id == user_id,
            Paper.analysis_status != PaperStatus.FAILED.value
        )

        # 2. 语义搜索或关键词匹配
        if request.enable_semantic_search and request.query:
            embedding = await self._get_embedding(request.query)
            local_query = local_query.join(PaperChunk).order_by(
                PaperChunk.embedding.cosine_distance(embedding)
            )
        elif request.query:
            # 关键词匹配
            search_term = f"%{request.query}%"
            conditions = []
            
            if request.match_title:
                conditions.append(Paper.title.ilike(search_term))
            if request.match_author:
                conditions.append(func.cast(Paper.authors, String).ilike(search_term))
            if request.match_abstract and Paper.summary:
                conditions.append(Paper.summary.ilike(search_term))
            if request.match_source:
                conditions.append(Paper.source.ilike(search_term))
            
            if not conditions:
                 conditions.append(Paper.title.ilike(search_term))
            
            local_query = local_query.where(or_(*conditions))
            local_query = local_query.order_by(desc(Paper.created_at))
        else:
             # 无关键词，默认按时间倒序
             local_query = local_query.order_by(desc(Paper.created_at))

        # 3. 应用高级过滤器
        if request.filters:
            start_date = self._ensure_naive(request.filters.start_date)
            end_date = self._ensure_naive(request.filters.end_date)
            
            if start_date:
                local_query = local_query.where(
                    or_(
                        Paper.published_at >= start_date,
                        and_(Paper.published_at == None, Paper.created_at >= start_date)
                    )
                )
            if end_date:
                local_query = local_query.where(
                    or_(
                        Paper.published_at <= end_date,
                        and_(Paper.published_at == None, Paper.created_at <= end_date)
                    )
                )
            if request.filters.status:
                status_val = request.filters.status.value
                if status_val == PaperStatus.PENDING.value:
                    local_query = local_query.where(Paper.analysis_status.in_(['pending', 'unprocessed']))
                elif status_val == PaperStatus.COMPLETED.value:
                    local_query = local_query.where(Paper.analysis_status.in_(['completed', 'processed']))
                elif status_val == PaperStatus.FAILED.value:
                    local_query = local_query.where(Paper.analysis_status.in_(['failed', 'error']))
                else:
                    local_query = local_query.where(Paper.analysis_status == status_val)

        min_date = self._ensure_naive(request.min_date)
        max_date = self._ensure_naive(request.max_date)
        
        if min_date:
             local_query = local_query.where(
                or_(
                    Paper.published_at >= min_date,
                    and_(Paper.published_at == None, Paper.created_at >= min_date)
                )
            )
        if max_date:
             local_query = local_query.where(
                or_(
                    Paper.published_at <= max_date,
                    and_(Paper.published_at == None, Paper.created_at <= max_date)
                )
            )
        
        if request.match_analysis_status:
            target_status = request.match_analysis_status
            if target_status == 'unprocessed' or target_status == PaperStatus.PENDING.value:
                local_query = local_query.where(Paper.analysis_status.in_(['pending', 'unprocessed']))
            elif target_status == 'processed' or target_status == PaperStatus.COMPLETED.value:
                local_query = local_query.where(Paper.analysis_status.in_(['completed', 'processed']))
            elif target_status == 'error' or target_status == PaperStatus.FAILED.value:
                local_query = local_query.where(Paper.analysis_status.in_(['failed', 'error']))
            else:
                local_query = local_query.where(Paper.analysis_status == target_status)

        # 4. 执行本地查询与分页
        local_total = 0
        local_papers = []
        if not request.enable_semantic_search:
             count_stmt = select(func.count()).select_from(local_query.subquery())
             local_total = (await self.session.execute(count_stmt)).scalar_one()
             
             local_offset_query = local_query.offset((request.page - 1) * request.limit).limit(request.limit)
             local_result = await self.session.execute(local_offset_query)
             local_papers = list(local_result.scalars().all())
        else:
             # 语义搜索
             local_offset_query = local_query.limit(request.limit).offset((request.page - 1) * request.limit)
             local_result = await self.session.execute(local_offset_query)
             local_papers = list(local_result.scalars().all())
             # 去重 (保持顺序)
             seen = set()
             unique_papers = []
             for p in local_papers:
                 if p.id not in seen:
                     unique_papers.append(p)
                     seen.add(p.id)
             local_papers = unique_papers
             local_total = len(local_papers)

        # 5. 如果启用了网络搜索，则调用外部搜索并合并
        if request.enable_web_search and request.query:
             logger.info("Executing merged external search.")
             external_response = await self._search_external(user_id, request, api_configs or [])
             
             # 合并逻辑：
             # 1. 以本地结果为基础。
             # 2. 将外部结果映射到 PaperMeta，并排除那些已经存在于本地结果中的记录。
             
             items = []
             local_ids = set()
             local_titles = set()
             for p in local_papers:
                 local_ids.add(p.id)
                 local_titles.add(p.title.lower().strip())
                 
                 job_id = None
                 try:
                     job = await JobRepository.get_latest_job_by_paper_id(self.session, p.id)
                     if job: job_id = str(job.id)
                 except: pass

                 items.append(PaperMeta(
                    paper_id=p.id,
                    url=None,
                    title=p.title,
                    authors=p.authors if p.authors else [],
                    summary=p.summary,
                    published_at=p.published_at if p.published_at else p.created_at,
                    uploaded_at=p.created_at,
                    source=p.source if p.source else 'local',
                    tags=[],
                    references_number=None,
                    is_bookmarked=True,
                    status=p.analysis_status,
                    job_id=job_id,
                    source_id=p.source_ref
                 ))

             # 合并外部结果 (排除重复)
             for ext_item in external_response.items:
                 ext_title = ext_item.title.lower().strip()
                 if ext_title in local_titles:
                     continue
                 if ext_item.paper_id and ext_item.paper_id in local_ids:
                     continue
                 
                 items.append(ext_item)

             items = items[:request.limit]
             
             return SearchedPaperMetaResponse(
                 total=local_total + external_response.total,
                 items=items,
                 query_id=None,
                 message=external_response.message
             )

        # 6. 仅本地搜索的转换逻辑
        items = []
        for p in local_papers:
            job_id = None
            try:
                job = await JobRepository.get_latest_job_by_paper_id(self.session, p.id)
                if job: job_id = str(job.id)
            except: pass

            items.append(PaperMeta(
                paper_id=p.id,
                url=None,
                title=p.title,
                authors=p.authors if p.authors else [],
                summary=p.summary,
                published_at=p.published_at if p.published_at else p.created_at,
                uploaded_at=p.created_at,
                source=p.source if p.source else 'local',
                tags=[],
                references_number=None,
                is_bookmarked=True,
                status=p.analysis_status,
                job_id=job_id,
                source_id=p.source_ref
            ))

        # 7. 记录搜索历史并返回
        query_id = await self._save_search_history(user_id, request, local_total)

        return SearchedPaperMetaResponse(
            total=local_total,
            items=items,
            query_id=query_id,
            message=None
        )

    async def _search_external(
        self, 
        user_id: UUID, 
        request: SearchRequest, 
        api_configs: List[SearchApiConfigInfo]
    ) -> SearchedPaperMetaResponse:
        """Helper method for external search with multi-datasource fallback."""
        
        base_query = request.query
        start = (request.page - 1) * request.limit

        # 排序所有可用的并且是开启状态的 API 配置，按照权限(权重)倒序
        active_configs = [c for c in api_configs if c.is_active]
        active_configs.sort(key=lambda c: c.weight, reverse=True)

        if not active_configs:
            logger.warning("外部搜索开启，但系统没有配置任何活跃的 Search API。")
            return SearchedPaperMetaResponse(
                total=0, 
                items=[], 
                query_id=None,
                message="外部搜索开启，但系统没有配置任何活跃的 Search API。请联系管理员配置后重试。"
            )

        results_with_source: List[Tuple[PaperInfo, str]] = []
        total_count = 0
        errors = []  # 收集各提供商的错误信息
        
        for config in active_configs:
            provider = self.providers.get(config.api_name)
            if not provider:
                logger.warning(f"跳过未知的搜索服务提供商: {config.api_name}")
                continue
                
            logger.info(f"尝试使用外部 API 进行搜索: {provider.api_name} (权重={config.weight})")
            
            # 适配不同 provider 的查询语法可以在 Provider 实现里做。这里透传。
            final_query = base_query
            if provider.api_name == "arXiv":
                field_conditions = []
                if request.match_title: field_conditions.append(f"ti:{base_query}")
                if request.match_author: field_conditions.append(f"au:{base_query}")
                if request.match_abstract: field_conditions.append(f"abs:{base_query}")
                final_query = f"({' OR '.join(field_conditions)})" if len(field_conditions) > 1 else (field_conditions[0] if field_conditions else f"all:{base_query}")
                if request.min_date or request.max_date:
                    min_str = request.min_date.strftime("%Y%m%d%H%M") if request.min_date else "190001010000"
                    max_str = request.max_date.strftime("%Y%m%d%H%M") if request.max_date else "209912312359"
                    final_query = f"{final_query} AND submittedDate:[{min_str} TO {max_str}]"
            
            try:
                p_results, p_total = await provider.search_papers(
                    query=final_query, 
                    start=start, 
                    max_results=request.limit,
                    api_key=config.api_key
                )
                if p_results:
                    logger.info(f"使用 API '{provider.api_name}' 成功获取 {len(p_results)} 条记录。")
                    for p in p_results:
                        results_with_source.append((p, provider.api_name))
                    total_count += p_total
                
                # 如果已经获取了足够的搜索结果，可以考虑不再请求后续低优先级的 API 以节省资源
                if len(results_with_source) >= request.limit:
                    break
                    
            except Exception as e:
                error_msg = f"{provider.api_name}: {str(e)}"
                logger.error(f"API '{provider.api_name}' 发生错误: {str(e)}")
                errors.append(error_msg)
                continue
        
        # Check if papers exist locally
        source_refs = []
        titles = []
        for p, _ in results_with_source:
            if p.paper_url:
                 parts = p.paper_url.split('/')
                 if parts:
                     source_refs.append(parts[-1])
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
                stmt = select(Paper.id, Paper.source_ref, Paper.title, Paper.analysis_status).where(
                    Paper.user_id == user_id,
                    or_(*conditions)
                )
                db_results = await self.session.execute(stmt)
                for row in db_results:
                    p_id, p_ref, p_title, p_status = row
                    # 尝试获取该论文的最相关主任务
                    p_job_id = None
                    try:
                        job = await JobRepository.get_latest_job_by_paper_id(self.session, p_id)
                        if job: p_job_id = str(job.id)
                    except: pass
                        
                    data = {"id": p_id, "status": p_status, "job_id": p_job_id}
                    if p_ref:
                        existing_map[p_ref] = data
                    if p_title:
                        existing_map[p_title] = data

        items = []
        for p, p_source in results_with_source:
            arxiv_id = None
            if p.paper_url:
                arxiv_id = p.paper_url.split('/')[-1]
            elif p.source_id:
                arxiv_id = p.source_id

            existing_data = existing_map.get(arxiv_id) or existing_map.get(p.title)
            existing_id = existing_data["id"] if existing_data else None

            # Ensure published_at is datetime
            pb_date = p.published_date
            if isinstance(pb_date, str):
                try:
                    if len(pb_date) >= 10: pb_date = datetime.strptime(pb_date[:10], "%Y-%m-%d")
                    elif len(pb_date) == 7: pb_date = datetime.strptime(pb_date, "%Y-%m")
                    elif len(pb_date) == 4: pb_date = datetime.strptime(pb_date, "%Y")
                    else: pb_date = None
                except: pb_date = None

            items.append(PaperMeta(
                paper_id=existing_id, 
                url=p.pdf_url or p.paper_url,
                title=p.title,
                authors=p.authors,
                summary=p.abstract,
                published_at=pb_date,
                uploaded_at=None,
                source=p_source,
                tags=p.categories,
                references_number=None,
                is_bookmarked=True if existing_id else False,
                status=existing_data["status"] if existing_data else None,
                job_id=existing_data["job_id"] if existing_data else None,
                source_id=arxiv_id
            ))
        
        # 如果搜不到结果且有错误发生，则汇总错误信息
        message = None
        if not items and errors:
            message = "搜索源请求失败: " + " | ".join(errors)

        # 分页总数封顶策略
        FINAL_TOTAL_CAP = 1000
        effective_total = min(total_count, FINAL_TOTAL_CAP)
        if total_count < FINAL_TOTAL_CAP:
            effective_total = total_count

        return SearchedPaperMetaResponse(
            items=items,
            total=effective_total,
            query_id=None,
            message=message
        )

    async def _save_search_history(self, user_id: UUID, request: SearchRequest, total: int) -> Optional[UUID]:
        try:
            history = SearchHistory(
                user_id=user_id,
                query=request.query, 
                filters=request.filters.model_dump() if request.filters else None,
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
        from sqlalchemy import delete
        stmt = delete(SearchHistory).where(SearchHistory.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount


async def get_search_service(session: SessionDep) -> SearchService:
    return SearchService(session)

import json
from typing import List, Optional, Annotated, Dict
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from base.pg.entity import Paper, Note, MindMap, AgentSession, Job, PaperSummary, Annotation as AnnotationEntity
from base.pg.service import SessionDep, ReaderRepository, PaperRepository
from service.reader.schema import (
    Toc, TocItem, NoteMeta, AISummary, Record,
    Job as JobSchema, Rect, Annotation, MindMap as MindMapSchema,
    MindMapNode, MindMapEdge, PaperReaderMeta, AnnotationRequest
)


from service.reader.job_service import JobService

class ReaderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_service = JobService(session)

    async def get_paper_meta(self, paper_id: UUID, user_id: UUID) -> PaperReaderMeta:
        # 1. Fetch Paper with relationships
        stmt = (
            select(Paper)
            .where(Paper.id == paper_id, Paper.user_id == user_id)
            .options(
                selectinload(Paper.annotations),
                selectinload(Paper.notes),
                selectinload(Paper.summaries),
                selectinload(Paper.mind_map),
                selectinload(Paper.chat_sessions),
            )
        )
        result = await self.session.execute(stmt)
        paper = result.scalar_one_or_none()

        if not paper:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

        # 2. Fetch Jobs separately (no relationship in entity)
        stmt_jobs = select(Job).where(Job.paper_id == paper_id).order_by(Job.created_at.desc())
        result_jobs = await self.session.execute(stmt_jobs)
        jobs_entities = result_jobs.scalars().all()

        # Check and trigger parse_text job if needed
        # Condition: Paper is unprocessed/pending, and no active parse_text job exists
        active_parse_job = next(
            (j for j in jobs_entities if j.type == 'parse_text' and j.status in ['queued', 'running']),
            None
        )
        has_completed_parse_job = any(
            j.type == 'parse_text' and j.status == 'succeeded'
            for j in jobs_entities
        )
        
        # 1. 自动触发：如果没有 active 且没有 completed
        if not active_parse_job and not has_completed_parse_job:
            from controller.api.reader.schema import JobCreateRequest
            try:
                # Trigger parse_text
                await self.job_service.create_job(
                    paper_id, 
                    JobCreateRequest(job_type='parse_text'), 
                    user_id
                )
                # Refresh jobs list
                result_jobs = await self.session.execute(stmt_jobs)
                jobs_entities = result_jobs.scalars().all()
            except Exception as e:
                print(f"Failed to auto-trigger parse_text job: {e}")
        
        # 2. 自动恢复：如果有 active 任务 (queued/running)，但可能因为 Worker 重启或未启动而卡住
        # 策略：如果任务处于 queued 状态超过 30 秒，或者 running 但很久没更新（这里暂只处理 queued），
        # 且我们知道用户正在请求该页面，那么重新 enqueue 一次是安全的（Arq 幂等）。
        # 简单起见，只要有 active_parse_job，我们就尝试 re-enqueue，确保它在 Redis 中。
        elif active_parse_job:
            try:
                # 只有当它是 queued 时才 re-enqueue，或者 running 但没有心跳？
                # running 状态比较复杂，可能是真的在跑。如果 worker 死掉，running 状态不会变。
                # 但这里主要解决 "worker 后启动" 的问题，此时状态应该是 queued（如果入队成功但没消费）
                # 或者根本没入队成功（如果当时 redis 挂了）。
                # 重新入队是低成本且安全的。
                await self.job_service.re_enqueue_job(active_parse_job.id)
            except Exception as e:
                print(f"Failed to auto-recover active job: {e}")


        # 3. Construct Response
        
        # TOC
        toc = None
        if paper.toc:
            try:
                # PyMuPDF TOC 格式: [[lvl, title, page], ...]
                # TocItem Schema: title: str, page: int
                # 需要转换格式
                toc_items = []
                for item in paper.toc:
                    if isinstance(item, list) and len(item) >= 3:
                        # PyMuPDF 格式
                        toc_items.append(TocItem(title=item[1], page=item[2]))
                    elif isinstance(item, dict):
                        # 已经是字典格式 (可能是前端上传或其他解析器)
                        toc_items.append(TocItem(**item))
                
                if toc_items:
                    toc = Toc(items=toc_items)
            except Exception as e:
                print(f"Failed to parse TOC: {e}")
                toc = None

        # Annotations
        annotations = []
        for ann in paper.annotations:
            # Parse rects (List[dict] -> List[Rect])
            rects_list = []
            if ann.rects:
                for r in ann.rects:
                    try:
                        # Compatibility for page_index vs pageIndex
                        if 'page_index' in r and 'pageIndex' not in r:
                            r['pageIndex'] = r.get('page_index')
                        
                        rects_list.append(Rect(**r))
                    except:
                        pass
            
            annotations.append(Annotation(
                id=ann.id,
                type=ann.type,
                rects=rects_list,
                content=ann.content,
                color=ann.color
            ))

        # Notes
        notes_meta = []
        for note in paper.notes:
            notes_meta.append(NoteMeta(
                id=note.id,
                title=note.title,
                page=note.page,
                created_at=note.created_at
            ))

        # AI Summary
        # Entity PaperSummary: summary_type, content.
        # Schema AISummary: summary_config: Dict[str, str]
        summary_config = {}
        for s in paper.summaries:
            # 兼容旧数据: ai_summary -> summary
            key = "summary" if s.summary_type == "ai_summary" else s.summary_type
            summary_config[key] = s.content
        ai_summary = AISummary(summary_config=summary_config) if summary_config else None

        # Mind Map
        mind_map = None
        if paper.mind_map:
            # Assuming graph_data has "nodes" and "edges" keys with lists
            gd = paper.mind_map.graph_data or {}
            nodes = [MindMapNode(**n) for n in gd.get("nodes", [])]
            edges = [MindMapEdge(**e) for e in gd.get("edges", [])]
            mind_map = MindMapSchema(nodes=nodes, edges=edges)

        # History (AgentSessions)
        history = []
        for session in paper.chat_sessions:
            history.append(Record(
                id=session.id,
                title=session.title, # Added to entity
                created_at=session.created_at,
                updated_at=session.updated_at
            ))

        # Jobs
        jobs_dto = []
        for job in jobs_entities:
            # Parse result if needed, or leave None. Schema has JobResult.
            # Job entity has result_ref (str). If we store JSON in payload or result_ref is ID, handling might differ.
            # For now, we assume simple mapping.
            # Schema Job has 'result': JobResult. Entity has 'result_ref': str.
            # We'll leave result as None for list view usually, or try to parse if payload has it.
            # Spec: result: JobResult|None=None.
            jobs_dto.append(JobSchema(
                id=job.id,
                job_type=job.type,
                status=job.status,
                progress=float(job.progress) / 100.0 if job.progress is not None else 0.0,
                stage=job.stage,
                error_message=job.error_message,
                created_at=job.created_at,
                completed_at=job.completed_at,
                result=None # TODO: Implement result parsing logic
            ))

        return PaperReaderMeta(
            paper_id=paper.id,
            file_url=paper.file_url,
            summary=ai_summary,
            toc=toc,
            annotations=annotations,
            notes=notes_meta,
            mind_map=mind_map,
            history=history,
            jobs=jobs_dto
        )

    async def get_annotations(self, paper_id: UUID, user_id: UUID) -> List[Annotation]:
        annotations = await ReaderRepository.get_annotations_by_paper(self.session, paper_id, user_id)
        
        result = []
        for ann in annotations:
            rects_list = []
            if ann.rects:
                for r in ann.rects:
                    try:
                        # Compatibility for page_index vs pageIndex
                        if 'page_index' in r and 'pageIndex' not in r:
                            r['pageIndex'] = r.get('page_index')

                        rects_list.append(Rect(**r))
                    except:
                        pass
            
            result.append(Annotation(
                id=ann.id,
                type=ann.type,
                rects=rects_list,
                content=ann.content,
                color=ann.color
            ))
        return result

    async def add_annotation(self, paper_id: UUID, req: AnnotationRequest, user_id: UUID) -> None:
        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        if not paper or paper.user_id != user_id:
             raise HTTPException(status_code=404, detail="Paper not found")
             
        annotation = AnnotationEntity(
            id=req.id if req.id else uuid4(),
            paper_id=paper_id,
            type=req.type,
            rects=[r for r in req.rects], 
            content=req.content,
            color=req.color
        )
        await ReaderRepository.create_annotation(self.session, annotation)

    async def update_annotation(self, paper_id: UUID, annotation_id: UUID, req: AnnotationRequest, user_id: UUID) -> None:
        annotation = await ReaderRepository.get_annotation_by_id(self.session, annotation_id)
        if not annotation:
             raise HTTPException(status_code=404, detail="Annotation not found")
        
        if annotation.paper_id != paper_id:
             raise HTTPException(status_code=400, detail="Annotation does not belong to this paper")

        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        if not paper or paper.user_id != user_id:
             raise HTTPException(status_code=403, detail="Permission denied")

        annotation.type = req.type
        annotation.rects = [r for r in req.rects]
        annotation.content = req.content
        annotation.color = req.color
        
        await ReaderRepository.update_annotation(self.session, annotation)

    async def delete_annotation(self, paper_id: UUID, annotation_id: UUID, user_id: UUID) -> None:
        annotation = await ReaderRepository.get_annotation_by_id(self.session, annotation_id)
        if not annotation:
             raise HTTPException(status_code=404, detail="Annotation not found")
             
        if annotation.paper_id != paper_id:
             raise HTTPException(status_code=400, detail="Annotation does not belong to this paper")

        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        if not paper or paper.user_id != user_id:
             raise HTTPException(status_code=403, detail="Permission denied")
             
        await ReaderRepository.delete_annotation(self.session, annotation)

def get_reader_service(session: SessionDep) -> ReaderService:
    return ReaderService(session)

ReaderServiceDep = Annotated[ReaderService, Depends(get_reader_service)]

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


class ReaderService:
    def __init__(self, session: AsyncSession):
        self.session = session
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
        stmt_jobs = select(Job).where(Job.paper_id == paper_id)
        result_jobs = await self.session.execute(stmt_jobs)
        jobs_entities = result_jobs.scalars().all()

        # 3. Construct Response
        
        # TOC
        toc = None
        if paper.toc:
            # Assuming paper.toc is List[dict] matching TocItem structure or close to it
            try:
                toc_items = [TocItem(**item) for item in paper.toc]
                toc = Toc(items=toc_items)
            except Exception:
                toc = None # Handle parsing error or empty

        # Annotations
        annotations = []
        for ann in paper.annotations:
            # Parse rects (List[dict] -> List[Rect])
            rects_list = []
            if ann.rects:
                for r in ann.rects:
                    try:
                        rects_list.append(Rect(**r))
                    except:
                        pass
            
            annotations.append(Annotation(
                id=ann.id,
                type=ann.type,
                rect=rects_list,
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
            summary_config[s.summary_type] = s.content
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
                job_type=job.job_type,
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
                        rects_list.append(Rect(**r))
                    except:
                        pass
            
            result.append(Annotation(
                id=ann.id,
                type=ann.type,
                rect=rects_list,
                content=ann.content,
                color=ann.color
            ))
        return result

    async def add_annotation(self, paper_id: UUID, req: AnnotationRequest, user_id: UUID) -> None:
        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        if not paper or paper.user_id != user_id:
             raise HTTPException(status_code=404, detail="Paper not found")
             
        annotation = AnnotationEntity(
            id=uuid4(),
            paper_id=paper_id,
            type=req.type,
            rects=[r for r in req.rect], 
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
        annotation.rects = [r for r in req.rect]
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

'''
开发者: BackendAgent
当前版本: v1.4_paper_file_url_and_x_accel
创建时间: 2026年01月08日 14:00
更新时间: 2026年01月17日 21:58
更新记录:
    [2026年01月17日 21:58:v1.4_paper_file_url_and_x_accel:上传时生成稳定file_url并规范化文件名，配合Nginx X-Accel-Redirect下载]
    [2026年01月10日 10:20:v1.3_paper_service_saas:适配SaaS化架构，Service层返回DTO而非Entity，解耦数据层]
    [2026年01月09日 16:10:v1.2_paper_service:重构数据库访问逻辑，移除Service层SQL语句，使用Repository模式]
    [2026年01月08日 16:30:v1.1_paper_service:从/src/base/service/paper_service.py迁移到/src/service/papers/paper_service.py中]
    [2026年01月08日 14:00:v1.0_paper_service:创建论文上传与解析服务，实现文件处理、状态管理、向量化等核心功能]
'''

import asyncio
import hashlib
import json
import logging
import os
import uuid
import httpx
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Annotated
from urllib.parse import urlparse
from uuid import UUID

import aiofiles
from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from arq import create_pool
from arq.connections import RedisSettings

# 导入 Business Models / DTOs
from service.papers.schema import PaperUploadResponse, PaperDTO, PaperInfo
from common.model.enums import PaperStatus
from controller.api.papers.schema import PapersUploadWebRequest, PapersUploadResponse

# 导入 Entities (仅用于与 Repository 交互)
from base.pg.entity import Paper, PaperChunk, User, Collection, Job

from base.config import settings
from base.pg.service import PaperRepository, CollectionRepository, SessionDep, async_session_factory
from base.pdf_parser.parser import PDFParseResult, parse_pdf, extract_pdf_text, PyMuPDFParser
from base.embedding.embedding_service import EmbeddingService, embed_batch
from base.embedding.text_splitter import SemanticTextSplitter

from loguru import logger


class PaperService:
    """
    论文上传与解析服务
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        # TODO: 仅管理员标注: 这里暂时就是指定本地的上传的目录在哪。
        logger.info(f"PaperService 初始化完成，上传目录: {self.upload_dir}")

    def _entity_to_dto(self, paper: Paper) -> PaperDTO:
        """
        将 Paper 实体转换为 PaperDTO
        """
        # 状态映射兼容处理
        status = paper.analysis_status
        if status == "unprocessed":
            status = PaperStatus.PENDING
        elif status == "processed":
            status = PaperStatus.COMPLETED
        elif status == "error":
            status = PaperStatus.FAILED
            
        return PaperDTO(
            id=paper.id,
            user_id=paper.user_id,
            title=paper.title,
            authors=paper.authors,
            abstract=paper.summary,
            file_key=paper.file_key,
            file_url=paper.file_url,
            status=status,
            error_message=paper.error_message,
            created_at=paper.created_at,
            published_at=paper.published_at,
            source=paper.source,
            toc=paper.toc
        )

    async def upload_papers_from_web(self, req: PapersUploadWebRequest, user_id: UUID) -> List[PapersUploadResponse]:
        """
        从网络URL上传论文
        """
        responses = []
        
        async with httpx.AsyncClient() as client:
            for url in req.urls:
                try:
                    # 1. Download
                    logger.info(f"Downloading from web: {url}")
                    resp = await client.get(url, follow_redirects=True, timeout=30.0)
                    resp.raise_for_status()
                    
                    content_type = resp.headers.get("content-type", "application/pdf")
                    
                    # Extract filename
                    filename = url.split("/")[-1]
                    # remove query params
                    if "?" in filename:
                        filename = filename.split("?")[0]
                        
                    if not filename.lower().endswith(".pdf"):
                        filename += ".pdf"
                    
                    # 2. Upload using existing logic
                    upload_resp = await self.upload_paper(
                        file_content=resp.content,
                        filename=filename,
                        user_id=user_id,
                        content_type=content_type,
                        collection_id=req.collection_id
                    )
                    
                    responses.append(PapersUploadResponse(
                        paper_id=uuid.UUID(upload_resp.paper_id),
                        title=filename, 
                        status=upload_resp.status,
                        message=upload_resp.message
                    ))
                    
                except Exception as e:
                    logger.error(f"Failed to upload from web: {url}, error: {e}")
                    responses.append(PapersUploadResponse(
                        paper_id=uuid.uuid4(), 
                        title=url,
                        status="failed",
                        message=str(e)
                    ))
                    
        return responses

    async def upload_paper(
        self,
        file_content: bytes,
        filename: str,
        user_id: UUID,
        content_type: str = "application/pdf",
        collection_id: UUID | None = None,
    ) -> PaperUploadResponse:
        """
        上传论文文件
        """
        logger.info(f"开始上传论文: {filename}, 用户ID: {user_id}")

        # 1. 验证文件
        if not self._validate_file(filename, file_content):
            raise ValueError(f"文件验证失败: {filename}")

        safe_filename = Path(filename).name
        if not safe_filename:
            raise ValueError("文件名无效")

        # 2. 生成文件ID和路径
        file_id = str(uuid.uuid4())
        file_key = f"papers/{user_id}/{file_id}/{safe_filename}"
        file_path = self.upload_dir / file_key

        target_collection_id: UUID | None = None
        if collection_id is not None:
            collection = await CollectionRepository.get_collection_by_id(self.session, collection_id)
            if not collection or collection.user_id != user_id:
                raise ValueError("收藏夹不存在或无权访问")
            target_collection_id = collection.collection_id

        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 3. 保存文件
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)

            logger.info(f"文件保存成功: {file_path}")

            # 3.1 立即提取元数据 (Sync/Fast)
            # 使用PyMuPDF快速提取标题、作者、摘要，无需等待异步解析
            extracted_title = safe_filename
            extracted_authors = []
            extracted_summary = None
            extracted_published_at = None
            extracted_source = "upload"
            extracted_source_ref = None

            try:
                parser = PyMuPDFParser()
                # 使用 extract_metadata 异步方法 (内部会在 executor 中运行)
                metadata = await parser.extract_metadata(file_path)
                
                if metadata.get("title"):
                    extracted_title = metadata["title"]
                if metadata.get("authors"):
                    extracted_authors = metadata["authors"]
                if metadata.get("abstract"):
                    extracted_summary = metadata["abstract"]
                if metadata.get("source"):
                    extracted_source = metadata["source"]
                if metadata.get("source_id"):
                    extracted_source_ref = metadata["source_id"]
                
                # 处理日期
                if metadata.get("published_date"):
                    try:
                        p_date_str = metadata.get("published_date")
                        if len(p_date_str) == 10:
                            extracted_published_at = datetime.strptime(p_date_str, "%Y-%m-%d")
                        elif len(p_date_str) == 7:
                            extracted_published_at = datetime.strptime(p_date_str, "%Y-%m")
                        elif len(p_date_str) == 4:
                            extracted_published_at = datetime.strptime(p_date_str, "%Y")
                    except Exception as e:
                        logger.warning(f"上传时日期解析失败: {e}")

                # 增强: 如果解析器没识别出arXiv但文件名符合arXiv ID格式，强制修正
                if extracted_source != "arXiv":
                    # 匹配格式: 1405.3614.pdf 或 1405.3614v1.pdf
                    arxiv_id_match = re.search(r'(\d{4}\.\d{4,5}(v\d+)?)', filename)
                    if arxiv_id_match:
                        extracted_source = "arXiv"
                        extracted_source_ref = arxiv_id_match.group(1)
                        logger.info(f"通过文件名识别出arXiv ID: {extracted_source_ref}")

                # 增强: 如果是arXiv来源，尝试从arXiv API获取更准确的元数据
                if extracted_source == "arXiv" and extracted_source_ref:
                    try:
                        arxiv_meta = await self._fetch_arxiv_metadata(extracted_source_ref)
                        if arxiv_meta:
                            if arxiv_meta.get("title"):
                                extracted_title = arxiv_meta["title"]
                            if arxiv_meta.get("authors"):
                                extracted_authors = arxiv_meta["authors"]
                            if arxiv_meta.get("summary"):
                                extracted_summary = arxiv_meta["summary"]
                            if arxiv_meta.get("published_at"):
                                extracted_published_at = arxiv_meta["published_at"]
                            logger.info(f"已从arXiv API获取增强元数据: {extracted_title}")
                    except Exception as e:
                         logger.warning(f"arXiv元数据获取失败: {e}")

                logger.info(f"元数据提取成功: title={extracted_title}, authors={len(extracted_authors)}")
            except Exception as e:
                logger.warning(f"元数据提取失败(不影响上传): {e}")

            # 4. 创建论文记录
            paper = await self._create_paper_record(
                user_id=user_id,
                title=extracted_title,
                authors=extracted_authors,
                summary=extracted_summary,
                file_key=file_key,
                file_url=None,  # 可配置CDN URL
                published_at=extracted_published_at,
                source=extracted_source,
                source_ref=extracted_source_ref
            )

            try:
                if target_collection_id is not None:
                    await CollectionRepository.add_paper_to_collection(self.session, target_collection_id, paper.id)
                else:
                    default_collection = await CollectionRepository.get_default_collection(self.session, user_id)
                    if not default_collection:
                        try:
                            default_collection = await CollectionRepository.create_collection(
                                self.session,
                                Collection(
                                    user_id=user_id,
                                    name="默认收藏夹",
                                    description="系统默认收藏夹",
                                    is_default=True,
                                ),
                            )
                        except IntegrityError:
                            await self.session.rollback()
                            default_collection = await CollectionRepository.get_default_collection(self.session, user_id)

                    if default_collection:
                        await CollectionRepository.add_paper_to_collection(self.session, default_collection.collection_id, paper.id)
            except Exception as e:
                logger.warning(f"论文加入默认收藏夹失败(不影响上传): paper_id={paper.id}, user_id={user_id}, err={e}")

            logger.info(f"论文记录创建成功: {paper.id}")

            # 5. 触发异步处理任务
            # TODO: 这个解析好像有问题。TODO::作者标记,1. 要不要等待解析完成才持久化到本地?2.现在是先存储元数据到数据库,哪如果第一次解析,失败,那什么时候会再解析呢?
            await self._trigger_process_task(paper.id, file_path)

            return PaperUploadResponse(
                paper_id=str(paper.id),
                status=paper.analysis_status,
                message="论文上传成功，正在处理中"
            )

        except Exception as e:
            logger.error(f"论文上传失败: {e}", exc_info=True)
            # 清理已保存的文件
            if file_path.exists():
                file_path.unlink()
            raise
    
    # TODO: 这个异步任务创建和调度是否合理呃?
    async def _trigger_process_task(self, paper_id: UUID, file_path: Path):
        """
        触发PDF处理异步任务
        """
        # 0. 创建任务记录 (持久化)
        try:
            # 检查是否已存在(避免重复) - 这里简化为直接创建新任务
            # 获取 user_id 需要查询 paper，这里暂略，直接从 paper_id 关联
            # 为了简单，我们先获取 paper 的 user_id
            paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
            if paper:
                # 计算 params_hash
                params = {"paper_id": str(paper_id), "type": "process_pdf"}
                params_str = json.dumps(params, sort_keys=True)
                params_hash = hashlib.md5(params_str.encode()).hexdigest()

                job = Job(
                    user_id=paper.user_id,
                    paper_id=paper_id,
                    type="process_pdf",
                    status="queued",
                    progress=0.0,
                    params_hash=params_hash
                )
                self.session.add(job)
                await self.session.commit()
                logger.info(f"任务记录已创建: job_id={job.job_id}")
        except Exception as e:
             logger.error(f"创建任务记录失败: {e}")

        try:
            redis_url = settings.arq_redis_url
            parsed = urlparse(redis_url)
            host = parsed.hostname
            port = parsed.port or 6379
            database = int(parsed.path.lstrip("/") or "0")

            if not host:
                raise ValueError(f"Invalid Redis URL: {redis_url}")

            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=0.2,
                )
                writer.close()
                await writer.wait_closed()
            except Exception:
                # TODO: 这里的确是需要异步任务的一个执行。其实应该分为3个模块论文上传
                # 1.解析: 存储解析结果给AI进行利用(在上传的时候就进行处理,而不用等到需要AI需要的时候再解析->持久化))
                # 2.pdf持久化: 存储到本地文件系统或是对象存储,用于在离线的情况下,存储论文(思考: 我真的需要存储完整的论文嘛?我这边只做pdf解析和元数据存储(url或file?),想就保留着吧,再说)
                # 3.pdf元数据持久化: 存储基础的信息和可引用信息,可服务与收藏夹。
                logger.warning(f"Redis不可用，跳过任务入队: {host}:{port}, paper_id={paper_id}")

                return

            redis_settings = RedisSettings(
                host=host,
                port=port,
                database=database
            )
            
            pool = None
            try:
                pool = await create_pool(redis_settings)
                await pool.enqueue_job('process_pdf_task', str(paper_id))
            finally:
                if pool is not None:
                    await pool.close()
            
            logger.info(f"已触发PDF处理任务: {paper_id}")
        except Exception as e:
            logger.error(f"触发PDF处理任务失败: {e}", exc_info=True)
            # 记录错误但不抛出异常，避免影响上传响应
    
    async def _fetch_arxiv_metadata(self, arxiv_id: str) -> dict:
        """
        从arXiv API获取论文元数据
        """
        # 移除版本号 (v1, v2...) 以获取主记录，或者直接用带版本号的ID
        clean_id = arxiv_id
        if "arXiv:" in clean_id:
            clean_id = clean_id.replace("arXiv:", "")
            
        url = f"https://export.arxiv.org/api/query?id_list={clean_id}"
        logger.info(f"Fetching arXiv metadata for {clean_id}")
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(url, timeout=10.0)
                resp.raise_for_status()
                
                # 解析XML
                root = ET.fromstring(resp.content)
                # arXiv API 返回 Atom 格式
                ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
                
                entry = root.find('atom:entry', ns)
                if entry is None:
                    return {}
                
                # 检查标题是否包含 Error
                title_elem = entry.find('atom:title', ns)
                if title_elem is None:
                    return {}
                    
                title = title_elem.text.strip().replace('\n', ' ')
                if title == "Error":
                    return {}
                
                summary_elem = entry.find('atom:summary', ns)
                summary = summary_elem.text.strip() if summary_elem is not None else None
                
                published_elem = entry.find('atom:published', ns)
                published = published_elem.text.strip() if published_elem is not None else None
                
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append(name_elem.text.strip())
                
                published_at = None
                if published:
                    try:
                        # 2014-12-19T16:54:55Z
                        published_at = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                    except Exception:
                        pass
                    
                return {
                    "title": title,
                    "authors": authors,
                    "summary": summary,
                    "published_at": published_at
                }
        except Exception as e:
            logger.warning(f"arXiv API fetch failed: {e}")
            return {}

    #TODO: 用这里的redis做嘛?不用我们的worker下的内容,Agent需要获取重新了解下整个项目对这种解析的任务的了解,并汇报给我。
    def _validate_file(self, filename: str, file_content: bytes) -> bool:
        """
        验证文件类型和大小
        """
        # 检查文件大小
        if len(file_content) > settings.max_file_size:
            logger.warning(f"文件过大: {len(file_content)} > {settings.max_file_size}")
            return False

        # 检查文件类型
        allowed_extensions = {'.pdf', '.PDF'}
        file_ext = Path(filename).suffix.lower()

        if file_ext not in allowed_extensions:
            logger.warning(f"不支持的文件类型: {file_ext}")
            return False

        # 检查文件头（PDF文件以%PDF开头）
        if not file_content.startswith(b'%PDF'):
            logger.warning("文件头验证失败，不是有效的PDF文件")
            return False

        return True

    async def _create_paper_record(
        self,
        user_id: UUID,
        title: str,
        authors: List[str],
        file_key: str,
        file_url: Optional[str] = None,
        summary: Optional[str] = None,
        published_at: Optional[datetime] = None,
        source: Optional[str] = None,
        source_ref: Optional[str] = None
    ) -> Paper:
        """
        创建论文记录 (返回 Entity 供内部使用)
        """
        paper = Paper(
            user_id=user_id,
            title=title,
            authors=authors,
            summary=summary,
            file_key=file_key,
            file_url=file_url,
            analysis_status=PaperStatus.PENDING.value,
            published_at=published_at,
            source=source,
            source_id=source_ref
        )

        if paper.file_url is None:
            paper.file_url = f"/api/v1/papers/{paper.id}/file"

        return await PaperRepository.create_paper(self.session, paper)

    async def get_paper_status(self, paper_id: UUID, user_id: UUID) -> Optional[PaperDTO]:
        """
        获取论文处理状态/详情 (返回 DTO)
        """
        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        if paper and paper.user_id == user_id:
            return self._entity_to_dto(paper)
        return None

    async def get_paper_detail(self, paper_id: UUID, user_id: UUID) -> Optional[PaperDTO]:
        """
        获取论文详情 (别名方法，供Router调用)
        """
        return await self.get_paper_status(paper_id, user_id)


    async def update_paper_status(
        self,
        paper_id: UUID,
        status: PaperStatus,
        error_message: Optional[str] = None,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None
    ) -> bool:
        """
        更新论文处理状态
        """
        # 先更新状态
        paper = await PaperRepository.update_paper_status(self.session, paper_id, status, error_message)
        if not paper:
            return False
        
        # 如果有元数据更新
        if title or authors:
            await PaperRepository.update_paper_metadata(self.session, paper_id, title, authors)
        
        logger.info(f"论文状态更新: {paper_id} -> {status.value}")
        return True

    async def get_user_papers(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> List[PaperDTO]:
        """
        获取用户的论文列表 (返回 DTO 列表)
        """
        papers = await PaperRepository.get_user_papers(self.session, user_id, limit, offset)
        return [self._entity_to_dto(p) for p in papers]

    async def get_file_path(self, paper: PaperDTO) -> Optional[Path]:
        """
        获取论文文件的本地路径
        """
        file_path = self.upload_dir / paper.file_key
        if file_path.exists():
            return file_path
        return None

    async def delete_paper(self, paper_id: UUID, user_id: UUID) -> bool:
        """
        删除论文（包含相关数据）
        """
        # 验证权限
        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        if not paper or paper.user_id != user_id:
            return False

        # 删除数据库记录
        await PaperRepository.delete_paper(self.session, paper_id)

        # 删除文件
        file_path = self.upload_dir / paper.file_key
        if file_path.exists():
            file_path.unlink()

        logger.info(f"论文已删除: {paper_id}")
        return True


async def get_paper_service(session: SessionDep) -> PaperService:
    """获取 PaperService 实例"""
    return PaperService(session)

PaperServiceDep = Annotated[PaperService, Depends(get_paper_service)]


class PaperProcessingService:
    """
    论文处理服务（供异步任务调用）
    """

    def __init__(self):
        # TODO: 初始化PDF解析器、向量化模型等
        pass

    async def process_pdf(self, paper_id: UUID) -> bool:
        """
        处理PDF文件
        """
        logger.info(f"开始处理PDF: {paper_id}")

        try:
            # 1. 获取论文记录并更新状态
            async with async_session_factory() as session:
                paper = await PaperRepository.get_paper_by_id(session, paper_id)
                if not paper:
                    logger.error(f"论文不存在: {paper_id}")
                    return False
                
                # 更新状态为处理中
                await PaperRepository.update_paper_status(session, paper_id, PaperStatus.PROCESSING)
                paper.analysis_status = PaperStatus.PROCESSING.value # 更新本地对象状态

            # 2. 获取文件路径
            upload_dir = Path(settings.upload_dir)
            file_path = upload_dir / paper.file_key

            if not file_path.exists():
                logger.error(f"文件不存在: {file_path}")
                await self._update_status(paper_id, PaperStatus.FAILED, "文件不存在")
                return False

            # 3. 解析PDF
            text_content = await self._parse_pdf(file_path)
            if not text_content:
                logger.error("PDF解析失败")
                await self._update_status(paper_id, PaperStatus.FAILED, "PDF解析失败")
                return False

            # 4. 提取元数据（标题、作者等）
            metadata = await self._extract_metadata(file_path, text_content)

            # 5. 分割文本
            chunks = self._split_text(text_content)

            # 6. 生成向量嵌入
            embeddings = await self._generate_embeddings(chunks)

            # 7. 存储chunks
            await self._save_chunks(paper_id, chunks, embeddings)

            # 8. 更新论文记录
            published_at = None
            if metadata.get("published_date"):
                try:
                    p_date_str = metadata.get("published_date")
                    if len(p_date_str) == 10:
                        published_at = datetime.strptime(p_date_str, "%Y-%m-%d")
                    elif len(p_date_str) == 7:
                        published_at = datetime.strptime(p_date_str, "%Y-%m")
                    elif len(p_date_str) == 4:
                        published_at = datetime.strptime(p_date_str, "%Y")
                except Exception as e:
                    logger.warning(f"处理PDF时日期解析失败: {e}")

            await self._update_paper_after_processing(
                paper_id,
                title=metadata.get("title"),
                authors=metadata.get("authors", []),
                summary=metadata.get("abstract"),
                published_at=published_at,
                source=metadata.get("source"),
                source_id=metadata.get("source_id")
            )

            logger.info(f"PDF处理完成: {paper_id}")
            return True

        except Exception as e:
            logger.error(f"PDF处理失败: {e}", exc_info=True)
            await self._update_status(
                paper_id,
                PaperStatus.FAILED,
                f"处理失败: {str(e)}"
            )
            return False

    async def _parse_pdf(self, file_path: Path) -> Optional[str]:
        """
        解析PDF文件
        """
        try:
            logger.info(f"开始解析PDF文件: {file_path}")
            # 使用PDF解析器提取文本
            text_content = await extract_pdf_text(file_path)
            logger.info(f"PDF解析完成，文本长度: {len(text_content)}")
            return text_content
        except Exception as e:
            logger.error(f"PDF解析失败: {e}", exc_info=True)
            return None

    async def _extract_metadata(
        self,
        file_path: Path,
        text_content: str
    ) -> dict:
        """
        提取PDF元数据
        """
        try:
            logger.info(f"开始提取PDF元数据: {file_path}")
            # 使用PDF解析器提取完整信息
            parse_result = await parse_pdf(file_path)

            metadata = {
                "title": parse_result.title or file_path.stem,
                "authors": parse_result.authors or [],
                "abstract": parse_result.abstract,
                "published_date": parse_result.published_date,
                "source": parse_result.source,
                "source_id": parse_result.source_id,
                "pages": len(parse_result.pages),
                **parse_result.metadata
            }

            logger.info(f"元数据提取完成: 标题={metadata.get('title')}, 作者数={len(metadata.get('authors', []))}")
            return metadata
        except Exception as e:
            logger.error(f"元数据提取失败: {e}", exc_info=True)
            # 降级处理：返回基础信息
            return {
                "title": file_path.stem,
                "authors": [],
                "abstract": None,
                "pages": 0
            }

    def _split_text(self, text: str) -> List[str]:
        """
        分割文本成chunks
        """
        # 使用语义分割器
        splitter = SemanticTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            min_sentence_length=20
        )

        chunks = splitter.split_text(text)
        logger.info(f"文本分割完成，共 {len(chunks)} 个块")
        return chunks

    async def _generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """
        生成文本向量嵌入
        """
        try:
            logger.info(f"开始生成向量嵌入，chunks数量: {len(chunks)}")
            # 使用嵌入服务批量生成向量
            embeddings = await embed_batch(chunks, model_type="openai")
            logger.info(f"向量生成完成，向量维度: {len(embeddings[0]) if embeddings else 0}")
            return embeddings
        except Exception as e:
            logger.error(f"向量生成失败: {e}", exc_info=True)
            # 降级处理：返回零向量
            return [[0.0] * 1536 for _ in chunks]

    async def _save_chunks(
        self,
        paper_id: UUID,
        chunks: List[str],
        embeddings: List[List[float]]
    ):
        """
        保存文本块到数据库
        """
        async with async_session_factory() as session:
            paper_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                paper_chunks.append(PaperChunk(
                    paper_id=paper_id,
                    content=chunk,
                    chunk_index=i,
                    embedding=embedding
                ))
            
            await PaperRepository.create_paper_chunks(session, paper_chunks)
            logger.info(f"保存了 {len(chunks)} 个文本块")

    async def _update_paper_after_processing(
        self,
        paper_id: UUID,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None,
        toc: Optional[List] = None,
        summary: Optional[str] = None,
        published_at: Optional[datetime] = None,
        source: Optional[str] = None,
        source_id: Optional[str] = None
    ):
        """
        处理完成后更新论文记录
        """
        async with async_session_factory() as session:
            await PaperRepository.update_paper_status(session, paper_id, PaperStatus.COMPLETED)
            await PaperRepository.update_paper_metadata(
                session, 
                paper_id, 
                title, 
                authors, 
                toc, 
                summary, 
                published_at,
                source,
                source_id
            )
            logger.info(f"论文状态更新为完成: {paper_id}")

    async def _update_status(
        self,
        paper_id: UUID,
        status: PaperStatus,
        error_message: Optional[str] = None
    ):
        """
        更新论文状态
        """
        async with async_session_factory() as session:
            await PaperRepository.update_paper_status(session, paper_id, status, error_message)

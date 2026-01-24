'''
开发者: BackendAgent
当前版本: v1.2_marker_fix
创建时间: 2026年01月08日 15:00
更新时间: 2026年01月15日 14:00
更新记录:
    [2026年01月15日 14:00:v1.2_marker_fix:修复Marker库API变更导致的导入错误，适配新版Marker API]
    [2026年01月08日 15:00:v1.0_pdf_parser:创建PDF解析器，支持Marker和PyMuPDF两种方案]
'''

import asyncio
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from loguru import logger
# 尝试导入Marker依赖
try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False
    logger.warning("Marker依赖未安装，MarkerPDFParser将不可用")

# 尝试导入PyMuPDF依赖
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF依赖未安装，PyMuPDFParser将不可用")




class PDFParseResult(BaseModel):
    """PDF解析结果"""
    text: str = Field(..., description="提取的全文内容")
    title: Optional[str] = Field(None, description="论文标题")
    authors: List[str] = Field(default_factory=list, description="作者列表")
    abstract: Optional[str] = Field(None, description="摘要")
    published_date: Optional[str] = Field(None, description="发表日期")
    source: Optional[str] = Field(None, description="来源")
    source_id: Optional[str] = Field(None, description="来源ID")
    metadata: Dict = Field(default_factory=dict, description="元数据")
    pages: List[str] = Field(default_factory=list, description="按页分割的文本")
    toc: List = Field(default_factory=list, description="目录结构 (Table of Contents)")

    model_config = ConfigDict(arbitrary_types_allowed=True)

class BasePDFParser(ABC):
    """PDF解析器基类"""

    @abstractmethod
    async def parse(self, file_path: Path) -> PDFParseResult:
        """解析PDF文件"""
        pass

    @abstractmethod
    async def extract_text(self, file_path: Path) -> str:
        """提取纯文本"""
        pass

    @abstractmethod
    async def extract_metadata(self, file_path: Path) -> Dict:
        """提取元数据"""
        pass

    def _extract_published_date_and_source_from_text(self, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """从文本中提取发表日期、来源和来源ID (通用实现)"""
        # 限制搜索范围在前2000字符
        header_text = text[:2000]
        
        published_date = None
        source = None
        source_id = None

        # 1. 检查arXiv ID
        arxiv_match = re.search(r'arXiv:\d{4}\.\d{4,5}', header_text, re.IGNORECASE)
        if arxiv_match:
            source = "arXiv"
            # 提取YYMM
            arxiv_id = arxiv_match.group(0)
            source_id = arxiv_id
            match = re.search(r'arXiv:(\d{2})(\d{2})', arxiv_id, re.IGNORECASE)
            if match:
                year_short = match.group(1)
                month = match.group(2)
                # 假设20xx年
                year = f"20{year_short}"
                published_date = f"{year}-{month}-01"
                return published_date, source, source_id

        # 2. 检查常见日期格式
        date_patterns = [
            r'Published:\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # Published: 2023-01-01
            r'Date:\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',       # Date: 2023-01-01
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})', # 1 Jan 2023
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})', # Jan 1, 2023
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, header_text, re.IGNORECASE)
            if match:
                published_date = match.group(1)
                break

        # 3. 检查版权年份 (作为兜底)
        if not published_date:
            copyright_match = re.search(r'©\s*(\d{4})', header_text)
            if copyright_match:
                published_date = f"{copyright_match.group(1)}-01-01"
            
        return published_date, source, source_id

class MarkerPDFParser(BasePDFParser):
    """基于Marker的PDF解析器
    
    Marker是一个强大的PDF转Markdown工具，支持：
    - 准确的文本提取
    - 表格识别
    - 公式识别
    - 布局保持

    注意：Marker主要用于高质量文本提取，对于简单的元数据提取可能较慢。
    解析过程是计算密集型的，建议在Worker中运行。
    """

    def __init__(self):
        self.converter = None
        if MARKER_AVAILABLE:
            try:
                # 加载模型
                self.converter = PdfConverter(
                    artifact_dict=create_model_dict(),
                )
                logger.info("Marker模型加载完成")
            except Exception as e:
                logger.error(f"Marker模型加载失败: {e}")
                # 初始化失败时抛出异常，以便工厂类可以降级处理
                raise ImportError(f"Marker模型加载失败: {e}")
        else:
            raise ImportError("marker-pdf库未安装")
        
        logger.info("MarkerPDFParser初始化完成")

    async def parse(self, file_path: Path) -> PDFParseResult:
        """使用Marker解析PDF"""
        logger.info(f"使用Marker解析PDF: {file_path}")

        if not MARKER_AVAILABLE or self.converter is None:
             raise ImportError("marker-pdf库未安装或模型加载失败")

        try:
            # 定义同步转换函数
            def _run_converter():
                rendered = self.converter(str(file_path))
                text, _, images = text_from_rendered(rendered)
                return text, images, rendered.metadata

            # 在Executor中运行
            full_text, images, metadata = await asyncio.get_event_loop().run_in_executor(
                None,
                _run_converter
            )

            # 解析标题和作者
            title = metadata.get('title')
            authors = metadata.get('authors', [])
            
            if not title:
                title, _ = self._extract_title_and_authors(full_text)
            if not authors:
                _, authors = self._extract_title_and_authors(full_text)
                
            abstract = self._extract_abstract(full_text)

            # 分页处理
            pages = self._split_to_pages(full_text)

            published_date, source, source_id = self._extract_published_date_and_source_from_text(full_text)

            return PDFParseResult(
                text=full_text,
                title=title,
                authors=authors,
                abstract=abstract,
                published_date=published_date,
                source=source,
                source_id=source_id,
                metadata=metadata,
                pages=pages
            )

        except Exception as e:
            logger.error(f"Marker解析失败: {e}", exc_info=True)
            raise

    async def extract_text(self, file_path: Path) -> str:
        """提取纯文本"""
        result = await self.parse(file_path)
        return result.text

    async def extract_metadata(self, file_path: Path) -> Dict:
        """提取元数据"""
        result = await self.parse(file_path)
        return {
            "title": result.title,
            "authors": result.authors,
            "abstract": result.abstract,
            "published_date": result.published_date,
            "source": result.source,
            "source_id": result.source_id,
            **result.metadata
        }

    def _extract_title_and_authors(self, text: str) -> tuple:
        """从文本中提取标题和作者"""
        # 简单的提取逻辑，实际应该更复杂
        lines = text.strip().split('\n')
        title = lines[0] if lines else "Unknown Title"

        # 查找作者（通常在标题后几行）
        authors = []
        for line in lines[1:10]:  # 检查前10行
            # 简单的作者检测逻辑
            if any(keyword in line.lower() for keyword in ['author', 'by ', 'written by']):
                authors = [author.strip() for author in line.split(',')]
                break

        return title, authors

    def _extract_abstract(self, text: str) -> Optional[str]:
        """提取摘要"""
        # 查找Abstract部分
        abstract_match = re.search(
            r'abstract[\s]*\n(.*?)(?=\n\s*\n|\n1\s|\nintroduction|\nkeywords)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if abstract_match:
            return abstract_match.group(1).strip()
        return None

    def _split_to_pages(self, text: str) -> List[str]:
        """将文本按页分割"""
        # Marker通常会在分页处插入特殊标记
        # 这里使用简单的分页符检测
        pages = re.split(r'\f|\n\s*\n\s*\n', text)
        return [page.strip() for page in pages if page.strip()]


class PyMuPDFParser(BasePDFParser):
    """基于PyMuPDF的PDF解析器
    
    PyMuPDF（fitz）是一个轻量级的PDF处理库，支持：
    - 快速文本提取
    - 元数据读取
    - 页面级处理
    
    优势：速度极快，无需GPU，适合提取目录和元数据。
    劣势：复杂布局和公式还原能力不如Marker。
    """

    def __init__(self):
        self.fitz_available = PYMUPDF_AVAILABLE
        if self.fitz_available:
             self.fitz = fitz
        else:
             logger.warning("PyMuPDF (fitz) 未安装，将使用模拟解析器")
        
        logger.info(f"PyMuPDFParser初始化完成 (可用状态: {self.fitz_available})")

    async def parse(self, file_path: Path) -> PDFParseResult:
        """使用PyMuPDF解析PDF"""
        logger.info(f"使用PyMuPDF解析PDF: {file_path}")

        try:
            # 在异步环境中运行同步代码
            # 即使在Worker中，将CPU密集型任务放到executor中也是好的实践，避免阻塞事件循环
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self._parse_sync,
                file_path
            )
        except Exception as e:
            logger.error(f"PyMuPDF解析失败: {e}", exc_info=True)
            raise

    def _parse_sync(self, file_path: Path) -> PDFParseResult:
        """同步解析函数"""
        if not self.fitz_available:
            return self._mock_parse(file_path)

        doc = self.fitz.open(str(file_path))

        full_text = ""
        pages = []
        metadata = {}

        # 提取每页文本
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            pages.append(page_text)
            full_text += page_text + "\n"

        # 提取TOC
        try:
            toc = doc.get_toc()
            logger.info(f"PDF TOC提取结果: {len(toc)} items")
        except Exception as e:
            logger.warning(f"PDF TOC提取失败: {e}")
            toc = []

        # 提取元数据
        metadata = doc.metadata
        doc.close()

        # 从元数据或文本中提取标题和作者
        title = metadata.get('title', '') or self._extract_title_from_text(full_text)
        authors = self._extract_authors_from_text(full_text)
        abstract = self._extract_abstract_from_text(full_text)
        published_date, source, source_id = self._extract_published_date_and_source_from_text(full_text)

        return PDFParseResult(
            text=full_text.strip(),
            title=title,
            authors=authors,
            abstract=abstract,
            published_date=published_date,
            source=source,
            source_id=source_id,
            metadata=metadata,
            pages=pages,
            toc=toc
        )

    def _mock_parse(self, file_path: Path) -> PDFParseResult:
        """模拟解析结果（当依赖不可用时）"""
        # 注意: 开发环境使用Mock，生产环境应确保依赖安装
        logger.warning(f"使用模拟解析结果: {file_path}")
        mock_text = f"这是文件 {file_path.name} 的模拟文本内容。\n由于 PyMuPDF 未安装，无法提取真实内容。\n" * 10
        return PDFParseResult(
            text=mock_text,
            title=file_path.stem,
            authors=["Mock Author"],
            abstract="This is a mock abstract.",
            metadata={"producer": "MockParser"},
            pages=[mock_text],
            toc=[[1, "Mock Section 1", 1], [1, "Mock Section 2", 2]]
        )

    async def extract_text(self, file_path: Path) -> str:
        """提取纯文本"""
        result = await self.parse(file_path)
        return result.text

    async def extract_metadata(self, file_path: Path) -> Dict:
        """提取元数据"""
        result = await self.parse(file_path)
        return {
            "title": result.title,
            "authors": result.authors,
            "abstract": result.abstract,
            "published_date": result.published_date,
            "source": result.source,
            "source_id": result.source_id,
            **result.metadata
        }

    def _extract_title_from_text(self, text: str) -> str:
        """从文本中提取标题"""
        lines = text.strip().split('\n')
        for line in lines[:20]:  # 检查前20行
            line = line.strip()
            # 标题通常是较长的行，不包含特殊字符
            if len(line) > 20 and not re.search(r'[@#$%^*()={}\[\]]', line):
                return line
        return "Unknown Title"

    def _extract_authors_from_text(self, text: str) -> List[str]:
        """从文本中提取作者"""
        authors = []
        # 查找常见的作者格式
        patterns = [
            r'Authors?:\s*(.+?)(?:\n|\r)',
            r'By:\s*(.+?)(?:\n|\r)',
            r'^(.+?)(?:\n|\r)',  # 第一行可能是作者
        ]

        for pattern in patterns:
            match = re.search(pattern, text[:1000], re.IGNORECASE | re.MULTILINE)
            if match:
                author_text = match.group(1).strip()
                # 分割多个作者
                if ',' in author_text:
                    authors = [name.strip() for name in author_text.split(',')]
                elif ' and ' in author_text:
                    authors = [name.strip() for name in author_text.split(' and ')]
                else:
                    authors = [author_text]
                break

        return authors

    def _extract_abstract_from_text(self, text: str) -> Optional[str]:
        """从文本中提取摘要"""
        # 查找Abstract部分
        patterns = [
            r'Abstract[\s]*\n(.*?)(?=\n\s*\n|\n1\s|\nIntroduction|\nKeywords)',
            r'Summary[\s]*\n(.*?)(?=\n\s*\n)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return None


class PDFParserFactory:
    """PDF解析器工厂"""

    @staticmethod
    def create_parser(parser_type: str = "auto") -> BasePDFParser:
        """
        创建PDF解析器

        参数:
        - parser_type: 解析器类型 ("marker", "pymupdf", "auto")

        返回:
        - BasePDFParser: 解析器实例
        """
        if parser_type == "auto":
            # 优先使用Marker（质量更好），如果不可用则使用PyMuPDF（速度更快/备选）
            if MARKER_AVAILABLE:
                try:
                    logger.info("尝试初始化 MarkerPDFParser (Auto)...")
                    return MarkerPDFParser()
                except Exception as e:
                    logger.warning(f"MarkerPDFParser 初始化失败 ({e})，自动降级使用 PyMuPDFParser")
                    if PYMUPDF_AVAILABLE:
                        return PyMuPDFParser()
                    else:
                        logger.warning("PyMuPDFParser 也不可用，返回 MockParser")
                        return PyMuPDFParser() # PyMuPDFParser handles missing dep with mock
            elif PYMUPDF_AVAILABLE:
                logger.info("使用PyMuPDFParser (Auto)")
                return PyMuPDFParser()
            else:
                logger.warning("没有可用的解析器，返回Mock/PyMuPDFParser(Mock模式)")
                return PyMuPDFParser()

        elif parser_type == "marker":
            return MarkerPDFParser()

        elif parser_type == "pymupdf":
            return PyMuPDFParser()

        else:
            raise ValueError(f"不支持的解析器类型: {parser_type}")


# 全局解析器实例
_pdf_parser: Optional[BasePDFParser] = None


async def get_pdf_parser(parser_type: str = "auto") -> BasePDFParser:
    """获取PDF解析器单例"""
    global _pdf_parser
    if _pdf_parser is None:
        _pdf_parser = PDFParserFactory.create_parser(parser_type)
    return _pdf_parser


async def parse_pdf(file_path: Path, parser_type: str = "auto") -> PDFParseResult:
    """便捷函数：解析PDF文件"""
    parser = await get_pdf_parser(parser_type)
    return await parser.parse(file_path)


async def extract_pdf_text(file_path: Path, parser_type: str = "auto") -> str:
    """便捷函数：提取PDF文本"""
    parser = await get_pdf_parser(parser_type)
    return await parser.extract_text(file_path)
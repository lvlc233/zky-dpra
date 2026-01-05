'''
开发者: BackendAgent
当前版本: v0.1_papers
创建时间: 2026年01月02日 10:16
更新时间: 2026年01月02日 10:16
更新记录:
    [2026年01月02日 10:16:v0.1_papers:修复依赖注入和安全问题，使用Depends注入服务]
    [2026年01月02日 08:54:v0.1_paper_router:全局实例化服务，违反依赖注入原则]
'''

from fastapi import APIRouter, HTTPException, status, Depends
import logging

from .requests import PaperFetchRequest
from ....business_model.model import PaperListResponse, PaperInfo
from ....service.papers.arxiv_service import ArxivService
from ....base.arxiv.client import ArxivClient
from ....base.arxiv.parser import ArxivXmlParser

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/papers", tags=["papers"])


def get_arxiv_service() -> ArxivService:
    '''
    服务工厂函数

    创建ArxivService实例，并注入Infrastructure依赖

    返回:
    - ArxivService实例

    依赖注入:
    - 创建ArxivClient（Infrastructure层：处理HTTP通信）
    - 创建ArxivXmlParser（Infrastructure层：处理XML解析）
    - 将依赖注入ArxivService
    '''
    client = ArxivClient()
    parser = ArxivXmlParser()
    return ArxivService(client=client, parser=parser)


@router.post("/fetch", response_model=PaperListResponse)
async def fetch_papers(
    request: PaperFetchRequest,
    service: ArxivService = Depends(get_arxiv_service)
):
    '''
    从URL获取论文集

    接口说明:
    - 接收包含论文页面URL的请求
    - 从URL中提取并获取论文信息
    - 返回论文列表和元数据

    参数:
    - request: PaperFetchRequest对象，包含url和source字段
    - service: ArxivService实例（通过依赖注入获取）

    返回:
    - PaperListResponse对象，包含论文列表、总数、来源和原始URL

    错误处理:
    - 400: 请求参数无效
    - 422: URL格式不支持或无法解析
    - 500: 服务器内部错误

    使用示例:
    ```json
    {
        "url": "https://arxiv.org/abs/2101.12345",
        "source": "arXiv"
    }
    ```

    响应示例:
    ```json
    {
        "papers": [
            {
                "title": "Attention Is All You Need",
                "authors": ["Ashish Vaswani", "Noam Shazeer"],
                "abstract": "The dominant sequence transduction models...",
                "paper_url": "https://arxiv.org/abs/1706.03762",
                "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
                "published_date": "2017-06-12",
                "categories": ["cs.CL", "cs.LG"],
                "source_id": "1706.03762"
            }
        ],
        "total_count": 1,
        "source": "arXiv",
        "fetch_url": "https://arxiv.org/abs/2101.12345"
    }
    ```

    架构说明:
    - Controller层：接收请求，验证参数，返回响应（本函数）
    - Service层：处理业务逻辑（ArxivService）
    - Infrastructure层：处理HTTP和XML解析（ArxivClient, ArxivXmlParser）

    TODO:
    - 支持批量URL提交
    - 添加请求速率限制
    - 添加缓存机制（Redis）
    - 支持更多学术网站（IEEE, ACM, PubMed等）
    '''

    logger.info(f"接收到论文获取请求: url={request.url}, source={request.source}")

    try:
        # 验证输入
        if not request.url or not request.url.strip():
            logger.error("URL为空，返回400错误")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL不能为空"
            )

        # 根据source选择服务（目前仅支持arXiv，后续可扩展）
        if request.source.lower() != "arxiv":
            logger.error(f"不支持的数据源: {request.source}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"目前仅支持arXiv数据源，不支持: {request.source}"
            )

        # 调用Service层获取论文信息（依赖注入）
        logger.info("调用ArxivService获取论文信息")
        papers = await service.fetch_papers_from_url(request.url)

        # 构建响应
        total_count = len(papers)
        logger.info(f"成功获取 {total_count} 篇论文")

        response = PaperListResponse(
            papers=papers,
            total_count=total_count,
            source=request.source,
            fetch_url=request.url
        )

        logger.info("论文获取完成，返回响应")
        return response

    except HTTPException:
        # 已定义的HTTP异常，直接抛出
        raise
    except Exception as e:
        # 未预期的异常，记录日志并返回500错误
        # 安全：不将异常详情返回给客户端，防止信息泄露
        logger.error(f"获取论文时发生未知错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请联系管理员"
        )


@router.get("/{arxiv_id}", response_model=PaperInfo)
async def get_paper_by_id(arxiv_id: str):
    '''
    根据arXiv ID获取单篇论文详情

    接口说明:
    - 直接通过arXiv ID获取论文详细信息
    - 不需要完整的URL

    参数:
    - arxiv_id: arXiv论文ID（例如: 2101.12345）

    返回:
    - PaperInfo对象，包含完整论文信息

    TODO:
    - 实现此接口
    - 支持批量ID查询（query参数格式: ids=id1,id2,id3）
    '''

    logger.info(f"接收到获取单篇论文请求: arxiv_id={arxiv_id}")

    # TODO: 实现单篇论文查询逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="该接口尚未实现"
    )


@router.get("/search/test")
async def test_arxiv_search():
    '''
    测试接口：获取arXiv最近几篇论文用于测试

    使用场景:
    - 前端开发测试
    - API连通性测试
    - 演示功能

    TODO:
    - 实现此接口
    - 添加参数控制返回数量（默认10篇）
    - 添加分类过滤参数
    '''

    logger.info("接收到测试请求: 获取arXiv最新论文")

    # TODO: 实现测试接口
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="测试接口尚未实现"
    )

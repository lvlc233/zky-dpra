import asyncio
import os
from sqlmodel import select
from base.pg.service import get_db_session
from base.pg.entity import SystemModelConfig
from service.papers.core_service import CoreProvider
from loguru import logger

async def test_core():
    # 1. Fetch API key from DB
    try:
        session = next(get_db_session())
        stmt = select(SystemModelConfig).where(SystemModelConfig.api_name == "CORE")
        db_config = session.execute(stmt).scalars().first()
        
        if not db_config or not db_config.api_key:
            logger.error("未在数据库中找到 CORE API Key。请确保已经在管理员页面配置。")
            return
            
        api_key = db_config.api_key
        logger.info(f"找到 CORE API Key (长度: {len(api_key)})")
        
        # 2. Test CoreProvider
        provider = CoreProvider()
        query = "artificial intelligence"
        logger.info(f"尝试搜索: {query}")
        
        results, total = await provider.search_papers(query=query, max_results=5, api_key=api_key)
        
        if results:
            logger.info(f"搜索成功！获取到 {len(results)} 条结果 (总计约 {total} 条)")
            for i, p in enumerate(results):
                logger.info(f"[{i+1}] {p.title}")
                logger.info(f"    - 作者: {', '.join(p.authors)}")
                logger.info(f"    - 链接: {p.paper_url}")
                logger.info(f"    - PDF: {p.pdf_url}")
                logger.info(f"    - 日期: {p.published_date}")
        else:
            logger.warning("搜索返回空结果。请检查 API Key 是否有效。")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_core())

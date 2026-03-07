"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-25
描述: InPaperChatAgent 工具集
"""

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from loguru import logger
from uuid import UUID

@tool
async def retrieve_paper_tool(
    query: str, 
    config: RunnableConfig
) -> str:
    """
    检索当前论文的相关片段。
    """
    # 1. 获取上下文
    configuration = config.get("configurable", {})
    session = configuration.get("session")
    paper_id = configuration.get("paper_id") # 注意：这里假设 paper_id 被注入到了 configurable 中
    user_id_val = configuration.get("user_id")

    if not session:
        return "Error: Database session not found in context."
    if not paper_id:
        return "Error: Paper ID not found in context."
        
    try:
        from service.reader.retrieval_service import RetrievalService
        
        # 处理 user_id
        user_id = None
        if user_id_val:
            user_id = UUID(str(user_id_val)) if not isinstance(user_id_val, UUID) else user_id_val
            
        service = RetrievalService(session, user_id)
        
        # 混合检索
        chunks = await service.retrieve_chunks(paper_id, query, hybrid=True)
        
        if not chunks:
            return "未检索到相关内容。"
            
        # 格式化返回
        formatted = "\n\n".join([
            f"[片段 {i+1}] (Page {c.metadata.get('page', '?')}):\n{c.page_content}" 
            for i, c in enumerate(chunks)
        ])
        return formatted
        
    except Exception as e:
        logger.exception("Tool execution failed: {}", e)
        return f"检索失败: {str(e)}"

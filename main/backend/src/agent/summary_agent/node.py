"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14
更新时间: 2026-01-14
更新记录: 
    [2026-01-14:v1.0.0:实现 SummaryAgent 核心节点: load_paper, generate_summary]
"""

import logging
from typing import Dict, Any
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime

from agent.summary_agent.schema import SummaryAgentState,SummaryAgentRuntimeContext
from agent.summary_agent.prompts import SUMMARY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def generate_summary_node(state: SummaryAgentState, runtime: Runtime[SummaryAgentRuntimeContext]) -> Dict[str, Any]:
    """
    生成总结。
    """
    paper_content = state.get("paper_content")
    
    if not paper_content:
        return {
            "summary": "无法获取论文内容，无法生成总结。",
            "messages": [AIMessage(content="无法获取论文内容，无法生成总结。")]
        }
    
    llm_config = runtime.context
    logger.info(f"llm_config: {llm_config}")
    llm:BaseChatModel = init_chat_model(
        model=llm_config.get("model_name", "gpt-3.5-turbo"),
        model_provider=llm_config.get("model_provider", "openai"),
        base_url=llm_config.get("base_url"),
        api_key=llm_config.get("api_key"),
        temperature=llm_config.get("temperature", 0.3),
    ) 
    
    response = await llm.ainvoke(
        SUMMARY_SYSTEM_PROMPT.format(paper_content=paper_content, language="中文"),
    ) 
    
    return {
        "summary": response.content,
        "messages": [response], # 将总结作为 AI 回复推入消息历史
        "sender": "SummaryAgent"
    }

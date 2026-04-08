"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14
更新时间: 2026-01-14
更新记录: 
    [2026-01-14:v1.0.0:实现 SummaryAgent 核心节点: load_paper, generate_summary]
"""

from loguru import logger
from typing import Dict, Any
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.runtime import Runtime

from agent.summary_agent.schema import SummaryAgentState,SummaryAgentRuntimeContext
from agent.summary_agent.prompts import SUMMARY_SYSTEM_PROMPT

# logger = logging.getLogger(__name__) # Use loguru instead


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
    
    # 截断以适应 Context (参考 MindMapAgent)
    # 目的: 防止超长论文导致 Connection error 或 Context Overflow
    safe_content = paper_content[:15000]
    if len(paper_content) > 15000:
        logger.warning(f"Paper content truncated from {len(paper_content)} to 15000 chars")

    llm_config = runtime.context
    llm_config = runtime.context
    logger.error(f"DEBUG: runtime type: {type(runtime)}, dir(runtime): {dir(runtime)}")
    logger.error(f"DEBUG: runtime.context: {runtime.context}")
    logger.error(f"SummaryAgent using llm_config: {llm_config.get('model_name') if llm_config else 'None'} at {llm_config.get('base_url') if llm_config else 'None'}")
    
    try:
        llm:BaseChatModel = init_chat_model(
            model=llm_config.get("model_name", "gpt-3.5-turbo"),
            model_provider=llm_config.get("model_provider", "openai"),
            base_url=llm_config.get("base_url") or None,
            api_key=llm_config.get("api_key") or None,
            temperature=llm_config.get("temperature", 0.3),
            timeout=300, # 增加超时时间到 300s
            max_tokens=llm_config.get("max_tokens", 4096),
        ) 
        
        # 使用 ChatPromptTemplate 避免直接 .format() 可能带来的 { } 溢出或解析错误
        prompt = ChatPromptTemplate.from_messages([
            ("system", SUMMARY_SYSTEM_PROMPT),
            ("human", "请根据以上内容生成论文总结报告。"),
        ])
        
        # 截断以适应 Context
        safe_content = paper_content[:15000]
        
        chain = prompt | llm
        
        logger.info(f"SummaryAgent invoking LLM chain... (content length: {len(safe_content)})")
        
        response = await chain.ainvoke({
            "paper_content": safe_content
        }) 
        
        return {
            "summary": response.content,
            "messages": [response], 
            "sender": "SummaryAgent"
        }
    except Exception as e:
        logger.error(f"SummaryAgent node failed: {e}", exc_info=True)
        # Re-raise to ensure arq/LangGraph signals failure
        raise e

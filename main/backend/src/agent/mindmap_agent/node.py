"""
开发者: LangGraphAgent
当前版本: v1.0.1
创建时间: 2026-01-14
更新时间: 2026-01-24
更新记录: 
    [2026-01-14:v1.0.0:实现 MindMapAgent 核心节点]
    [2026-01-24:v1.0.1:更新 generate_mindmap_node 以支持结构化输出]
"""

import logging
from typing import Dict, Any
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig

from agent.mindmap_agent.schema import MindMapAgentState, MindMapStructure, MindMapAgentRuntimeContext
from agent.mindmap_agent.prompts import mindmap_generator_prompt
logger = logging.getLogger(__name__)



async def generate_mindmap_node(state: MindMapAgentState, runtime: Runtime[MindMapAgentRuntimeContext]) -> Dict[str, Any]:
    """
    生成结构化脑图 (Nodes/Edges)。
    """
    paper_content = state.get("paper_content")
    depth = state.get("depth", 2)
    
    if not paper_content:
        return {
            "mindmap_data": {"nodes": [], "edges": []},
            "messages": [AIMessage(content="无法获取论文内容。")]
        }
    
    # 获取 LLM 配置 (参考 SummaryAgent 风格)
    llm_config = runtime.context
    logger.info(f"llm_config: {llm_config}")
    
    llm: BaseChatModel = init_chat_model(
        model=llm_config.get("model_name", "gpt-3.5-turbo"),
        model_provider=llm_config.get("model_provider", "openai"),
        base_url=llm_config.get("base_url"),
        api_key=llm_config.get("api_key"),
        temperature=llm_config.get("temperature", 0.3),
    )
    
    # 绑定结构化输出 schema
    structured_llm = llm.with_structured_output(MindMapStructure)
    
    chain = mindmap_generator_prompt | structured_llm
    
    # 截断以适应 Context
    safe_content = paper_content[:15000]
    
    try:
        response: MindMapStructure = await chain.ainvoke({
            "paper_content": safe_content,
            "depth": depth
        })
        
        return {
            "mindmap_data": response.model_dump(),
            "messages": [AIMessage(content="Mind map generated successfully.")],
            "sender": "MindMapAgent"
        }
    except Exception as e:
        logger.error(f"MindMap generation failed: {e}")
        # Fallback empty
        return {
            "mindmap_data": {"nodes": [], "edges": []},
            "messages": [AIMessage(content=f"Mind map generation failed: {e}")]
        }

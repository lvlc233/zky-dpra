"""
开发者: LangGraphAgent
当前版本: v1.0.2
创建时间: 2026-01-14
更新时间: 2026-04-05
更新记录: 
    [2026-01-14:v1.0.0:实现 MindMapAgent 核心节点]
    [2026-01-24:v1.0.1:更新 generate_mindmap_node 以支持结构化输出]
    [2026-04-05:v1.0.2:添加 JSON 解析回退机制，兼容不支持结构化输出的模型]
"""

import re
import json
import logging
from typing import Dict, Any
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig

from agent.mindmap_agent.schema import MindMapAgentState, MindMapStructure, MindMapAgentRuntimeContext
from agent.mindmap_agent.prompts import mindmap_generator_prompt
logger = logging.getLogger(__name__)


def _extract_json_from_response(text: str) -> str:
    """
    从 LLM 响应中提取 JSON 内容。
    处理模型返回 ```json ... ``` 包裹的情况。
    """
    # 尝试匹配 ```json ... ``` 或 ``` ... ``` 代码块
    pattern = r'```(?:json)?\s*\n?(.*?)\n?\s*```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 如果没有代码块包裹，尝试直接查找 JSON 对象
    # 查找第一个 { 到最后一个 } 之间的内容
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        return brace_match.group(0).strip()
    return text.strip()


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
        base_url=llm_config.get("base_url") or None,
        api_key=llm_config.get("api_key") or None,
        temperature=llm_config.get("temperature", 0.3),
        timeout=300, # 增加超时时间到 300s
        max_tokens=llm_config.get("max_tokens", 4096),
    )
    
    # 截断以适应 Context
    safe_content = paper_content[:15000]
    
    try:
        # 方式1: 尝试使用结构化输出 (适用于原生支持的模型, 如 OpenAI)
        structured_llm = llm.with_structured_output(MindMapStructure)
        chain = mindmap_generator_prompt | structured_llm
        
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
        logger.warning(f"Structured output failed (likely model doesn't support it), falling back to manual JSON parsing: {e}")
        
        try:
            # 方式2: 回退 - 直接调用 LLM，手动解析 JSON
            chain_raw = mindmap_generator_prompt | llm
            raw_response = await chain_raw.ainvoke({
                "paper_content": safe_content,
                "depth": depth
            })
            
            raw_text = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)
            logger.info(f"Raw LLM response length: {len(raw_text)}")
            
            # 提取并解析 JSON
            json_str = _extract_json_from_response(raw_text)
            parsed_data = MindMapStructure.model_validate_json(json_str)
            
            return {
                "mindmap_data": parsed_data.model_dump(),
                "messages": [AIMessage(content="Mind map generated successfully (fallback parser).")],
                "sender": "MindMapAgent"
            }
        except Exception as fallback_error:
            logger.error(f"MindMap generation failed (both structured and fallback): {fallback_error}")
            raise fallback_error


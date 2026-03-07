"""
开发者: LangGraphAgent
当前版本: v1.1.0
创建时间: 2026-01-25
描述: InPaperChatAgent 节点实现 (Agentic RAG)
"""

from typing import Dict, Any, Optional
from uuid import UUID
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from sqlalchemy.ext.asyncio import AsyncSession

from service.setting.setting_service import SettingService
from .schema import InPaperChatState
from .prompts import paper_chat_prompt
from .tools import retrieve_paper_tool

# 1. 定义工具列表
tools = [retrieve_paper_tool]

# 2. 移除全局模型初始化，改为动态获取
# model = ChatOpenAI(model="gpt-4o", temperature=0)
# model_with_tools = model.bind_tools(tools)

async def _get_model(session: AsyncSession, user_id: UUID) -> ChatOpenAI:
    """动态获取配置好的 LLM 模型"""
    try:
        setting_service = SettingService(session)
        # 获取原始设置（包含未掩码的 API Key）
        user_settings = await setting_service.get_settings(user_id)
        
        # 优先使用 AgentSettings (RAG Config)
        if hasattr(user_settings, 'agent_settings') and user_settings.agent_settings:
            agent_settings = user_settings.agent_settings
            
            # 如果配置了 RAG 设置，则优先使用
            if agent_settings.rag_provider in ['siliconflow', 'openai', 'ollama']:
                api_key = agent_settings.rag_api_key
                base_url = agent_settings.rag_base_url
                model_name = agent_settings.rag_base_model
                
                # SiliconFlow / OpenAI
                if agent_settings.rag_provider in ['siliconflow', 'openai']:
                    if api_key:
                        return ChatOpenAI(
                            model=model_name,
                            temperature=agent_settings.rag_temperature,
                            api_key=api_key,
                            base_url=base_url
                        )
                
                # Ollama
                elif agent_settings.rag_provider == 'ollama':
                     return ChatOpenAI(
                        model=model_name,
                        temperature=agent_settings.rag_temperature,
                        base_url=base_url,
                        api_key="ollama" # Ollama doesn't need key but langchain might require string
                    )

        # Fallback to AIReaderSettings (Old logic)
        ai_settings = user_settings.ai_reader_settings
        
        # 查找配置优先级: chat > summary > first
        target_setting = next((s for s in ai_settings if s.type == 'chat'), None)
        if not target_setting:
            target_setting = next((s for s in ai_settings if s.type == 'summary'), None)
        if not target_setting and ai_settings:
            target_setting = ai_settings[0]
            
        api_key = None
        base_url = None
        model_name = "gpt-4o"
        
        if target_setting:
            api_key = target_setting.api_key
            base_url = target_setting.base_url or None
            if target_setting.llm_name:
                model_name = target_setting.llm_name
                
        # 如果有 API Key，使用配置的
        if api_key:
            return ChatOpenAI(
                model=model_name,
                temperature=0,
                api_key=api_key,
                base_url=base_url
            )
        
        # 否则尝试默认 (依赖环境变量)
        return ChatOpenAI(model="gpt-4o", temperature=0)
        
    except Exception as e:
        # 如果获取失败，尝试最基本的初始化
        # 但此时是在 runtime，不是 import time
        return ChatOpenAI(model="gpt-4o", temperature=0)


# 3. 节点实现
async def agent_node(state: InPaperChatState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Agent 决策节点：决定是调用工具还是直接回答。
    """
    # 获取上下文中的 session 和 user_id
    configuration = config.get("configurable", {})
    session = configuration.get("session")
    user_id_val = configuration.get("user_id")
    
    if not session or not user_id_val:
        raise ValueError("Session or User ID missing in config")
        
    user_id = UUID(user_id_val) if isinstance(user_id_val, str) else user_id_val
    
    # 动态初始化模型
    model = await _get_model(session, user_id)
    model_with_tools = model.bind_tools(tools)
    
    chain = paper_chat_prompt | model_with_tools
    
    response = await chain.ainvoke(state, config)
    
    return {"messages": [response]}

# 4. 工具节点
# 使用 LangGraph 预置的 ToolNode，它会自动执行 tool_calls
tools_node = ToolNode(tools)

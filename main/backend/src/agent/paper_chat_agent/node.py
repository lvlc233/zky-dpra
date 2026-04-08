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
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from service.setting.setting_service import SettingService
from .schema import InPaperChatState
from .prompts import PAPER_CHAT_SYSTEM
from .tools import retrieve_paper_tool
from base.pg.service import PaperRepository

# 1. 定义工具列表
tools = [retrieve_paper_tool]

# 2. 移除全局模型初始化，改为动态获取
# model = ChatOpenAI(model="gpt-4o", temperature=0)
# model_with_tools = model.bind_tools(tools)

async def _get_model(session: AsyncSession, user_id: UUID) -> ChatOpenAI:
    """动态获取配置好的 LLM 模型 (支持系统级配置)"""
    try:
        setting_service = SettingService(session)
        config = await setting_service.get_effective_model_config(user_id, 'chat')
        
        # 提取配置
        model_name = config.get("model_name", "gpt-4o")
        temperature = config.get("temperature", 0)
        api_key = config.get("api_key")
        base_url = config.get("base_url")

        # 如果有 API Key，使用配置的
        if api_key:
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=api_key,
                base_url=base_url
            )
        
        # 否则尝试默认 (依赖环境变量)
        return ChatOpenAI(model="gpt-4o", temperature=0)
        
    except Exception as e:
        logger.error(f"Error getting model config: {e}")
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
    paper_id = configuration.get("paper_id")
    
    # 3. 获取论文信息以增强上下文
    paper_title = "未知论文"
    if paper_id:
        paper = await PaperRepository.get_paper_by_id(session, paper_id)
        if paper:
            paper_title = paper.title

    # 4. 动态初始化模型
    model = await _get_model(session, user_id)
    model_with_tools = model.bind_tools(tools)
    
    # 5. 注入论文信息到 System Prompt
    # 注意: paper_chat_prompt 是 ChatPromptTemplate
    # 我们需要替换其中的 system 消息
    messages = [
        ("system", PAPER_CHAT_SYSTEM.format(paper_title=paper_title, paper_id=str(paper_id))),
        *state["messages"]
    ]
    
    # 使用 ainvoke
    response = await model_with_tools.ainvoke(messages, config)
    
    return {"messages": [response]}

# 4. 工具节点
# 使用 LangGraph 预置的 ToolNode，它会自动执行 tool_calls
tools_node = ToolNode(tools)

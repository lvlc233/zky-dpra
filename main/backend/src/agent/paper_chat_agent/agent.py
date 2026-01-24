"""
开发者: LangGraphAgent
当前版本: v1.1.0
创建时间: 2026-01-25
描述: InPaperChatAgent 图编排 (Agentic RAG)
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import tools_condition
from .schema import InPaperChatState
from .node import agent_node, tools_node
from ..base.checkpointer import get_checkpointer

def create_paper_chat_agent_graph():
    """
    创建并编译 InPaperChatAgent 的运行图。
    模式: ReAct (Agent -> Tools -> Agent)
    """
    workflow = StateGraph(InPaperChatState)

    # 1. 添加节点
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)

    # 2. 定义边
    workflow.set_entry_point("agent")
    
    # 条件边: 如果 Agent 决定调用工具，则跳转到 tools；否则结束
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
    )
    
    # 工具执行完后，返回给 Agent 继续处理
    workflow.add_edge("tools", "agent")

    # 3. 编译图
    checkpointer = get_checkpointer()
    
    return workflow.compile(checkpointer=checkpointer), workflow

# 导出已编译的图实例和工作流定义
paper_chat_agent_graph, paper_chat_workflow = create_paper_chat_agent_graph()

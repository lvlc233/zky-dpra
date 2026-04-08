"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-14
更新时间: 2026-01-14
更新记录: 
    [2026-01-14:v1.0.0:编排 MindMapAgent 图结构]
"""

from langgraph.graph import StateGraph, END
from agent.mindmap_agent.schema import MindMapAgentState
from agent.mindmap_agent.node import generate_mindmap_node

def create_mindmap_agent_graph():
    """
    创建并编译 MindMapAgent 的运行图。
    """
    workflow = StateGraph(MindMapAgentState)

    workflow.add_node("generate_mindmap", generate_mindmap_node)

    # 2. 定义边
    workflow.set_entry_point("generate_mindmap")
    workflow.add_edge("generate_mindmap", END)

    
    return workflow.compile()

mindmap_agent_graph = create_mindmap_agent_graph()

"""
创建时间: 2026-01-02
创建者: LangGraphAgent
描述: DeepResearchAgent 的状态定义。
"""
from langgraph.graph.message import BaseMessage, add_messages
from typing import Annotated, TypedDict, List, Dict, Any

class ResearchPaper(TypedDict):
    title: str
    url: str
    summary: str
    relevance_score: float

class DeepResearchState(TypedDict):
    """
    DeepResearchAgent 的状态
    """
    # 基础字段
    messages: Annotated[list[BaseMessage], add_messages]
    context: Annotated[list[BaseMessage], add_messages]

    # 业务字段
    research_topic: str  # 研究主题
    sub_topics: List[str] # 拆解的子主题/研究方向
    current_sub_topic: str # 当前正在研究的子主题
    
    found_papers: Annotated[List[ResearchPaper], lambda x, y: x + y] # 收集到的论文 (增量更新)
    knowledge_base: Annotated[List[str], lambda x, y: x + y] # 知识库/笔记 (增量更新)
    
    report_content: str # 最终报告内容
    iteration_count: int # 迭代次数 (防止死循环)

class DeepResearchConfig(TypedDict):
    """
    静态配置
    """
    max_iterations: int
    search_depth: int

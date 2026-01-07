"""
创建时间: 2026-01-02
创建者: LangGraphAgent
描述: DeepResearchAgent 的编排逻辑 (基于 deepagents)。
集成了 Arxiv 搜索工具和自定义的研究规划/报告生成工具。
更新记录:
    [2026-01-05:v1.1:修复了僵尸代码和IO阻塞问题，重构了工具定义]
"""

from deepagents import create_deep_agent
from agent.deep_research_agent.tools import tools as arxiv_tools
from agent.deep_research_agent.node import research_tools
from agent.deep_research_agent.prompts import DEEP_RESEARCH_SYSTEM_PROMPT

# 合并所有工具
all_tools = arxiv_tools + research_tools

# 创建深度研究 Agent
# 使用 deepagents 库的 create_deep_agent 函数
# 传入工具列表和系统提示词
deep_research_agent = create_deep_agent(
    tools=all_tools,
    system_prompt=DEEP_RESEARCH_SYSTEM_PROMPT
)

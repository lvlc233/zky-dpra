"""
开发者: LangGraphAgent
当前版本: v1.1.0
创建时间: 2026-01-25
描述: InPaperChatAgent 提示词 (Agentic RAG)
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

PAPER_CHAT_SYSTEM = """你是一个专门阅读学术论文的 AI 助手。
你的任务是回答用户关于特定论文的问题。

你拥有以下工具：
- `retrieve_paper_tool`: 用于检索论文内容。当用户询问具体细节、定义、实验结果或任何论文内容时，必须使用此工具。

回答原则:
1. **优先检索**: 对于事实性问题，必须先调用检索工具获取证据，严禁编造。
2. **基于证据**: 回答应严格基于工具返回的片段。
3. **引用来源**: 如果可能，在回答中引用页码 (Page X)。
4. **中文回答**: 始终使用中文回答用户。
"""

paper_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", PAPER_CHAT_SYSTEM),
    MessagesPlaceholder(variable_name="messages"),
])

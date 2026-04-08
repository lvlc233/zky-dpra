"""
开发者: LangGraphAgent
当前版本: v1.0.1
创建时间: 2026-01-14
更新时间: 2026-01-24
更新记录: 
    [2026-01-14:v1.0.0:定义 MindMapAgent Prompt]
    [2026-01-24:v1.0.1:更新 Prompt 以支持结构化输出]
"""

from langchain_core.prompts import ChatPromptTemplate

MINDMAP_SYSTEM_PROMPT = """你是一个专业的思维导图生成助手。你的任务是阅读论文内容，并将其结构化为节点(Nodes)和边(Edges)的图结构。

论文内容:
{paper_content}

生成要求:
1. **根节点**: 论文标题 (type='root')。
2. **第一层节点**: 核心章节 (如 Introduction, Methods, Results, Conclusion) (type='main')。
3. **第二层节点**: 章节内的关键点摘要 (type='sub')。
4. **内容**: 节点文本(label)要极其精简，提炼关键词。
5. **边**: 必须正确连接父子节点。
6. **结构**: 请确保生成完整的树状或网状结构，覆盖论文主要内容。
"""

mindmap_generator_prompt = ChatPromptTemplate.from_template(MINDMAP_SYSTEM_PROMPT)

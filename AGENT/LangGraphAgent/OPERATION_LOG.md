
## 2026-01-25 00:09
**行动**: 重构 PaperChatAgent 为 Agentic RAG 并支持 SSE 流式输出。

**详细信息**:
1. **Agentic RAG 重构**
    - 创建 `RetrievalService` (Hybrid Search):
        - 集成 pgvector 向量检索与关键词检索。
        - 实现 RRF (Reciprocal Rank Fusion) 融合算法提升检索相关性。
    - 实现 `retrieve_paper_tool`:
        - 封装 `RetrievalService` 为 LangChain Tool，供 Agent 自主调用。
        - 移除冗余的 Pydantic 模型，使用 `@tool` 装饰器简化定义。
    - 升级 `paper_chat_agent`:
        - 图编排重构为 ReAct 模式 (`agent` -> `tools` -> `agent`)。
        - 节点实现 `agent_node` 绑定工具，`tools_node` 执行工具调用。
        - 提示词优化，强制事实性问题必须调用检索工具。

2. **SSE 流式接口实现**
    - 创建 `api/agent/router.py`:
        - 实现 `POST /stream` 接口，基于 `sse-starlette` 返回 `text/event-stream`。
        - 订阅 `agent.astream_events(version="v2")`，分发 `message` (token流) 与 `tool_*` (工具状态) 事件。
    - 注册路由至 `app.py` (`/api/v1/agent/paper_chat`).

**验证**:
- `RetrievalService` 混合检索逻辑覆盖向量与关键词路径。
- `paper_chat_agent_graph` 编译通过，符合 LangGraph 标准。
- SSE 接口已注册，支持实时流式交互。

**风险**:
- `RetrievalService` 依赖 `PaperChunk` 的 embedding 字段，需确保数据库中该列已正确 populate。
- SSE 连接保持需前端 EventSource 配合处理重连。

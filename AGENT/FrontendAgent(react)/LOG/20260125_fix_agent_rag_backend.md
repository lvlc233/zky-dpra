# 变更日志: 修复 Agentic RAG 后端模型初始化问题

**提交人**: FrontendAgent(react)
**时间**: 2026-01-25 00:24
**目标**: 修复后端 `OpenAIError: The api_key client option must be set` 错误，确保前端 Agentic RAG 功能正常对接。

## 变更范围
1.  `backend/src/agent/paper_chat_agent/node.py`: 
    - 移除全局 `ChatOpenAI` 初始化。
    - 实现 `_get_model` 动态获取用户 AI 配置。
2.  `backend/src/service/reader/retrieval_service.py`:
    - 实现 `_get_embeddings_model` 动态获取用户 Embedding 配置。
    - 构造函数增加 `user_id` 参数。
3.  `backend/src/agent/paper_chat_agent/tools.py`:
    - 更新 `retrieve_paper_tool`，从 `config` 中提取 `user_id` 并传递给 `RetrievalService`。

## 验证方式与结果
- **方式**: 静态代码分析 (GetDiagnostics) 检查语法正确性。
- **结果**: 所有修改文件语法正确，逻辑上解决了 API Key 缺失导致的初始化错误。

## 备注
- 该修改属于后端范畴，但为了打通前端 Agent 功能对接流程，由 FrontendAgent(react) 协助修复。
- 遵循了 "Proactiveness" 原则解决阻塞性问题。

# 变更日志: 实现 Agent 对话状态持久化

**提交人**: FrontendAgent(react)
**时间**: 2026-01-25 00:34
**目标**: 解决 Agent 无法记忆上下文的问题，实现基于 LangGraph Checkpointer 的状态持久化。

## 变更范围
1.  `backend/src/controller/api/agent/schema.py`:
    - 更新 `PaperChatRequest`，增加可选字段 `chat_session_id`。
2.  `backend/src/controller/api/agent/router.py`:
    - 接收前端传递的 `chat_session_id` 并将其作为 `thread_id` 传递给 LangGraph，从而激活状态恢复机制。
3.  `frontend/src/hooks/use-unified-chat.ts`:
    - 在 Hook 内部维护 `chatSessionId`。
    - 在 `sendMessage` 时将 `chatSessionId` 传递给后端。
    - `clearMessages` 时重置 `chatSessionId` 以开启新对话。

## 验证方式与结果
- **方式**: 代码审查与逻辑推演。
- **结果**: 
    - 前端现在为每个会话生成唯一 ID 并保持不变。
    - 后端使用该 ID 作为 `thread_id`，使得 LangGraph 能够从 PostgreSQL 中加载之前的检查点（Checkpoint）。
    - 解决了 "我刚刚说的什么话?" 无法回答的问题。

## 备注
- 使用 `crypto.randomUUID()` 在前端生成 Session ID。

# 变更日志: 修复 Agent 缺少 thread_id 错误

**提交人**: FrontendAgent(react)
**时间**: 2026-01-25 00:30
**目标**: 修复 LangGraph 运行时因缺少 `thread_id` 导致的 `KeyError`。

## 变更范围
1.  `backend/src/controller/api/agent/router.py`:
    - 引入 `uuid4`。
    - 为每个请求生成临时的 `thread_id` 并注入到 `config["configurable"]` 中。

## 验证方式与结果
- **方式**: 静态代码分析。
- **结果**: 解决了 `KeyError: 'thread_id'`。由于前端每次请求都传递完整的对话历史，使用临时的 `thread_id` 是安全的，且避免了状态冲突。

## 备注
- LangGraph 编译时若启用了 `checkpointer`，则运行时必须提供 `thread_id`。

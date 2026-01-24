# 修复 Embedding 服务配置与任务重复问题

**时间**: 2026-01-23 15:55
**目标**: 
1. 解决 `EmbeddingService` 无法使用用户自定义配置的问题（Terminal#59-60）。
2. 解决 `PaperService` 触发异步任务时可能导致的 "job already running elsewhere" 问题（Terminal#70-72）。

**变更范围**:
1. `backend/src/base/embedding/embedding_service.py`: 重构 `EmbeddingService`，支持构造时传入 `api_key`、`base_url` 等配置，并优先使用这些配置。
2. `backend/src/service/papers/paper_service.py`: 
    - 修改 `process_pdf` 方法，在处理前获取用户的 `AgentSettings` 并传递给 Embedding 服务。
    - 修改 `_trigger_process_task` 方法，增加任务去重逻辑（检查 DB 中是否有活跃任务），并使用确定性的 `job_id` 入队。

**验证方式**:
- 代码审查：确认 `EmbeddingService` 初始化逻辑正确回退到全局配置。
- 逻辑推演：确认 `process_pdf` 能正确获取用户配置并传递。
- 逻辑推演：确认 `_trigger_process_task` 在任务存在时返回现有 ID，且使用 `_job_id` 参数防止 Arq 层面重复。

**结果**:
- `EmbeddingService` 现在更加灵活，支持多租户配置。
- 任务调度更加健壮，避免了重复任务导致的资源浪费和错误日志。

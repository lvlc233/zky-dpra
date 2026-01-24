# 2026-01-23 Job SSE and Arq Integration Fix

## 目标
修复后端任务进度无法实时追踪的问题，确保 PDF 解析任务的进度能够通过 SSE (Server-Sent Events) 实时推送到前端。
同时修复 `JobService.create_job` 未实际触发 Arq 任务的问题。

## 变更范围
1.  **Backend Service**:
    -   `backend/src/service/papers/paper_service.py`: 修改 `PaperProcessingService.process_pdf`，增加 `redis` 参数，并在关键步骤通过 Redis 发布进度事件。
    -   `backend/src/service/reader/job_service.py`:
        -   修改 `create_job`，使用 `worker.tasks.task_queue` 实际入队任务。
        -   修改 `subscribe_job_events`，替换 Mock 实现，改为订阅 Redis 频道 `job_progress:{job_id}` 并推送实时事件。

2.  **Worker**:
    -   `backend/src/worker/tasks.py`: 修改 `process_pdf_task`，将 `ctx['redis']` 传递给 `PaperProcessingService`。

## 验证方式
1.  **代码审查**: 确认 `process_pdf` 中包含 `redis.publish` 调用，且 `subscribe_job_events` 包含 `pubsub.subscribe`。
2.  **逻辑验证**:
    -   创建任务 -> `JobService` 入队任务 -> Worker 接收任务。
    -   Worker 执行 -> `PaperProcessingService` 发布 Redis 消息。
    -   `JobService` 订阅 Redis 消息 -> SSE 推送给前端。

## 结果
-   任务创建现在会正确触发后台 Worker。
-   SSE 接口现在返回真实的 Worker 进度数据，而非模拟数据。
-   用户可以实时看到 PDF 解析进度（Parsing -> Extracting -> Splitting -> Embedding -> Saving）。

# 后端任务创建逻辑修复日志

## 变更时间
2026-01-22

## 变更目标
修复创建异步任务（Job）时因缺少 `params_hash` 字段导致的数据库 `IntegrityError`。

## 问题分析
*   **现象**: 用户在上传论文或触发任务时，后端报错 `IntegrityError: null value in column "params_hash" of relation "jobs" violates not-null constraint`。
*   **原因**: `Job` 数据库表的 `params_hash` 字段被定义为 `NOT NULL`（用于幂等性检查），但在 `PaperService` 和 `JobService` 的代码中，创建 `Job` 对象时未给该字段赋值。
*   **额外发现**: `JobService` 中存在多个字段名与数据库实体不匹配的问题（如使用 `id` 而非 `job_id`，`job_type` 而非 `type`）。

## 变更内容

### 后端 (Backend)
1.  **service/papers/paper_service.py**:
    *   在 `_trigger_process_task` 方法中引入 `hashlib`。
    *   在创建 `Job` 之前，基于 `paper_id` 和任务类型计算 MD5 哈希作为 `params_hash`。
    *   将 `params_hash` 传入 `Job` 构造函数。

2.  **service/reader/job_service.py**:
    *   全面修正字段映射：
        *   `id` -> `job_id`
        *   `job_type` -> `type`
        *   `error_message` -> `error`
        *   `completed_at` -> `end_at`
    *   添加 `params_hash` 计算逻辑（基于请求参数 JSON 的 MD5）。
    *   修正 `get_jobs`, `create_job`, `get_job` 中的查询和返回对象构建逻辑，不再依赖可能不匹配的 Pydantic 模型自动转换，而是手动映射以确保准确性。

## 验证结果
*   **代码审查**: 确认所有 `Job` 对象的创建路径均已包含 `params_hash` 字段。
*   **预期效果**: 再次上传论文或触发任务时，数据库插入操作将成功，不再报非空约束错误。

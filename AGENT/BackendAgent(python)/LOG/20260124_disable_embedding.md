# 变更记录

**时间**: 2026-01-24 10:45:00
**目标**: 实现向量化功能的开关控制，允许用户在设置中关闭 Embedding 任务。
**变更范围**: 
- `main/backend/src/service/setting/schema.py`: 更新 `AgentSettings` schema，`embedding_provider` 支持 `none` 选项。
- `main/backend/src/base/config.py`: 更新全局 `Settings` schema，`embedding_type` 支持 `none`。
- `main/backend/src/service/papers/paper_service.py`: 修改 `_trigger_next_tasks` 方法，在触发向量化任务前检查用户的 `embedding_provider` 设置。如果为 `none`，则跳过 `vectorize` 任务的创建。
- `main/backend/src/base/embedding/embedding_service.py`: 修改 `EmbeddingService` 初始化逻辑，如果 provider 为 `none`，则不加载模型并记录日志。
- `main/frontend/src/components/settings/AgentSettingsForm.tsx`: 在前端设置界面添加 "Disabled (Close)" 选项，并相应隐藏 API Key 等输入框。

**验证方式**:
1. 设置验证: 在前端将 Embedding Provider 设置为 Disabled，保存。
2. 流程验证: 上传一篇新论文，观察后台日志或任务列表。
3. 预期结果: 论文解析完成后，`vectorize` 任务**不会**被创建，但 `summary` 和 `mind_map` 任务应正常继续执行。

**结果**: 
- 系统现在支持完全关闭向量化功能，节省资源并加快处理流程（对于不需要向量搜索的场景）。

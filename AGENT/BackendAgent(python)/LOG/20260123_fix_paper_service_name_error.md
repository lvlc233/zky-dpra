# 修复 PaperService 中的 NameError 和配置源问题

**时间**: 2026-01-23 16:10
**目标**: 解决 `PaperService` 中 `AgentSettings` 未定义导致的 `NameError`，并根据用户反馈切换配置源为 `AIReaderSettings`。

**变更范围**:
1. `backend/src/service/papers/paper_service.py`:
    - 移除了 `AgentSettings` 的导入和使用。
    - 修改 `process_pdf` 方法，从 `SettingService.get_settings()` 获取完整的用户配置，并提取 `type='chat'` 的 `AIReaderSettings` 中的 `config`。
    - 修改 `_generate_embeddings` 方法，接收 `embedding_config` 字典而非 `AgentSettings` 对象。

**验证方式**:
- 静态检查：确认 `AgentSettings` 不再被引用，`NameError` 应消除。
- 逻辑确认：`embedding_config` 字典包含了前端 `AI 阅读设置` 中配置的 `embedding_provider`, `embedding_model` 等字段。

**结果**:
- 修复了运行时错误。
- 实现了与前端配置界面的正确对接（使用 AI 阅读设置而非 Agent 设置）。

# 变更日志: 修复 Settings Schema 缺失及前端错误解析

**提交人**: FrontendAgent(react)
**时间**: 2026-01-25 00:28
**目标**: 修复前端无法正确显示后端错误信息的问题，以及后端 Settings Schema 字段缺失导致的配置读取错误。

## 变更范围
1.  `frontend/src/hooks/use-unified-chat.ts`:
    - 增加对 `data.error` 字段的检查，解决 `Unknown error` 显示问题。
2.  `backend/src/service/setting/schema.py`:
    - 在 `Settings` 类中添加 `agent_settings` 字段，确保能正确解析数据库中的 Agent 配置。
3.  `backend/src/service/reader/retrieval_service.py`:
    - 修正配置读取逻辑，从 `agent_settings` 或 `ai_reader_settings` 获取 API Key，而不是不存在的 `search_settings.provider`。

## 验证方式与结果
- **方式**: 静态代码分析。
- **结果**: 
    - 前端现在能正确显示后端传回的 `{"error": "..."}` 格式错误。
    - 后端 Schema 补全后，`SettingService` 能正确加载 Agent 配置，避免因字段缺失导致 API Key 读取失败。
    - `RetrievalService` 逻辑已更新，匹配正确的 Schema 结构。

## 备注
- `SearchSetting` 此前被错误地认为包含 API Key 配置，实际上这些配置位于 `AgentSettings` 或 `AIReaderSettings` 中。

# 更新 AI 阅读设置前端与安全逻辑

**时间**: 2026-01-23 14:16
**目标**: 响应用户需求，在 AI 阅读设置开启向量搜索后，提供内联的 Embedding 模型配置项。
**变更范围**: 
- `main/frontend/src/components/settings/SettingsModal.tsx`: 新增 Embedding 配置 UI（Provider, Model, Base URL, API Key）。
- `main/backend/src/service/setting/setting_service.py`: 增加对 `AIReaderSettings.config` 中 `embedding_api_key` 的安全掩码处理。
**验证方式**: 代码审查与逻辑推演。
**结果**: 实现了配置项的动态显示与安全存储。

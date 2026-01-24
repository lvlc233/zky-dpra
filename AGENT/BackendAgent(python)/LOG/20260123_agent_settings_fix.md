# 修复 Agent Settings 路由导入错误

**时间**: 2026-01-23 14:11
**目标**: 修复 settings_router.py 中缺失的 AgentSettingsRequest/Response 导入
**变更范围**: 
- `main/backend/src/controller/api/settings/settings_router.py`
**验证方式**: 静态代码检查
**结果**: 修复了由于缺少导入导致的 NameError，确保 /settings/agent 接口可用。

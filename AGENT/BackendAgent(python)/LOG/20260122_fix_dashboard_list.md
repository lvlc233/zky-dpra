# 变更记录

**时间**: 2026-01-22 20:55:00
**目标**: 修复前端仪表盘无法显示用户论文列表（显示为空或Mock数据）的问题。
**变更范围**: 
- `main/frontend/src/app/dashboard/page.tsx`: 移除了初始加载时的 Mock Data 注入，启用了 `loadRecentPapers()` 调用，并修正了 `loadRecentPapers` 在成功获取数据后未设置 `hasSearched=true` 导致列表不显示的问题。
- `main/backend/src/controller/api/papers/router.py`: 增加了日志以辅助调试（保留以供观察）。
- `main/backend/src/controller/api/app.py`: 修正 CORS 配置，允许跨域请求。

**验证方式**:
1. 后端验证: 编写 `reproduce_issue.py` 模拟客户端请求 `/api/v1/papers/list`，确认后端正确返回 4 条论文数据。
2. 前端代码审查: 确认 `dashboard/page.tsx` 中存在硬编码的 Mock Data 覆盖逻辑，且 `loadRecentPapers` 未在初始化时调用。
3. 修正后逻辑: 初始化时调用 `loadRecentPapers`，获取真实数据并显示。

**结果**: 
- 后端接口 `/api/v1/papers/list` 正常工作。
- 前端现在可以正确发起请求并展示用户的论文列表。

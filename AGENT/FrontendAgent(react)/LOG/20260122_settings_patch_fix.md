# 2026-01-22 修复配置更新无效问题与方法对齐

**提交人**: FrontendAgent(react)
**时间**: 2026-01-22 15:25:00

## 目标
1.  解决用户反馈的“后端数据更新后样式未变”（即数据未真正持久化）的问题。
2.  将配置更新接口的 HTTP 方法从 `PUT` 改为 `PATCH`，以符合文档规范。

## 变更内容
### 后端 (Backend)
1.  **路由方法修正**:
    *   `src/controller/api/settings/settings_router.py`:
        *   `/reader/ai`: `PUT` -> `PATCH`
        *   `/system`: `PUT` -> `PATCH`
2.  **数据持久化修复**:
    *   `src/service/setting/setting_service.py`:
        *   在 `_save_settings` 方法中引入 `flag_modified(user, "settings")`。
        *   **原因**: SQLAlchemy 默认无法检测 JSON 字段内部属性的变化（如 `user.settings.system_settings` 的修改），导致 `await session.commit()` 时认为数据未变更，从而未执行 SQL UPDATE。强制标记修改后可确保数据写入数据库。

### 前端 (Frontend)
1.  **服务调用修正**:
    *   `src/services/settings.service.ts`:
        *   `updateSystemSettings`: 改用 `request.patch`。
        *   `updateAIReaderSettings`: 改用 `request.patch`。

## 验证建议
1.  **功能验证**:
    *   在前端设置中切换主题（如 Light -> Dark），观察网络请求是否为 `PATCH /settings/system`。
    *   刷新页面，检查是否保持 Dark 模式（这验证了数据已成功写入数据库并被正确读取）。
2.  **接口验证**:
    *   检查 Swagger 文档或网络控制台，确认方法已变更为 PATCH。

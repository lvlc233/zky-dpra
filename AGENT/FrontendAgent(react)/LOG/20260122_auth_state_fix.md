# 2026-01-22 前端 Auth 状态同步修复

**提交人**: FrontendAgent(react)
**时间**: 2026-01-22 15:15:00

## 目标
修复用户注册后自动登录状态未更新到 UI（头像未显示）的问题，以及刷新页面后登录状态可能失效的问题。

## 变更范围
1.  **前端**:
    *   `src/components/auth/RegisterForm.tsx`: 修复 `login` 调用参数错误，正确传递用户信息。
    *   `src/components/providers/AuthProvider.tsx`: 新增组件，负责全局 Auth 状态初始化和 Token 验证。
    *   `src/app/layout.tsx`: 集成 `AuthProvider`。
    *   `src/services/auth.service.ts`: 新增 `getCurrentUser` 方法，并更新 `validateToken`。
    *   `src/components/layout/Navbar.tsx`: 优化头像显示样式。
2.  **后端**:
    *   `backend/src/controller/api/auth/router.py`: 新增 `/users/me` 接口，用于获取当前用户信息。

## 验证方式
1.  **注册自动登录**: 注册新用户后，检查 Navbar 是否立即变为用户头像。
2.  **刷新页面**: 登录状态下刷新页面，检查 Navbar 是否保持用户头像显示。
3.  **Token 验证**: `AuthProvider` 会在后台验证 Token 有效性。

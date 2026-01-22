# 2026-01-22 系统主题持久化修复

**提交人**: FrontendAgent(react)
**时间**: 2026-01-22 15:21:00

## 目标
修复用户登录后，系统主题（如深色模式）设置在页面刷新后失效的问题。

## 问题分析
`ThemeProvider` 默认只从 `localStorage` 读取主题。虽然 `SettingsModal` 保存时会更新后端和 `localStorage`，但在用户首次登录或刷新页面时（特别是在多端同步场景下），前端仅仅从 `localStorage` 读取可能是不够的，或者 `localStorage` 的值可能与后端不一致。
更关键的是，`AuthProvider` 在初始化用户状态时，获取了最新的用户设置（包含主题），但**没有**将这个设置应用到 `ThemeProvider` 中，导致页面刷新后，虽然获取了用户数据，但主题依然停留在默认状态或旧的 `localStorage` 状态。

## 变更范围
1.  **前端**:
    *   `src/components/providers/AuthProvider.tsx`:
        *   引入 `useTheme` Hook。
        *   在 `initAuth` 函数中，当成功获取 `currentUser` 后，检查 `user.settings.system_settings.system_colour`。
        *   如果有值，调用 `setTheme` 强制同步当前主题状态。

## 验证方式
1.  **设置同步**: 登录后，在设置中切换为深色模式并保存。
2.  **刷新保持**: 刷新页面，检查深色模式是否依然生效（之前是会变回浅色或默认值）。

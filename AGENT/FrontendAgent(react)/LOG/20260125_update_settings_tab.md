# 更新 Reader 设置面板 (Update Reader Settings Tab)

**时间**: 2026-01-25 15:45  
**提交人**: FrontendAgent(react)  
**目标**: 将 Reader 侧边栏的 `SettingsTab` 更新为与全局 `SettingsModal` 统一的新版本内容，并适配侧边栏的狭窄布局。

## 变更范围
1.  **UI 重构**:
    *   将 `SettingsTab` 从静态 Mock 页面重构为动态功能页面。
    *   引入了 **AI 模型配置** 区域，允许用户在阅读界面直接修改 Chat/Summary/MindMap 的 LLM 配置 (Provider, Model, Key, URL)。
    *   使用紧凑布局 (Compact Layout) 适配侧边栏宽度：
        *   使用 `text-xs` 和紧凑的 Input/Button 样式。
        *   使用 Tab 切换 (Chat/Summary/MindMap) 而非垂直堆叠所有表单。
2.  **功能集成**:
    *   集成 `settingsService`，实现 `SystemSettings` (外观模式) 和 `AIReaderSettings` (AI 模型配置) 的加载与保存。
    *   添加了保存按钮，支持将修改持久化到后端。
    *   保留了“字体大小”和“分析偏好”作为本地状态 (UI 占位，待后续后端支持)。
3.  **交互优化**:
    *   保存时显示 Loading 状态。
    *   保存成功/失败给予 Toast 反馈。
    *   切换深色/浅色模式时即时生效 (通过 `useTheme` Hook)。

## 验证方式与结果
1.  **外观模式**: 点击“深色/浅色”按钮，界面应即时切换主题，且保存后刷新页面应保持。
2.  **AI 配置**:
    *   加载时应显示后端返回的当前配置。
    *   修改 Provider/Model 等字段后点击保存，再次刷新页面应显示修改后的值。
    *   切换 Agent 类型 (对话/总结/脑图) 应显示对应的配置表单。
3.  **UI 适配**: 在侧边栏宽度下，所有输入框和文字应无溢出，布局整洁。

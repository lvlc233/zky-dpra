# 前端变更日志 - 全局深色模式适配

**时间**: 2026年01月22日 17:21
**变更目标**: 
1. 完成全站深色模式（Dark Mode）适配，覆盖首页、登录/注册页、收藏夹（控制台）、阅读器及各类弹窗。
2. 统一深色模式下的配色方案，确保风格一致性（主要采用 `slate-900` / `slate-800` 色系）。
3. 修复基础 UI 组件在深色模式下的显示问题。

**变更范围**:
- **基础 UI 组件 (`src/components/ui/`)**:
    - `button.tsx`: 移除了依赖未定义 CSS 变量的 `bg-primary` 等类名，替换为具体的 Tailwind 颜色类（如 `bg-indigo-600`），确保按钮在深色模式下可见且美观。
    - `dialog.tsx`: 修复了弹窗背景和边框颜色。
    - `input.tsx`, `scroll-area.tsx`, `switch.tsx`: 验证并确认已包含正确的深色模式样式。

- **功能模块组件**:
    - **搜索 (`src/components/search/`)**: 
        - `SearchBar.tsx`: 更新背景色为 `dark:bg-slate-900`，边框为 `dark:border-slate-700`。
        - `SearchFilters.tsx`: 优化筛选按钮和上传按钮的深色模式样式。
        - `SearchSettings.tsx`: 适配下拉菜单的深色模式。
        - `SearchResults.tsx`: 验证并确认列表项及标签的深色模式显示。
    - **阅读器 (`src/components/reader/`)**:
        - `ReaderNavbar.tsx`, `ReaderSidebar.tsx`, `ReaderRightPanel.tsx`: 统一背景色和边框颜色。
        - `PDFPageOverlay.tsx`: 适配覆盖层的深色样式。
    - **设置 (`src/components/settings/`)**:
        - `SettingsModal.tsx`: 将背景色从 `gray-900` 统一调整为 `slate-900`，确保与全局风格一致。
    - **上传 (`src/components/upload/`)**:
        - `UploadModalFull.tsx`: 适配上传弹窗的各个 Tab 页和输入框。

- **页面 (`src/app/`)**:
    - `page.tsx` (首页): 验证深色模式下的背景和文字颜色。
    - `dashboard/page.tsx`: 验证控制台整体布局背景。
    - `auth/*`: 验证登录、注册表单的深色模式适配。
    - `chat/page.tsx`: 适配 AI 对话页面的输入框和消息气泡。

**验证方式与结果**:
1. **视觉检查**:
    - 首页：背景深色，文字清晰。
    - 登录/注册：表单卡片背景深色，输入框边框清晰。
    - 控制台：侧边栏、搜索栏、列表项颜色一致，无突兀的白色块。
    - 阅读器：PDF 阅读区域、侧边栏、右侧面板风格统一。
    - 弹窗：设置弹窗、上传弹窗、搜索设置弹窗均显示正常。
2. **交互检查**:
    - 按钮 Hover 状态在深色模式下反馈明显。
    - 输入框 Focus 状态光标和边框颜色正确。

**提交人**: FrontendAgent(react)

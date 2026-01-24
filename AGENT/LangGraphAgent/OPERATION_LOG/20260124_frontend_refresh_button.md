# 前端导读刷新功能实现

**时间**: 2026-01-24 11:25:00
**执行者**: LangGraphAgent (协助前端修改)
**目标**: 在阅读页右侧边栏的“论文导读”模块增加刷新按钮，允许用户手动重新获取导读内容。

**变更文件**:
- `main/frontend/src/components/reader/tabs/GuideTab.tsx`

**主要变更**:
1.  **引入图标**: 引入 `RefreshCw` 图标用于刷新按钮。
2.  **逻辑重构**: 
    -   将原 `useEffect` 中的获取逻辑提取为 `fetchSummary` 函数。
    -   增加了 `isManual` 参数，用于区分自动加载和手动刷新。
    -   手动刷新成功或失败时，调用 `toast` 进行提示。
3.  **UI 交互**:
    -   在“论文导读”标题旁增加刷新按钮。
    -   点击按钮时触发 `fetchSummary(true)`。
    -   加载过程中图标增加旋转动画 (`animate-spin`)。
    -   处理了点击冒泡 (`e.stopPropagation()`)，防止误触发折叠。

**效果**:
-   用户点击刷新按钮后，前端会重新请求 `GET /papers/{id}/ai/summary` 接口。
-   如果后台 SummaryAgent 已生成新内容，前端将即时更新显示。
-   解决了用户需刷新整个页面才能看到新生成导读的问题。

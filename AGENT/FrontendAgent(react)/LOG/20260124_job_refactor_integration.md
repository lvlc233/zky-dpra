# FrontendAgent(react) 开发日志

## 2026-01-24: Job系统重构对接

### 变更目标
对接后端 Job 系统重构，实现上传后静默、阅读页自动触发解析、以及后续 AI 任务链的进度展示。

### 变更内容
1.  **ReaderPage (`src/app/reader/[id]/page.tsx`)**:
    -   更新了轮询逻辑：现在不仅检查论文状态 (`status`)，还会持续监控后台任务状态 (`jobStatus`)。即使论文本身标记为 `completed`（正文解析完成），只要有后续 AI 任务（如向量化、总结）在运行，轮询就会继续。
    -   向 `ReaderRightPanel` 传递完整的 `jobStatus` 对象。

2.  **ReaderRightPanel (`src/components/reader/ReaderRightPanel.tsx`)**:
    -   新增 `jobStatus` 属性。
    -   增加了后台任务进度条：当有非阻塞任务（如 `vectorize`, `summary`, `mind_map`）运行时，在右侧面板顶部显示进度条，提示用户 AI 功能正在准备中，而不阻断阅读。

### 验证方式
-   模拟上传流程：上传后直接进入阅读页。
-   状态流转验证：
    -   `pending` -> `processing` (parse_text): 全屏遮罩或 Sidebar 加载（保持原有逻辑）。
    -   `completed` (parse_text done) -> `running` (vectorize): 全屏遮罩消失，显示 PDF，右侧面板显示 "构建知识库索引..." 进度条。
    -   `all done`: 进度条消失，功能完全可用。

### 提交人
FrontendAgent(react)

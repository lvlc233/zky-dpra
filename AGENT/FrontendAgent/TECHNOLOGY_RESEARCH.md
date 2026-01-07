# 前端技术选型与需求分析文档

**文档信息**
- **负责人**: FrontendAgent
- **日期**: 2026-01-06
- **版本**: v1.1 (Context7 调研修正版)
- **关联任务**: T-006

---

## 1. 概述

本项目 DeepPaperResearcher 旨在构建一个融合 AI 深度研究能力的轻量级论文阅读平台。前端需承载 PDF 阅读、复杂标注（视图层）、AI 流式对话、知识图谱可视化等高交互功能。

本技术选型遵循以下原则：
1.  **轻量化**: 避免臃肿的 All-in-one 框架，按需引入。
2.  **高性能**: 针对 PDF 渲染和长列表进行特定优化。
3.  **可维护性**: 严格的 TypeScript 类型约束和模块化架构。
4.  **现代化**: 全面拥抱 React 18+ 和 Next.js App Router 生态。

---

## 2. 核心技术栈 (Core Stack)

| 模块 | 选型 | 理由 |
| :--- | :--- | :--- |
| **框架** | **Next.js 14+ (App Router)** | 官方推荐，天然支持 SSR/SSG，路由系统完善，便于 SEO 和首屏优化。 |
| **语言** | **TypeScript 5.x** | 强制类型安全，配合 strict 模式，减少运行时错误。 |
| **样式** | **TailwindCSS** | 原子化 CSS，开发效率高，配合 PostCSS 构建体积小。 |
| **组件库** | **Shadcn/UI** (基于 Radix UI) | **Headless UI + Tailwind** 方案，代码可控性强，方便定制“视图”等特殊交互组件。 |
| **图标** | **Lucide React** | 风格统一，轻量，Shadcn 默认推荐。 |

---

## 3. 关键功能模块选型 (Detailed Selection)

### 3.1 PDF 阅读与“视图”层 (Core Feature)
*   **需求**: 加载 PDF，实现不破坏原文件的“视图”覆盖（高亮、划线、笔记）。
*   **选型**: **react-pdf** (by wojtekmaj) + **Custom SVG/DOM Overlay** (交互层)。
*   **调研结论**:
    *   经 Context7 调研，`react-pdf` (171 snippets, Score 76.3) 仍是 React 生态中最成熟的 PDF **渲染**库。
    *   `react-pdf-highlighter` 虽然开箱即用，但其标注逻辑较封闭。为了实现本项目核心的“多视图叠加”和“玻璃板”概念，我们需要完全控制标注层的渲染（Z-Index, 坐标映射），因此坚持使用 `react-pdf` 作为底层渲染引擎，上层自研标注交互。

### 3.2 知识图谱可视化 (Graph Visualization)
*   **需求**: 展示论文引用关系、概念关联图，支持框选（Lasso）和高性能渲染。
*   **选型**: **Reagraph** (基于 WebGL/Three.js)。
*   **变更理由**: 原定 `react-force-graph`。
    *   经 Context7 调研，**Reagraph** (Benchmark 92.6) 提供了更现代的 React API（如 `<GraphCanvas renderNode={...} />`），支持声明式的自定义节点渲染（基于 React Three Fiber 范式），并且**开箱即用支持 Lasso (套索) 选择**。这对于用户批量选中论文进行“AI 深度分析”是非常关键的交互特性。

### 3.3 AI 交互与流式响应 (AI Interaction)
*   **需求**: 接收后端 AI 推送的流式 Token，同时处理“中间状态”（如：正在搜索 Google、正在阅读 PDF）。
*   **选型**: **Vercel AI SDK (Core + React)**。
*   **变更理由**: 原定 `@microsoft/fetch-event-source`。
    *   `Vercel AI SDK` (Snippet count > 3000) 是 Next.js 生态事实标准。
    *   它提供了 **Data Streams** (`createUIMessageStream`) 功能，允许后端在发送文本 Token 的同时，发送自定义 JSON 数据（如 `{ type: 'tool_call', status: 'reading_pdf' }`）。这完美解决了“Deep Research”长流程中需要实时反馈进度给 UI 的需求，而无需建立额外的 WebSocket 连接。
    *   `useChat` 和 `useCompletion` Hooks 极大简化了状态管理。

### 3.4 状态管理 (State Management)
*   **选型**:
    *   **Server State**: **TanStack Query (React Query) v5**。
    *   **Global Client State**: **Zustand**。
    *   *理由保持不变*: 轻量、高性能、DevTools 支持好。

---

## 4. 架构设计 (Architecture)

### 4.1 目录结构 (App Router)
```text
src/
├── app/                    # 路由层
│   ├── (dashboard)/        # 主应用区
│   │   ├── graph/          # 知识图谱页 (新增)
│   │   ├── library/        # 论文管理页
│   │   └── reader/[id]/    # 阅读器页
│   └── api/                # Next.js API Routes (AI SDK 转发)
├── components/
│   ├── ui/                 # Shadcn 组件
│   ├── graph/              # Reagraph 封装组件
│   ├── pdf/                # PDF 核心组件
│   └── ai/                 # 聊天/进度反馈组件
├── lib/
│   └── ai/                 # AI SDK 配置
```

### 4.2 关键交互流程 (AI Deep Research)
1.  用户在**图谱**或**列表**中选中多篇论文 (Reagraph Lasso Selection)。
2.  点击“深度研究”。
3.  前端调用 `useChat` 发送请求。
4.  后端 (LangGraph) 开始运行，通过 `streamText` + `DataStream` 返回：
    *   `data: { status: 'planning' }` -> UI 显示“正在规划任务...”
    *   `data: { status: 'reading', file: 'p1.pdf' }` -> UI 显示“正在阅读 p1.pdf...”
    *   `text: "根据您的..."` -> UI 流式显示最终报告。

---

## 5. 下一步计划
1.  提交本技术文档供审核 (T-007)。
2.  待审核通过后，输出详细的实现规范文档 (T-008)。

# 后端接口需求文档 (草稿)

**创建者**: FrontendAgent  
**日期**: 2026-01-11  
**状态**: Draft / Pending Review  
**描述**: 本文档基于前端 UI 设计稿及当前已实现的组件架构（特别是 Reader 模块），梳理了后端需提供的 API 接口规范。

---

## 1. 核心原则
1.  **RESTful 风格**: 资源导向，使用标准 HTTP 动词。
2.  **统一响应格式**: `{ "code": 200, "data": ..., "message": "success" }`。
3.  **流式支持**: AI 相关接口（对话、翻译、深度研究）需支持 Server-Sent Events (SSE)。
4.  **鉴权**: 所有接口需通过 Bearer Token 鉴权（除了登录/注册）。

---

## 2. 接口清单

### 2.1. 文献管理 (Paper Management)

用于 `Dashboard` 和 `Manager` 页面。

| 方法 | 路径 | 描述 | 参数示例 |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/papers/upload` | 上传文献 (支持单文件/文件夹/URL) | `FormData`: `file`, `url`, `folderId` |
| `GET` | `/api/papers` | 获取文献列表 (分页/搜索/筛选) | `Query`: `page`, `limit`, `keyword`, `tags`, `collectionId` |
| `GET` | `/api/papers/{id}` | 获取文献元数据详情 | - |
| `PUT` | `/api/papers/{id}` | 更新文献元数据 (标题/作者/标签) | `Body`: `{ title, tags, ... }` |
| `DELETE` | `/api/papers/{id}` | 删除文献 | - |
| `GET` | `/api/papers/{id}/status` | 查询解析/处理状态 (轮询用) | - |

### 2.2. 阅读器核心 (Reader Core)

用于 `Reader` 页面初始化。

| 方法 | 路径 | 描述 | 参数示例 |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/papers/{id}/pdf` | 获取 PDF 文件流或预签名 URL | - |
| `GET` | `/api/papers/{id}/toc` | 获取 PDF 目录结构 | - |

### 2.3. 图层与标注 (Layers & Annotations)

支持 "View as Layer" 架构。所有标注必须归属于某个 Layer。

**数据模型 (Layer)**:
```typescript
interface Layer {
  id: string;
  paperId: string;
  name: string;
  type: 'system' | 'user'; // system: 默认层, user: 自定义层
  visible: boolean;
  ownerId: string;
}
```

**数据模型 (Annotation)**:
```typescript
interface Annotation {
  id: string;
  layerId: string;
  type: 'highlight' | 'note' | 'translate';
  rects: Array<{x, y, width, height, pageIndex}>; // 百分比坐标
  content?: string;
  color?: string;
}
```

| 方法 | 路径 | 描述 | 参数示例 |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/papers/{id}/layers` | 获取某篇论文的所有图层 | - |
| `POST` | `/api/papers/{id}/layers` | 创建新图层 | `Body`: `{ name }` |
| `DELETE` | `/api/layers/{layerId}` | 删除图层 | - |
| `GET` | `/api/layers/{layerId}/annotations` | 获取图层下的所有标注 | - |
| `POST` | `/api/layers/{layerId}/annotations` | 添加标注 | `Body`: AnnotationData |
| `PUT` | `/api/annotations/{id}` | 更新标注 (颜色/内容) | `Body`: PartialAnnotation |
| `DELETE` | `/api/annotations/{id}` | 删除标注 | - |

### 2.4. AI 辅助服务 (AI Services)

用于 `ReaderRightPanel` 及 `PDFPageOverlay`。

#### 2.4.1. 导读与对话 (Guide & Chat)
*   **流式响应 (SSE)**: 需返回 `event: message`, `data: { chunk: "..." }`。
*   **上下文**: 需支持携带 `currentSelection` (选中文本) 或 `currentLayerId` (当前视图上下文)。

| 方法 | 路径 | 描述 | 参数示例 |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/papers/{id}/guide` | 获取/生成 AI 导读 (摘要/关键点) | - |
| `POST` | `/api/ai/chat` | 发送对话消息 (SSE) | `Body`: `{ paperId, history, query, context: { selection, layerId } }` |

#### 2.4.2. 翻译 (Translate)
用于 `PDFPageOverlay` 的瞬时翻译功能。

| 方法 | 路径 | 描述 | 参数示例 |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/ai/translate` | 翻译文本 (SSE 可选) | `Body`: `{ text, targetLang }` |

#### 2.4.3. 知识图谱 (Graph)
用于 `GraphTab`。

| 方法 | 路径 | 描述 | 参数示例 |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/papers/{id}/graph` | 获取知识图谱数据 | 返回 `{ nodes, edges }` |
| `POST` | `/api/papers/{id}/graph/regenerate` | 重新生成图谱 | - |

#### 2.4.4. 深度研究 (Deep Research / Report)
用于 `ReportTab`。这是一个长耗时任务。

| 方法 | 路径 | 描述 | 参数示例 |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/research/start` | 开启深度研究任务 | `Body`: `{ paperId, focusPoints[] }` |
| `GET` | `/api/research/{taskId}` | 获取任务状态及流式日志 | 返回状态 (`pending`/`processing`/`completed`) 及当前生成的 Markdown |
| `GET` | `/api/papers/{id}/reports` | 获取该论文的历史报告列表 | - |

### 2.5. 收藏夹与搜索 (Collections & Search)

| 方法 | 路径 | 描述 | 参数示例 |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/collections` | 获取收藏夹列表 | - |
| `POST` | `/api/collections` | 创建收藏夹 | `Body`: `{ name }` |
| `POST` | `/api/collections/{id}/papers` | 向收藏夹添加论文 | `Body`: `{ paperIds: [] }` |
| `GET` | `/api/search` | 全局搜索 (支持 AI 增强) | `Query`: `{ q, mode: 'keyword'|'semantic', useAI: boolean }` |

---

## 3. 特殊交互说明

1.  **坐标系统**: 前端 `Rect` 使用百分比坐标 (0-100)，后端存储时请保持该格式，不要转换为绝对像素，以适应不同分辨率的渲染。
2.  **瞬时模式 (Transient Mode)**: 翻译操作的前端状态是临时的，但如果用户点击 "保存为笔记"，则会调用 `POST /annotations` 接口将翻译结果作为 `content` 存入笔记。
3.  **图层合并**: 当前端请求 "导出 PDF" 时，后端可能需要支持将指定 Layer 的标注 "烧录" (Burn-in) 到 PDF 文件中并返回新的 PDF 流。


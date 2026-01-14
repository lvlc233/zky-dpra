# 后端系统架构需求分析文档

**文档信息**
- **负责人**: BackendAgent
- **日期**: 2026-01-07
- **关联任务**: T-012
- **版本**: v1.0

---

## 1. 概述

本文档旨在基于项目规格说明书、产品需求文档以及前端和Agent端的设计文档，对后端系统进行详细的需求分析。后端主要承担数据管理、业务逻辑处理、以及作为Frontend和LangGraph Agent之间的桥梁。

## 2. 功能需求分析

### 2.1 核心业务功能
1.  **用户与权限管理** (Infra/Auth)
    *   支持用户注册、登录。
    *   基于 `PyJWT` 的 Token 验证机制。
    *   区分普通用户与管理员（如果需要），目前主要关注单用户/多用户隔离。

2.  **论文管理** (Core/Paper)
    *   **上传与导入**: 支持本地 PDF 上传、URL (Arxiv) 导入。
    *   **元数据管理**: 存储标题、作者、摘要、发布日期、来源等。
    *   **解析与处理**:
        *   集成 `Marker` 或类似工具进行 PDF 转 Markdown (异步任务)。
        *   文本切片 (Chunking) 用于向量存储。
    *   **存储**:
        *   元数据存入 PostgreSQL。
        *   PDF 文件存入本地文件系统或 MinIO。
        *   向量数据存入 PGVector。

3.  **阅读器支持** (Core/Reader)
    *   **文件服务**: 提供 PDF 文件流访问。
    *   **目录支持 (TOC)**: 提取 PDF 目录结构，支持跳转。
    *   **视图层 (View Layer)**:
        *   实现 "View" 概念，即用户对论文的个性化标注层。
        *   支持高亮 (Highlight)、笔记 (Note)、划线 (Underline) 的 CRUD。
        *   视图数据需与特定论文版本关联。

4.  **收藏夹管理** (Core/Collection)
    *   **创建与管理**: 用户可创建多个收藏夹，自定义名称和描述。
    *   **论文关联**: 支持将论文添加到收藏夹，实现多对多管理。
    *   **私有化**: 默认私有，仅创建者可见。

5.  **知识图谱支持** (Core/Graph)
    *   提供图谱所需的节点 (Node) 和边 (Edge) 数据。
    *   支持基于引用的自动关联。
    *   支持基于内容的语义关联 (通过向量相似度计算)。

### 2.2 Agent 交互支持
1.  **LangGraph 集成**
    *   作为 LangGraph 的运行时环境 (Runtime Host)。
    *   提供统一的 Agent 调用接口 (`POST /api/agent/chat`)。
    *   **流式响应 (SSE)**: 支持 `text`, `tool_call`, `status`, `error` 等事件的流式推送。

2.  **RAG 混合检索**
    *   实现基于 PostgreSQL 的混合检索逻辑 (Hybrid Search)。
    *   结合 `pgvector` (语义检索) 和 `Full-Text Search` (关键词检索)。
    *   实现 RRF (Reciprocal Rank Fusion) 排序算法。

## 3. 非功能需求分析

1.  **性能**
    *   **向量检索**: 在百万级切片数据下保持毫秒级响应 (需合理索引)。
    *   **PDF 加载**: 支持大文件 (100MB+) 的流式传输和断点续传。
    *   **并发**: 利用 FastAPI 的异步特性处理高并发 I/O (数据库、网络请求)。

2.  **可扩展性**
    *   **模块化**: 严格遵循 Controller-Service-Data 分层架构。
    *   **异步任务**: 耗时操作 (PDF 解析、长 Agent 任务) 需支持后台执行，避免阻塞主线程。

3.  **规范性**
    *   严格遵守 `PROJECT/SPECIFICATION.md` 中的代码规范。
    *   所有 API 输入输出使用 Pydantic 模型。
    *   数据库交互使用 SQLModel。

## 4. 系统架构分析

### 4.1 分层架构设计
遵循 3+1 层架构：

*   **Controller Layer (`src/controller`)**:
    *   处理 HTTP 请求/响应。
    *   参数校验 (Pydantic)。
    *   权限控制 (Dependency Injection)。
    *   SSE 事件流封装。
    
*   **Service Layer (`src/service`)**:
    *   业务逻辑核心。
    *   协调 Data Layer 和 Agent Runtime。
    *   示例: `PaperService` 处理上传逻辑，调用 `FileStorage` 保存文件，调用 `MarkerService` 解析，调用 `VectorService` 存向量。

*   **Data Layer (`src/business_model` & `src/base`)**:
    *   **Entity**: SQLModel 定义的数据库表结构。
    *   **Repository/DAO**: 封装 SQL 操作 (CRUD)。
    *   **Infrastructure**: Redis, Neo4j, MinIO 的客户端封装。

*   **Agent Layer (`src/agent`)**:
    *   LangGraph 图定义。
    *   Tool 定义。
    *   Prompt 管理。

### 4.2 关键数据流
1.  **Deep Research 流程**:
    *   Frontend -> Controller (`/chat`) -> Service (`AgentService`) -> LangGraph (`ResearchAgent`)
    *   Agent -> Tools (`SearchTool`, `RAGTool`) -> Database (`PGVector`)
    *   Agent -> SSE Stream -> Frontend

2.  **PDF 解析流程**:
    *   Upload -> Controller -> Service (Save File) -> Background Task (Marker Parse) -> Update DB (Content & Vector)

## 5. 数据模型需求 (初步)

基于 `LangGraphAgent` 的建议和业务需求，主要实体包括：

*   **User**: `id`, `username`, `password_hash`, ...
*   **Paper**: `id`, `title`, `url`, `local_path`, `authors` (JSON), `publish_date`, `status` (parsing/ready), `toc` (JSON).
*   **PaperChunk**: `id`, `paper_id`, `content`, `embedding` (Vector), `metadata` (page_num, section).
*   **Collection**: `id`, `user_id`, `name`, `description`.
*   **Annotation/View**: `id`, `paper_id`, `user_id`, `type` (highlight/note), `position` (JSON/percentage), `content`.
*   **AgentSession**: `id`, `user_id`, `agent_type`, `history` (JSON/Pickle), `created_at`.

## 6. 接口需求概览

| 模块 | 方法 | 路径 | 描述 |
| :--- | :--- | :--- | :--- |
| **Auth** | POST | `/api/auth/login` | 登录 |
| **Paper** | GET | `/api/papers` | 获取论文列表 (支持分页、搜索) |
| **Paper** | POST | `/api/papers/upload` | 上传论文 |
| **Paper** | GET | `/api/papers/{id}/view` | 获取论文文件流 |
| **Agent** | POST | `/api/agent/chat` | Agent 对话 (SSE) |
| **Graph** | GET | `/api/graph/data` | 获取图谱数据 |

## 7. 结论与下一步

后端需重点构建支持向量检索的 PostgreSQL 环境，并封装高效的 PDF 解析与切片服务。Agent 的集成将通过 Service 层调用 LangGraph 编译后的 Runnable 来实现。

**下一步 (T-013)**: 进行具体的技术选型分析，确认使用的第三方库版本、数据库配置细节以及具体的目录结构调整。

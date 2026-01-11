# BackendAgent 记忆文档

## 项目核心概念理解

### 项目整体目标
- DeepResearcher：基于 LangGraph 的 AI 辅助论文研究与管理平台
- 采用"3+1"层后端架构（Controller + Service + Infrastructure + Data）
- 通过严格的工作流（AGENT开发 → SUBMISSION提交 → 主项目合并）进行迭代

### BackendAgent 职责
- 负责后端业务逻辑的实现
- 专注于 Controller、Service、Infrastructure、Data 层的开发
- 严格遵守资源约束（仅在 AGENT/BackendAgent/ 目录下操作）
- 所有代码需经管理员审核后方可合并至主项目

## 当前任务理解

### 任务 v0.2 - 核心服务与数据库构建 (T-016, T-017)
**目标**：构建后端核心数据底座与文件处理服务

**技术范围**：
- **Data**: SQLModel + PGVector 实现用户、论文、向量切片模型
- **Service**: 论文上传、状态管理、PDF解析、向量化
- **Worker**: Arq 异步任务队列处理耗时操作
- **Infrastructure**: PDF解析器 (Marker/PyMuPDF), Embedding服务 (OpenAI/Ollama)

**关键约束**：
- **导包规范**：严禁使用 `.../` 相对导入，必须使用绝对导入（如 `from base.arxiv.parser import ...`）
- **目录规范**：
    - ORM 实体必须在 `src/base/pg/entity.py`
    - Service 必须在 `src/service/papers/`
- **时间戳**：使用中国上海时区

## 技术栈认知

### 后端核心依赖
- **Web框架**: FastAPI
- **数据库**: PostgreSQL (数据) + pgvector (向量)
- **ORM**: SQLModel
- **异步队列**: Arq + Redis
- **依赖管理**: uv
- **PDF解析**: marker-pdf / PyMuPDF
- **Embedding**: OpenAI / Ollama

## 开发模式记忆

### 分层架构规则 (严格执行)
- **Controller**: `src/controller/` - 路由、参数校验、鉴权
- **Service**: `src/service/` - 业务逻辑编排
- **Infrastructure**: `src/base/` - 基础组件 (DB, Redis, PDF Parser, Arxiv Client)
- **Data**: `src/base/pg/entity.py` (ORM), `src/business_model/` (Pydantic schemas)

### 导包规范 (2026-01-08 新增)
- ❌ 错误：`from ...base.arxiv.parser import ArxivXmlParser`
- ✅ 正确：`from base.arxiv.parser import ArxivXmlParser` (假设在src目录下)
- 这里的根目录通常指 `src` 目录被添加到 python path 中，或者使用完整的包路径。

## 项目演进历史

### 阶段一：基础功能 v0.1 (2026-01-02)
- 完成基础 Arxiv 论文获取接口
- 确立 Controller-Service-Infra 分层架构
- 修复安全漏洞与依赖注入问题

### 阶段二：系统设计 (2026-01-07)
- **需求分析**: 确定 User, Paper, Chat 核心实体与交互流程
- **技术选型**: 确认使用 Arq 处理异步任务，PGVector 存向量
- **接口设计**: 定义 `/auth`, `/papers`, `/chat` 路由规范

### 阶段三：核心实现 (2026-01-08)
- **数据库模型**: 实现 `User`, `Paper`, `PaperChunk`, `ChatSession` (位于 `base/pg/entity.py`)
- **PaperService**: 实现文件上传与状态流转 (位于 `service/papers/paper_service.py`)
- **Worker**: 集成 Arq 实现 PDF 异步解析与向量化 (`worker/tasks.py`)
- **Infrastructure**:
    - `base/pdf_parser`: 封装 Marker/PyMuPDF
    - `base/embedding`: 封装 OpenAI/Ollama

## 关键经验与教训 (最新)

### 架构与路径修正 (2026-01-08)
1. **ORM位置**: 之前错误放在 `business_model`，现已强制统一到 `src/base/pg/entity.py`。
2. **Service位置**: 之前错误放在 `base/service`，现已强制统一到 `src/service/papers/`。
3. **导入路径**: 相对导入（`...`）会导致模块解析错误，必须使用绝对路径或基于根模块的导入。

### 异步任务处理
- 耗时操作（PDF解析、Embedding）必须通过 Arq 异步化，避免阻塞 Web 线程。
- 任务状态需要持久化到数据库，以便前端轮询或 SSE 推送。

---
**最后更新**: 2026年01月08日 17:00
**记忆版本**: v1.2


管理员补充: 业务模型已下层到common中命名为model了
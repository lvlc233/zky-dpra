# 项目统一技术架构文档 (Unified Technical Architecture)

> **版本**: v1.1
> **日期**: 2026-01-12
> **提交方**: BackendAgent
> **状态**: 正式 (Official)
> **说明**: 本文档作为项目开发的唯一技术事实来源 (Single Source of Truth)，消除了 Frontend、Backend 和 Agent 设计文档中的差异。已同步 v1.0 前端 API 需求。

---

## 1. 系统架构概览

采用 **前后端分离** + **Agent 编排** 的架构。

*   **前端**: Next.js 14 (App Router) + Zustand + Vercel AI SDK
*   **后端**: FastAPI + SQLModel + PostgreSQL (pgvector) + Arq (Async Tasks)
*   **Agent**: LangGraph (图编排) + LangChain (工具调用)

### 1.1 职责划分
*   **Infrastructure / Service Layer**: 负责重型计算和IO密集型任务（如 PDF 解析、OCR、向量化）。这些任务通过 `Arq` 异步队列执行，状态记录在 DB 中。
*   **Agent Layer**: 负责业务逻辑推理、多步决策和上下文管理。Agent 不直接进行 PDF 解析，而是查询 Service Layer 处理好的数据。

---

## 2. 统一数据库设计 (Database Schema)

基于 BackendAgent 的设计进行增强，统一字段类型。

### 2.1 用户 (Users)
```python
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2.2 论文 (Papers)
```python
class PaperStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Paper(SQLModel, table=True):
    __tablename__ = "papers"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    title: str = Field(index=True)
    # 统一使用 JSON 字段存储作者列表
    authors: List[str] = Field(sa_column=Column(JSON)) 
    abstract: Optional[str] = None
    
    # 存储
    file_key: str  # MinIO / Local Storage Path
    file_url: Optional[str] = None
    
    # 状态管理
    status: PaperStatus = Field(default=PaperStatus.PENDING)
    error_message: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 关联
    chunks: List["PaperChunk"] = Relationship(back_populates="paper")
    # LangGraphAgent 提到的摘要关联，可预留
    summaries: List["PaperSummary"] = Relationship(back_populates="paper")
```

### 2.3 向量切片 (PaperChunks)
```python
class PaperChunk(SQLModel, table=True):
    __tablename__ = "paper_chunks"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    paper_id: UUID = Field(foreign_key="papers.id", index=True)
    
    content: str
    page_number: Optional[int] = None
    chunk_index: int
    
    # pgvector 1536 dim (OpenAI Small)
    embedding: List[float] = Field(sa_column=Column(Vector(1536)))
    
    paper: Paper = Relationship(back_populates="chunks")

### 2.4 收藏夹 (Collections)
```python
class Collection(SQLModel, table=True):
    __tablename__ = "collections"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # 关联
    # papers: 通过 CollectionPaper 中间表关联
```

```python
class CollectionPaper(SQLModel, table=True):
    __tablename__ = "collection_papers"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    collection_id: UUID = Field(foreign_key="collections.id")
    paper_id: UUID = Field(foreign_key="papers.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2.5 会话与消息 (Chat)
用于持久化对话记录。LangGraph 的 Checkpoint 可选择存储在 Postgres 的独立表中，但业务层查询历史使用此表。

```python
class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str
    # 新增: 标记该会话使用的 Agent 类型 (如 "search", "chat", "summary")
    agent_type: str = Field(default="chat") 
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    messages: List["ChatMessage"] = Relationship(back_populates="session")

class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chat_sessions.id", index=True)
    
    role: str # "user", "assistant", "system"
    content: str
    
    # 引用来源 JSON [{"paper_id": "...", "chunk_id": "..."}]
    sources: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    session: ChatSession = Relationship(back_populates="messages")
```

---

## 3. 统一 API 接口 (API Interface)

采用 RESTful 风格，URL 前缀 `/api/v1`。

### 3.1 接口概览
详细定义请参考 `FRONTEND_TO_BACKEND_API_REQ.md`。

| 模块 | Method | Path | 说明 |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/login` | 登录 (JWT) |
| | `POST` | `/api/v1/auth/register` | 注册 |
| | `GET` | `/api/v1/users/me` | 获取当前用户信息 |
| **Papers** | `POST` | `/api/v1/papers/upload` | 上传论文 |
| | `GET` | `/api/v1/papers` | 列表 |
| | `GET` | `/api/v1/papers/{id}` | 详情 |
| | `GET` | `/api/v1/papers/{id}/status` | 状态轮询 |
| **Reader** | `GET` | `/api/v1/papers/{id}/layers` | 获取图层 |
| | `POST` | `/api/v1/layers/{layerId}/annotations` | 添加标注 |
| **Chat** | `POST` | `/api/v1/chat/sessions` | 创建会话 |
| | `POST` | `/api/v1/chat/sessions/{id}/message` | 发送消息 (SSE) |
| **Reports** | `POST` | `/api/v1/papers/{id}/reports` | 生成报告 |
| | `GET` | `/api/v1/reports/{id}` | 获取报告 |

### 3.2 SSE 交互协议 (Unified SSE Protocol)
前端与 Agent 的流式交互必须遵循以下事件定义：

| Event Name | Data Structure | Description |
| :--- | :--- | :--- |
| `metadata` | `{"run_id": "...", "session_id": "..."}` | 会话元数据，连接建立时发送 |
| `token` | `"Hello"` (string) | LLM 生成的文本片段 (Delta) |
| `tool_call` | `{"tool_name": "search", "args": "query..."}` | Agent 开始调用工具 |
| `tool_result` | `{"tool_name": "search", "result": "..."}` | 工具调用结束，返回结果 |
| `error` | `{"code": 500, "message": "..."}` | 发生异常 |
| `finish` | `{"reason": "stop"}` | 响应结束 |

> **注意**: 废弃 `thought` 事件，统一归类为 `token` (如果是 CoT 模型) 或通过 `tool_call` 隐式表达思考过程。

---

## 4. Agent 设计规范

### 4.1 Agent 类型
1.  **SearchAgent**: 混合检索 (Arxiv API + Local Vector DB)。
2.  **InPaperChatAgent**: 针对单篇论文的 RAG 问答。
3.  **DeepResearchAgent**: (高级) 自动规划、多步检索、生成报告。

### 4.2 状态管理
*   使用 `LangGraph` 的 `MemorySaver` (Postgres checkpointer) 进行图状态的持久化。
*   同时将**对用户可见**的消息同步写入 `ChatMessage` 表，以便前端历史记录列表查询。

### 4.3 工具 (Tools)
Agent 不直接操作数据库，而是通过 Service 层封装的函数进行操作。
*   `search_local_papers(query: str)` -> 调用 Vector Store 检索。
*   `get_paper_content(paper_id: str)` -> 从 DB 获取全文/摘要。

---

## 5. 前端适配指南

*   **PDF Viewer**: 使用 `react-pdf`。
*   **Chat UI**: 使用 `useChat` hook。需自定义 `onFinish` 或 `onResponse` 处理非标准 SSE 事件 (如 `tool_call`) 用于显示 UI 上的 "正在检索..." 状态。
*   **Graph**: 使用 `reagraph` 渲染知识图谱，数据源来自 `MindMapAgent` 的输出或后端图数据库查询接口。


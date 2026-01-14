# 定义pg数据库的实体映射。 

'''
开发者: BackendAgent
当前版本: v1.3_db_models
创建时间: 2026年01月08日 11:00
更新时间: 2026年01月12日 08:00
更新记录:
    [2026年01月08日 11:00:v1.0_db_models:创建数据库模型文件，包含所有核心表结构]
    [2026年01月08日 16:30:v1.1_db_models:从/src/business_model/database_models.py迁移到/src/base/pg/entity.py中]
    [2026年01月12日 07:50:v1.2_db_models:为所有实体类添加详细文档注释(Docstring)]
    [2026年01月12日 08:00:v1.3_db_models:为数据库表和字段添加物理注释(Comment)，支持数据库级元数据查看]
'''

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from pgvector.sqlalchemy import Vector
from sqlmodel import Field, Relationship, SQLModel

from common.model.enums import PaperStatus


class User(SQLModel, table=True):
    """
    用户表模型 (User Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00
    
    用途:
        存储系统用户的基本信息、认证凭据及状态。
    
    使用场景:
        - 用户注册、登录认证 (Auth Service)。
        - 关联用户上传的论文、聊天记录、阅读标注等资源。
        - 权限控制与用户信息查询。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'users'。
        - id: 使用 UUID 作为主键，确保全局唯一性。
        - email: 唯一索引，用于登录标识。
        - hashed_password: 存储加密后的密码哈希值，而非明文。
        - is_active: 软删除标记，用于禁用用户而非直接删除数据。
        - 关联: 
            - papers: 一对多关联 Paper 表。
            - chat_sessions: 一对多关联 ChatSession 表。
    """
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表: 存储系统用户的基本信息、认证凭据及状态"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "用户全局唯一标识(UUID)"}
    )
    email: str = Field(
        unique=True, 
        index=True,
        sa_column_kwargs={"comment": "用户邮箱(登录账号)"}
    )
    hashed_password: str = Field(
        sa_column_kwargs={"comment": "加密后的密码哈希值"}
    )
    full_name: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "用户全名/昵称"}
    )
    is_active: bool = Field(
        default=True,
        sa_column_kwargs={"comment": "账号是否激活(True:激活, False:禁用/删除)"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "账号创建时间"}
    )

    # 关联关系
    papers: List["Paper"] = Relationship(back_populates="user")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    collections: List["Collection"] = Relationship(back_populates="user")


class CollectionPaper(SQLModel, table=True):
    """
    收藏夹-论文关联表 (Collection Paper Association)
    
    注释者: BackendAgent
    注释时间: 2026-01-12 15:00:00
    
    用途:
        实现收藏夹与论文的多对多关联。
    """
    __tablename__ = "collection_papers"
    __table_args__ = {"comment": "收藏夹-论文关联表"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "关联ID"}
    )
    collection_id: UUID = Field(
        foreign_key="collections.id",
        primary_key=False,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "收藏夹ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        primary_key=False,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "论文ID"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "收藏时间"}
    )


class Collection(SQLModel, table=True):
    """
    收藏夹表模型 (Collection Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 15:00:00

    用途:
        存储用户创建的论文收藏夹/合集。

    使用场景:
        - 用户创建自定义分类收藏夹。
        - 将论文添加到收藏夹以便管理。
    """
    __tablename__ = "collections"
    __table_args__ = {"comment": "收藏夹表: 用户自定义的论文集合"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "收藏夹ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属用户ID"}
    )
    name: str = Field(
        index=True,
        sa_column_kwargs={"comment": "收藏夹名称"}
    )
    description: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "描述"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联关系
    user: User = Relationship(back_populates="collections")
    # 通过中间表关联论文
    # papers: List["Paper"] = Relationship(link_model=CollectionPaper) # 暂不直接定义反向，按需查询


class Paper(SQLModel, table=True):
    """
    论文表模型 (Paper Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储用户上传或导入的论文元数据及处理状态。

    使用场景:
        - 论文列表展示与详情查询。
        - 论文上传、解析状态跟踪 (Pending -> Processing -> Completed)。
        - 关联论文的向量切片 (Chunks)、摘要 (Summaries) 和阅读标注 (Layers/Annotations)。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'papers'。
        - user_id: 外键关联 Users 表，标识论文归属。
        - authors: 使用 JSON 类型存储作者列表，灵活适应不同数量的作者。
        - file_key: 存储对象存储 (如 MinIO) 中的文件路径或 Key。
        - status: 枚举类型 (PaperStatus)，管理论文处理生命周期。
        - 关联:
            - chunks: 一对多关联 PaperChunk，用于RAG检索。
            - layers: 一对多关联 Layer，用于阅读器标注。
            - reports: 一对多关联 Report，用于生成的研究报告。
    """
    __tablename__ = "papers"
    __table_args__ = {"comment": "论文表: 存储论文元数据、文件路径及处理状态"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "论文全局唯一标识(UUID)"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属用户ID"}
    )

    # 基本信息
    title: str = Field(
        index=True,
        sa_column_kwargs={"comment": "论文标题"}
    )
    authors: List[str] = Field(
        sa_column=Column(JSON, comment="作者列表(JSON数组)")
    )
    abstract: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "论文摘要原文"}
    )
    toc: Optional[List] = Field(
        default=None,
        sa_column=Column(JSON, comment="论文目录结构(TOC)")
    )

    # 文件存储
    file_key: str = Field(
        sa_column_kwargs={"comment": "文件存储Key/路径(MinIO或本地)"}
    )
    file_url: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "文件访问URL(可选)"}
    )

    # 状态管理
    status: PaperStatus = Field(
        default=PaperStatus.PENDING,
        sa_column_kwargs={"comment": "处理状态(PENDING/PROCESSING/COMPLETED/FAILED)"}
    )
    error_message: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "处理失败时的错误信息"}
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "上传/创建时间"}
    )

    # 关联关系
    user: User = Relationship(back_populates="papers")
    chunks: List["PaperChunk"] = Relationship(back_populates="paper")
    summaries: List["PaperSummary"] = Relationship(back_populates="paper")
    layers: List["Layer"] = Relationship(back_populates="paper")
    reports: List["Report"] = Relationship(back_populates="paper")


class PaperChunk(SQLModel, table=True):
    """
    论文向量切片表模型 (Paper Chunk Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储论文经解析、拆分后的文本片段及其向量表示 (Embedding)，用于 RAG (检索增强生成)。

    使用场景:
        - 向量检索: 根据用户 Query 查找相关论文片段。
        - 问答系统: 为 LLM 提供上下文依据。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'paper_chunks'。
        - paper_id: 外键关联 Papers 表。
        - content: 存储切片后的纯文本内容。
        - chunk_index: 记录切片在原文档中的顺序，用于上下文重组。
        - embedding: 使用 pgvector 扩展存储高维向量 (1536维，适配 OpenAI text-embedding-3-small 或兼容模型)。
            - 注意: 需要数据库开启 vector 扩展。
    """
    __tablename__ = "paper_chunks"
    __table_args__ = {"comment": "论文切片表: 存储解析后的文本片段及向量Embedding"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "切片唯一标识"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属论文ID"}
    )

    # 内容信息
    content: str = Field(
        sa_column_kwargs={"comment": "切片文本内容"}
    )
    page_number: Optional[int] = Field(
        default=None,
        sa_column_kwargs={"comment": "所在页码"}
    )
    chunk_index: int = Field(
        sa_column_kwargs={"comment": "切片顺序索引"}
    )

    # 向量嵌入 (pgvector 1536维，适配OpenAI Small模型)
    embedding: List[float] = Field(
        sa_column=Column(Vector(1536), comment="向量Embedding(1536维)")
    )

    # 关联关系
    paper: Paper = Relationship(back_populates="chunks")


class SearchHistory(SQLModel, table=True):
    """
    搜索历史表模型 (Search History Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 18:00:00

    用途:
        记录用户的搜索历史，用于提供搜索建议、历史回溯和用户兴趣分析。

    使用场景:
        - 用户在搜索框输入时显示最近搜索记录。
        - 分析用户感兴趣的领域。
    """
    __tablename__ = "search_histories"
    __table_args__ = {"comment": "搜索历史表: 记录用户的搜索关键词及上下文"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "记录ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "用户ID"}
    )
    query: str = Field(
        index=True,
        sa_column_kwargs={"comment": "搜索关键词"}
    )
    filters: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, comment="搜索过滤条件(JSON)")
    )
    result_count: int = Field(
        default=0,
        sa_column_kwargs={"comment": "搜索结果数量"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "搜索时间"}
    )

    # 关联关系 (可选)
    # user: User = Relationship(back_populates="search_histories") 
    # 暂不在 User 中定义反向关系以避免 User 类过于臃肿


class PaperSummary(SQLModel, table=True):
    """
    论文摘要表模型 (Paper Summary Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储论文的多维度摘要信息。

    使用场景:
        - 快速预览: 用户在阅读正文前查看简要总结。
        - 结构化提取: 存储如 "创新点", "方法论", "实验结果" 等特定类型的摘要。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'paper_summaries'。
        - summary_type: 区分摘要类型 (如 'abstract_rewrite', 'key_points', 'methodology')。
        - content: 摘要文本内容。
    """
    __tablename__ = "paper_summaries"
    __table_args__ = {"comment": "论文摘要表: 存储多维度的论文总结与分析"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "摘要ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属论文ID"}
    )

    # 摘要内容
    summary_type: str = Field(
        sa_column_kwargs={"comment": "摘要类型(如short, detailed, key_points)"}
    )
    content: str = Field(
        sa_column_kwargs={"comment": "摘要内容"}
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "生成时间"}
    )

    # 关联关系
    paper: Paper = Relationship(back_populates="summaries")


class ChatSession(SQLModel, table=True):
    """
    聊天会话表模型 (Chat Session Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        管理用户与 Agent 的对话会话上下文。

    使用场景:
        - 创建新对话、查看历史会话列表。
        - 区分不同类型的 Agent 会话 (如普通聊天、深度搜索、论文解读)。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'chat_sessions'。
        - user_id: 外键关联 Users 表。
        - agent_type: 标识会话使用的 Agent 策略 (如 'chat', 'search', 'summary')，决定后续消息处理逻辑。
        - 关联:
            - messages: 一对多关联 ChatMessage，存储具体消息记录。
    """
    __tablename__ = "chat_sessions"
    __table_args__ = {"comment": "聊天会话表: 管理用户对话上下文"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "会话ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属用户ID"}
    )

    title: str = Field(
        sa_column_kwargs={"comment": "会话标题"}
    )
    agent_type: str = Field(
        default="chat",
        sa_column_kwargs={"comment": "Agent类型(chat/search/summary)"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )

    # 关联关系
    user: User = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session")


class ChatMessage(SQLModel, table=True):
    """
    聊天消息表模型 (Chat Message Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储会话中的具体消息记录 (用户提问与 AI 回复)。

    使用场景:
        - 渲染聊天界面历史记录。
        - 为 Agent 提供多轮对话的历史上下文 (Memory)。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'chat_messages'。
        - session_id: 外键关联 ChatSessions 表。
        - role: 消息发送者角色 ('user', 'assistant', 'system')。
        - sources: JSON 字段，存储 AI 回复时引用的参考来源 (如引用论文片段、网页链接)，用于增强可信度。
        - TODO: 未来需考虑与 LangGraph Checkpoint 机制的整合，避免数据冗余。
    """
    __tablename__ = "chat_messages"
    __table_args__ = {"comment": "聊天消息表: 存储对话历史记录"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "消息ID"}
    )
    session_id: UUID = Field(
        foreign_key="chat_sessions.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属会话ID"}
    )

    role: str = Field(
        sa_column_kwargs={"comment": "角色(user/assistant/system)"}
    )
    content: str = Field(
        sa_column_kwargs={"comment": "消息内容"}
    )

    # 引用来源
    sources: Optional[List[dict]] = Field(
        default=None,
        sa_column=Column(JSON, comment="引用来源(JSON数组)")
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "发送时间"}
    )

    # 关联关系
    session: ChatSession = Relationship(back_populates="messages")


class Layer(SQLModel, table=True):
    """
    阅读器图层表模型 (Reader Layer Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        支持 PDF 阅读器的多图层标注功能，类似 Photoshop 图层概念。

    使用场景:
        - 多人协作: 区分 "我的标注"、"团队标注"、"AI 自动标注"。
        - 标注分类: 区分 "高亮层"、"翻译层"、"笔记层"。
        - 控制标注的可见性 (visible 字段)。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'layers'。
        - paper_id: 外键关联 Papers 表。
        - type: 图层类型 ('user' 为用户创建, 'system' 为系统生成)。
        - 关联:
            - annotations: 一对多关联 Annotation，该图层下的所有具体标注。
    """
    __tablename__ = "layers"
    __table_args__ = {"comment": "阅读器图层表: 支持多层级标注管理"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "图层ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属论文ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "创建者用户ID"}
    )

    name: str = Field(
        sa_column_kwargs={"comment": "图层名称"}
    )
    type: str = Field(
        default="user",
        sa_column_kwargs={"comment": "图层类型(user/system)"}
    )
    visible: bool = Field(
        default=True,
        sa_column_kwargs={"comment": "是否可见"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now, 
        sa_column_kwargs={"comment": "创建时间"}
    )

    # 关联关系
    paper: Paper = Relationship(back_populates="layers")
    annotations: List["Annotation"] = Relationship(back_populates="layer")


class Annotation(SQLModel, table=True):
    """
    标注表模型 (Annotation Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储 PDF 阅读器中的具体标注对象。

    使用场景:
        - 高亮 (Highlight): 标记重要文本。
        - 笔记 (Note/Comment): 对特定区域添加文字批注。
        - 划词翻译 (Translate): 保存翻译记录。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'annotations'。
        - layer_id: 外键关联 Layers 表，必须依附于某个图层。
        - rects: JSON 字段，存储标注在 PDF 页面上的几何坐标 (x, y, width, height, pageIndex)，前端利用此信息渲染。
        - content: 存储笔记内容或翻译结果文本。
        - color: 标注颜色，支持个性化配置。
    """
    __tablename__ = "annotations"
    __table_args__ = {"comment": "标注表: 存储PDF的高亮、笔记等标注信息"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "标注ID"}
    )
    layer_id: UUID = Field(
        foreign_key="layers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属图层ID"}
    )

    type: str = Field(
        sa_column_kwargs={"comment": "标注类型(highlight/note/translate)"}
    )
    # 存储矩形坐标 [{"x":.., "y":.., "width":.., "height":.., "pageIndex":..}]
    rects: List[dict] = Field(
        sa_column=Column(JSON, comment="标注区域坐标(JSON数组)")
    )
    content: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "标注内容(笔记/翻译结果)"}
    )
    color: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "标注颜色(Hex/RGB)"}
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"comment": "创建时间"}
    )

    # 关联关系
    layer: Layer = Relationship(back_populates="annotations")


class Report(SQLModel, table=True):
    """
    研究报告表模型 (Report Model)

    注释者: BackendAgent
    注释时间: 2026-01-12 07:50:00

    用途:
        存储 Agent 生成的深度研究报告。

    使用场景:
        - 深度调研 (Deep Research): 基于单篇或多篇论文生成的综合分析报告。
        - 相关工作 (Related Work): 自动生成的文献综述。
        - 报告查看与导出 (Markdown 格式)。

    内部实现:
        - 继承自 SQLModel，对应数据库表 'reports'。
        - paper_id: 外键关联 Papers 表 (目前设计为关联单篇，未来可能需要关联多篇或通过 Tags 关联)。
        - type: 报告类型 ('deep_research', 'related_work')。
        - status: 生成状态流转 ('generating' -> 'completed' / 'failed')，用于前端轮询或 SSE 通知。
        - content: 存储 Markdown 格式的报告正文。
    """
    __tablename__ = "reports"
    __table_args__ = {"comment": "研究报告表: 存储Agent生成的分析报告"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "报告ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "基于的论文ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属用户ID"}
    )

    title: str = Field(
        sa_column_kwargs={"comment": "报告标题"}
    )
    type: str = Field(
        sa_column_kwargs={"comment": "报告类型(deep_research/related_work)"}
    )
    status: str = Field(
        default="generating",
        sa_column_kwargs={"comment": "生成状态(generating/completed/failed)"}
    )
    content: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "报告正文(Markdown)"}
    )
    summary: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "报告摘要"}
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"comment": "创建时间"}
    )

    # 关联关系
    paper: Paper = Relationship(back_populates="reports")

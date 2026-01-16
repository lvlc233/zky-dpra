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
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON, Text, UniqueConstraint
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
    
    # 用户设置 (JSON)
    settings: Optional[dict] = Field(
        default_factory=lambda: {"theme": "light", "language": "zh"},
        sa_column=Column(JSON, comment="用户个性化设置")
    )

    # 关联关系
    papers: List["Paper"] = Relationship(back_populates="user")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    collections: List["Collection"] = Relationship(back_populates="user")
    notes: List["Note"] = Relationship(back_populates="user")
    mind_maps: List["MindMap"] = Relationship(back_populates="user")


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
    # TODO: 这里可能需要前端做处理,获取文件的时候转化为从nginx获取?
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
    chat_sessions: List["ChatSession"] = Relationship(back_populates="paper")
    notes: List["Note"] = Relationship(back_populates="paper")
    mind_map: Optional["MindMap"] = Relationship(back_populates="paper")


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

    #  TODO: 维度现在不确定.可能存在多维度配置的可能。
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
    paper_id: Optional[UUID] = Field(
        default=None,
        foreign_key="papers.id",
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "关联论文ID(可选)"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )

    # 关联关系
    user: User = Relationship(back_populates="chat_sessions")
    paper: Optional["Paper"] = Relationship(back_populates="chat_sessions")
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
        default_factory=datetime.now,
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


class Note(SQLModel, table=True):
    """
    用户笔记表模型 (User Note Model)
    
    注释者: BackendAgent
    注释时间: 2026-01-14 16:30:00
    
    用途:
        存储用户针对论文撰写的通用笔记 (非特定位置的标注)。
        
    使用场景:
        - 侧边栏的 "笔记" Tab，用于记录阅读心得、待办事项或草稿。
        - 独立于 PDF 标注 (Annotation)，是整篇论文层面的笔记。
    """
    __tablename__ = "notes"
    __table_args__ = {"comment": "用户笔记表: 存储论文层面的通用笔记"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "笔记ID"}
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
    
    title: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "笔记标题"}
    )
    content: str = Field(
        sa_column_kwargs={"comment": "笔记内容(Markdown)"}
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联
    paper: Paper = Relationship(back_populates="notes")
    user: User = Relationship(back_populates="notes")


class MindMap(SQLModel, table=True):
    """
    思维导图/知识图谱表模型 (Mind Map Model)
    
    注释者: BackendAgent
    注释时间: 2026-01-14 16:45:00
    
    用途:
        存储论文的知识结构图 (节点与边)。
        
    使用场景:
        - 侧边栏 "脑图" Tab，展示论文核心概念及其关系。
        - 支持前端 reagraph 渲染。
        - 存储 Agent 生成的图谱数据或用户手动编辑的结果。
    """
    __tablename__ = "mind_maps"
    __table_args__ = {"comment": "思维导图表: 存储论文的知识结构(节点与边)"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "脑图ID"}
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
        sa_column_kwargs={"comment": "所属用户ID"}
    )
    
    # 存储图数据: { "nodes": [...], "edges": [...] }
    # 节点结构: { "id": "...", "label": "...", "data": {...} }
    # 边结构: { "id": "...", "source": "...", "target": "...", "label": "..." }
    graph_data: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, comment="图数据(JSON):包含nodes和edges")
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联
    paper: Paper = Relationship(back_populates="mind_map")
    user: User = Relationship(back_populates="mind_maps")


class AgentSession(SQLModel, table=True):
    """
    Agent 会话表
    存储 Agent 的运行实例信息，关联到用户的聊天会话
    """
    __tablename__ = "agent_sessions"
    __table_args__ = {"comment": "Agent会话表: 存储Agent运行实例信息"}

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
        sa_column_kwargs={"comment": "用户ID"}
    )

    chat_session_id: Optional[UUID] = Field(
        default=None,
        foreign_key="chat_sessions.id",
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "关联的聊天会话ID"}
    )

    thread_id: str = Field(
        sa_column=Column(Text, unique=True, index=True, comment="LangGraph线程ID")
    )

    agent_type: str = Field(
        sa_column_kwargs={"comment": "Agent类型(search/paper_chat/summary/mindmap/deep_research)"}
    )

    status: str = Field(
        default="active",
        sa_column_kwargs={"comment": "会话状态(active/interrupted/completed/error)"}
    )

    interrupt_type: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "中断类型(strong/weak)"}
    )

    interrupt_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, comment="中断相关数据")
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"comment": "创建时间"}
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"comment": "更新时间"}
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"comment": "完成时间"}
    )


class AgentTodo(SQLModel, table=True):
    """
    Agent 待办事项表
    存储弱人工介入的待办事项
    """
    __tablename__ = "agent_todos"
    __table_args__ = {"comment": "Agent待办事项表: 存储弱人工介入的待办"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "待办ID"}
    )

    agent_session_id: UUID = Field(
        foreign_key="agent_sessions.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "Agent会话ID"}
    )

    todo_type: str = Field(
        sa_column_kwargs={"comment": "待办类型(approval/input/selection等)"}
    )

    todo_data: Dict[str, Any] = Field(
        sa_column=Column(JSON, comment="待办事项详情")
    )

    status: str = Field(
        default="pending",
        sa_column_kwargs={"comment": "状态(pending/completed/cancelled)"}
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"comment": "创建时间"}
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"comment": "完成时间"}
    )


class AgentCheckpoint(SQLModel, table=True):
    """
    Agent 检查点表
    扩展 LangGraph 的 checkpoint 表，添加业务字段
    """
    __tablename__ = "agent_checkpoints"
    __table_args__ = {"comment": "Agent检查点表: 扩展LangGraph checkpoint"}

    thread_id: str = Field(
        sa_column=Column(Text, primary_key=True, comment="线程ID")
    )

    checkpoint_id: str = Field(
        sa_column=Column(Text, primary_key=True, comment="检查点ID")
    )

    parent_id: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, comment="父检查点ID")
    )

    checkpoint: Dict[str, Any] = Field(
        sa_column=Column(JSON, comment="检查点数据")
    )

    checkpoint_metadata: Dict[str, Any] = Field(
        sa_column=Column("metadata", JSON, comment="元数据")
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"comment": "创建时间"}
    )

    node_name: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "节点名称"}
    )

    step_count: int = Field(
        default=0,
        sa_column_kwargs={"comment": "步骤计数"}
    )


class AgentCheckpointWrite(SQLModel, table=True):
    """
    Agent 检查点写入表
    扩展 LangGraph 的 checkpoint_writes 表
    """
    __tablename__ = "agent_checkpoint_writes"
    __table_args__ = {"comment": "Agent检查点写入表: 扩展LangGraph checkpoint_writes"}

    thread_id: str = Field(
        sa_column=Column(Text, primary_key=True, comment="线程ID")
    )

    checkpoint_id: str = Field(
        sa_column=Column(Text, primary_key=True, comment="检查点ID")
    )

    task_id: str = Field(
        sa_column=Column(Text, primary_key=True, comment="任务ID")
    )

    idx: int = Field(
        primary_key=True,
        sa_column_kwargs={"comment": "索引"}
    )

    channel: str = Field(
        sa_column=Column(Text, comment="通道")
    )

    type: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, comment="类型")
    )

    blob: Optional[bytes] = Field(
        default=None,
        sa_column_kwargs={"comment": "二进制数据"}
    )


class ConfigCategory(SQLModel, table=True):
    """
    配置分类表 (Config Categories)

    注释者: BackendAgent
    注释时间: 2026-01-14 18:50:00
    
    用途:
        用于对配置项进行分类管理，如 'system', 'user', 'agent' 等。
    
    内部实现:
        - code: 分类代码，如 'system.llm', 'user.ui'。
    """
    __tablename__ = "config_categories"
    __table_args__ = {"comment": "配置分类表: 用于对配置项进行分类管理"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "分类ID"}
    )
    code: str = Field(
        unique=True,
        index=True,
        max_length=50,
        sa_column_kwargs={"comment": "分类代码(如 system.llm)"}
    )
    name: str = Field(
        max_length=100,
        sa_column_kwargs={"comment": "分类显示名称"}
    )
    description: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "分类描述"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )

    # 关联
    definitions: List["ConfigDefinition"] = Relationship(back_populates="category")


class ConfigDefinition(SQLModel, table=True):
    """
    配置项定义表 (Config Definitions)

    注释者: BackendAgent
    注释时间: 2026-01-14 18:50:00
    
    用途:
        定义具体的配置项元数据，包括键名、类型、默认值、验证规则等。
    
    内部实现:
        - scope: 作用域 (system, user, session)。
        - value_type: 值类型 (string, number, boolean, json)。
    """
    __tablename__ = "config_definitions"
    __table_args__ = (
        UniqueConstraint("category_id", "key", name="unique_category_key"),
        {"comment": "配置项定义表: 定义具体的配置项元数据"}
    )

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "配置定义ID"}
    )
    category_id: Optional[UUID] = Field(
        default=None, 
        foreign_key="config_categories.id",
        sa_column_kwargs={"comment": "关联的分类ID"}
    )
    key: str = Field(
        max_length=200,
        index=True,
        sa_column_kwargs={"comment": "配置键(如 theme, timeout)"}
    )
    name: str = Field(
        max_length=200,
        sa_column_kwargs={"comment": "配置显示名称"}
    )
    description: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "配置描述"}
    )
    value_type: str = Field(
        max_length=50,
        sa_column_kwargs={"comment": "值类型(string, number, boolean, json)"}
    )
    default_value: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, comment="默认值(JSON格式)")
    )
    validation_rules: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, comment="验证规则(JSON格式)")
    )
    options: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON, comment="可选值列表(JSON格式)")
    )
    scope: str = Field(
        max_length=50,
        sa_column_kwargs={"comment": "作用域(system, user, session)"}
    )
    is_public: bool = Field(
        default=False,
        sa_column_kwargs={"comment": "是否公开(前端可见)"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联
    category: Optional[ConfigCategory] = Relationship(back_populates="definitions")
    user_values: List["UserConfigValue"] = Relationship(back_populates="definition")


class UserConfigValue(SQLModel, table=True):
    """
    用户配置值表 (User Config Values)

    注释者: BackendAgent
    注释时间: 2026-01-14 18:50:00
    
    用途:
        存储用户特定的配置值，覆盖默认配置。
    """
    __tablename__ = "user_config_values"
    __table_args__ = (
        UniqueConstraint("user_id", "config_id", name="unique_user_config"),
        {"comment": "用户配置值表: 存储用户特定的配置值"}
    )

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "配置值ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        sa_column_kwargs={"comment": "关联的用户ID"}
    )
    config_id: UUID = Field(
        foreign_key="config_definitions.id",
        sa_column_kwargs={"comment": "关联的配置定义ID"}
    )
    value: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False, comment="配置值(JSON格式)")
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联
    definition: Optional[ConfigDefinition] = Relationship(back_populates="user_values")
    # user: Optional["User"] = Relationship(back_populates="config_values") # 如果需要在User中反向关联

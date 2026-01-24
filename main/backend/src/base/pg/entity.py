
# 定义pg数据库的实体映射。 

'''
开发者: BackendAgent
当前版本: v1.4_db_refactor
创建时间: 2026年01月08日 11:00
更新时间: 2026年01月21日 10:00
更新记录:
    [2026年01月21日 10:00:v1.4_db_refactor:根据最新架构文档重构数据库模型]
    1. 移除 Layer/View/Report 相关实体，实现去图层化。
    2. 新增 Job 实体，统一管理所有异步任务（TOC/Summary/MindMap/Chat）。
    3. Annotation 直接关联 Paper。
    4. 移除 Message 表，将聊天记录整合至 AgentSession 或依赖 Job 产物。
    5. 优化 User/Paper 核心资产结构。
'''

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from pgvector.sqlalchemy import Vector
from sqlmodel import Field, Relationship, SQLModel

from service.setting.schema import Settings
from common.db_types import PydanticJSON


class User(SQLModel, table=True):
    """
    用户表模型 (User Model)
    核心资产持有者，关联所有资源。
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
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "账号最后更新时间"}
    )
    
    settings: Settings = Field(
        default_factory=Settings,
        sa_type=PydanticJSON(Settings),
        sa_column_kwargs={"comment": "用户个性化设置"}
    )

    # 关联关系
    papers: List["Paper"] = Relationship(back_populates="user")
    collections: List["Collection"] = Relationship(back_populates="user")
    agent_sessions: List["AgentSession"] = Relationship(back_populates="user")
    notes: List["Note"] = Relationship(back_populates="user")
    jobs: List["Job"] = Relationship(back_populates="user")


class Paper(SQLModel, table=True):
    """
    论文表模型 (Paper Model)
    核心资源，承载文件、元数据及所有衍生数据。
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
    summary: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "论文摘要原文"}
    )
    full_text: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, comment="解析后的全文内容")
    )
    toc: Optional[List] = Field(
        default=None,
        sa_column=Column(JSON, comment="论文目录结构(TOC)")
    )
    published_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"comment": "发表时间"}
    )
    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, comment="标签(JSON数组)")
    )
    references_number: Optional[int] = Field(
        default=None,
        sa_column_kwargs={"comment": "引用数量"}
    )

    # 文件存储
    file_key: str = Field(
        sa_column_kwargs={"comment": "文件存储Key/路径(MinIO或本地)"}
    )
    file_url: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "文件访问URL(可选)"}
    )
    source: str = Field(
        default="upload",
        sa_column_kwargs={"comment": "文件来源类型(upload/web/arxiv)"}
    )
    source_ref: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "文件来源引用(如arXiv ID)"}
    )

    # 状态管理
    analysis_status: str = Field(
        default="pending",
        index=True,
        sa_column_kwargs={"comment": "分析状态(pending/processing/completed/failed)"}
    )
    error_message: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "处理失败时的错误信息"}
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "上传/创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    # 关联关系
    user: User = Relationship(back_populates="papers")
    chunks: List["PaperChunk"] = Relationship(back_populates="paper")
    summaries: List["PaperSummary"] = Relationship(back_populates="paper")
    annotations: List["Annotation"] = Relationship(back_populates="paper")
    agent_sessions: List["AgentSession"] = Relationship(back_populates="paper")
    notes: List["Note"] = Relationship(back_populates="paper")
    mind_map: Optional["MindMap"] = Relationship(back_populates="paper")
    jobs: List["Job"] = Relationship(back_populates="paper")


class PaperChunk(SQLModel, table=True):
    """
    论文向量切片表模型 (Paper Chunk Model)
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

    embedding: List[float] = Field(
        sa_column=Column(Vector(1536), comment="向量Embedding(默认1536维)")
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        sa_column_kwargs={"comment": "用于生成Embedding的模型"}
    )

    paper: Paper = Relationship(back_populates="chunks")


class Collection(SQLModel, table=True):
    """
    收藏夹表模型 (Collection Model)
    """
    __tablename__ = "collections"
    __table_args__ = {"comment": "收藏夹表: 用户自定义的论文集合"}

    collection_id: UUID = Field(
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
    is_default: bool = Field(
        default=False,
        index=True,
        sa_column_kwargs={"comment": "是否为默认收藏夹"}
    )
    total: int = Field(
        default=0,
        sa_column_kwargs={"comment": "收藏夹下的论文数量"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )

    user: User = Relationship(back_populates="collections")


class CollectionPaper(SQLModel, table=True):
    """
    收藏夹-论文关联表
    """
    __tablename__ = "collection_papers"
    __table_args__ = {"comment": "收藏夹-论文关联表"}

    collection_id: UUID = Field(
        foreign_key="collections.collection_id",
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "收藏夹ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "论文ID"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "收藏时间"}
    )


class SearchHistory(SQLModel, table=True):
    """
    搜索历史表
    """
    __tablename__ = "search_histories"
    __table_args__ = {"comment": "搜索历史表"}

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
        sa_column=Column(JSON, comment="搜索过滤条件")
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "搜索时间"}
    )


class PaperSummary(SQLModel, table=True):
    """
    论文摘要表模型 (Paper Summary Model)
    """
    __tablename__ = "paper_summaries"
    __table_args__ = {"comment": "论文摘要表: 存储多维度的论文总结"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "摘要ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属论文ID"}
    )

    summary_type: str = Field(
        sa_column_kwargs={"comment": "摘要类型(如summary_config的key)"}
    )
    content: str = Field(
        sa_column_kwargs={"comment": "摘要内容"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "生成时间"}
    )
    
    paper: Paper = Relationship(back_populates="summaries")


class Note(SQLModel, table=True):
    """
    笔记表模型 (Note Model)
    """
    __tablename__ = "notes"
    __table_args__ = {"comment": "笔记表: 存储用户对论文的个人注释"}

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
        sa_column_kwargs={"comment": "关联论文ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属用户ID"}
    )
    title: str = Field(
        sa_column_kwargs={"comment": "笔记标题"}
    )
    page: Optional[int] = Field(
        default=None,
        sa_column_kwargs={"comment": "笔记对应的页码"}
    )
    content: str = Field(
        sa_column_kwargs={"comment": "笔记内容(Markdown)"}
    )
    tags: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON, comment="标签(JSON数组)")
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,   
        sa_column_kwargs={"comment": "更新时间"}
    )

    paper: Paper = Relationship(back_populates="notes")
    user: User = Relationship(back_populates="notes")


class MindMap(SQLModel, table=True):
    """
    思维导图表模型 (Mind Map Model)
    """
    __tablename__ = "mind_maps"
    __table_args__ = {"comment": "思维导图表: 存储论文的知识结构"}

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
    
    # 存储图数据: { "nodes": [...], "edges": [...] }
    graph_data: Dict[str, Any] = Field(
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

    paper: Paper = Relationship(back_populates="mind_map")


class Annotation(SQLModel, table=True):
    """
    标注表模型 (Annotation Model)
    直接关联 Paper，移除 Layer 概念。
    """
    __tablename__ = "annotations"
    __table_args__ = {"comment": "标注表: 存储PDF的高亮、笔记等标注信息"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "标注ID"}
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "所属论文ID"}
    )

    type: str = Field(
        sa_column_kwargs={"comment": "标注类型(highlight/note/translate)"}
    )
    # 存储矩形坐标 [{"x":.., "y":.., "width":.., "height":.., "pageIndex":..}]
    rects: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, comment="标注区域坐标(JSON数组)")
    )
    content: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "标注内容(笔记/翻译结果)"}
    )
    color: str = Field(
        default="#FFD700",
        sa_column_kwargs={"comment": "标注颜色(Hex/RGB)"}
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "更新时间"}
    )
    
    paper: Paper = Relationship(back_populates="annotations")


class AgentSession(SQLModel, table=True):
    """
    Agent 会话表 (AgentSession)
    对应文档中的 Record，管理 AI 对话历史。
    聊天记录 (messages) 存储在此表的 JSON 字段中。
    """
    __tablename__ = "agent_sessions"
    __table_args__ = {"comment": "Agent会话表: 存储对话历史"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "记录ID(RecordID)"}
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "用户ID"}
    )
    
    paper_id: Optional[UUID] = Field(
        default=None,
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "关联论文ID(可选)"}
    )

    title: str = Field(
        default="New Chat",
        sa_column_kwargs={"comment": "会话标题"}
    )

    thread_id: str = Field(
        sa_column=Column(Text, unique=True, index=True, comment="LangGraph线程ID")
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
    user: User = Relationship(back_populates="agent_sessions")
    paper: Optional[Paper] = Relationship(back_populates="agent_sessions")


class Job(SQLModel, table=True):
    """
    任务表 (Job)
    统一管理所有异步任务（TOC/Summary/MindMap/Chat）。
    """
    __tablename__ = "jobs"
    __table_args__ = {"comment": "任务表: 异步任务状态与结果"}

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "作业ID"}
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "用户ID"}
    )
    paper_id: Optional[UUID] = Field(
        default=None,
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True),
        sa_column_kwargs={"comment": "关联的论文ID"}
    )
    
    # toc, summary, mind_map, chat
    type: str = Field(
        index=True,
        sa_column_kwargs={"comment": "任务类型"}
    )
    
    # queued, running, blocked, succeeded, failed, canceled, expired
    status: str = Field(
        default="queued",
        index=True,
        sa_column_kwargs={"comment": "任务状态"}
    )
    
    progress: float = Field(
        default=0.0,
        sa_column_kwargs={"comment": "任务进度(0-1)"}
    )
    stage: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "当前阶段描述"}
    )
    
    # 存储 JobResult: {toc:..., summary:..., mind_map:..., chat:...}
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, comment="任务产物(JSON)")
    )
    
    error: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "错误信息"}
    )
    
    # 幂等控制
    params_hash: str = Field(
        index=True,
        sa_column_kwargs={"comment": "参数哈希(用于去重)"}
    )
    pipeline_version: str = Field(
        default="v1",
        sa_column_kwargs={"comment": "管道版本"}
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"comment": "创建时间"}
    )
    end_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"comment": "结束时间"}
    )

    # 关联
    paper: Optional[Paper] = Relationship(back_populates="jobs")
    user: User = Relationship(back_populates="jobs")

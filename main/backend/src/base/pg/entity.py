# 定义pg数据库的实体映射。 

'''
开发者: BackendAgent
当前版本: v1.0_db_models
创建时间: 2026年01月08日 11:00
更新时间: 2026年01月08日 16:30
更新记录:
    [2026年01月08日 11:00:v1.0_db_models:创建数据库模型文件，包含所有核心表结构]
    [2026年01月08日 16:30:v1.1_db_models:从/src/business_model/database_models.py迁移到/src/base/pg/entity.py中]
'''

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from pgvector.sqlalchemy import Vector
from sqlmodel import Field, Relationship, SQLModel


# 枚举定义
class PaperStatus(str, Enum):
    """论文处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(SQLModel, table=True):
    """用户表模型"""
    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True)
    )
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 关联关系
    papers: List["Paper"] = Relationship(back_populates="user")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")


class Paper(SQLModel, table=True):
    """论文表模型"""
    __tablename__ = "papers"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True)
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True)
    )

    # 基本信息
    title: str = Field(index=True)
    authors: List[str] = Field(sa_column=Column(JSON))
    abstract: Optional[str] = None

    # 文件存储
    file_key: str  # MinIO / 本地存储路径
    file_url: Optional[str] = None

    # 状态管理
    status: PaperStatus = Field(default=PaperStatus.PENDING)
    error_message: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 关联关系
    user: User = Relationship(back_populates="papers")
    chunks: List["PaperChunk"] = Relationship(back_populates="paper")
    summaries: List["PaperSummary"] = Relationship(back_populates="paper")


class PaperChunk(SQLModel, table=True):
    """论文向量切片表模型"""
    __tablename__ = "paper_chunks"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True)
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        index=True,
        sa_type=PGUUID(as_uuid=True)
    )

    # 内容信息
    content: str
    page_number: Optional[int] = None
    chunk_index: int

    # 向量嵌入 (pgvector 1536维，适配OpenAI Small模型)
    embedding: List[float] = Field(
        sa_column=Column(Vector(1536))
    )

    # 关联关系
    paper: Paper = Relationship(back_populates="chunks")


class PaperSummary(SQLModel, table=True):
    """论文摘要表模型（预留）"""
    __tablename__ = "paper_summaries"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True)
    )
    paper_id: UUID = Field(
        foreign_key="papers.id",
        sa_type=PGUUID(as_uuid=True)
    )

    # 摘要内容
    summary_type: str  # 如 "short", "detailed", "key_points"
    content: str

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 关联关系
    paper: Paper = Relationship(back_populates="summaries")


class ChatSession(SQLModel, table=True):
    """聊天会话表模型"""
    __tablename__ = "chat_sessions"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True)
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        sa_type=PGUUID(as_uuid=True)
    )

    title: str
    agent_type: str = Field(default="chat")  # 使用的Agent类型 (search, chat, summary)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 关联关系
    user: User = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session")

# TODO: 考虑Langgraph中的持久化和这里的消息表的关系,看是否合并或者复用
class ChatMessage(SQLModel, table=True):
    """聊天消息表模型"""
    __tablename__ = "chat_messages"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True)
    )
    session_id: UUID = Field(
        foreign_key="chat_sessions.id",
        index=True,
        sa_type=PGUUID(as_uuid=True)
    )

    role: str  # "user", "assistant", "system"
    content: str

    # 引用来源
    sources: Optional[List[dict]] = Field(
        default=None,
        sa_column=Column(JSON)
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 关联关系
    session: ChatSession = Relationship(back_populates="messages")
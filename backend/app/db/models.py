"""
SQLAlchemy ORM Models — MySQL compatible, UUID primary keys
Tables: users, quotas, documents, analysis_results, chat_histories
"""
from datetime import datetime, timezone
from typing import Optional
import uuid as uuid_lib

from sqlalchemy import (
    String, Text, Boolean, DateTime, Float,
    ForeignKey, BigInteger, Index, Integer
)
from sqlalchemy.dialects.mysql import LONGTEXT, JSON, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid() -> str:
    return str(uuid_lib.uuid4())


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class UserPlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AIProvider(str, enum.Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    LOCAL = "local"
    FALLBACK = "fallback"


class AnalysisType(str, enum.Enum):
    SUMMARY = "summary"
    CHAT = "chat"
    EXTRACTION = "extraction"
    COMPARISON = "comparison"
    CUSTOM = "custom"


# ─────────────────────────────────────────────
# User Table
# ─────────────────────────────────────────────
class UserRole(str, enum.Enum):
    USER  = "user"
    ADMIN = "admin"
    
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), default=UserRole.USER, nullable=False
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    quota: Mapped[Optional["Quota"]] = relationship(
        "Quota", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="user", cascade="all, delete-orphan"
    )
    chat_histories: Mapped[list["ChatHistory"]] = relationship(
        "ChatHistory", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email} plan={self.plan}>"
# ─────────────────────────────────────────────
# Quota Table
# ─────────────────────────────────────────────

class Quota(Base):
    __tablename__ = "quotas"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    daily_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_limit: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    daily_reset_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    total_analyses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_pages_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_used: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    storage_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    storage_limit_bytes: Mapped[int] = mapped_column(BigInteger, default=52428800, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="quota")

    @property
    def daily_remaining(self) -> int:
        return max(0, self.daily_limit - self.daily_used)

    @property
    def storage_used_mb(self) -> float:
        return round(self.storage_used_bytes / (1024 * 1024), 2)

    @property
    def usage_percentage(self) -> float:
        if self.daily_limit == 0:
            return 100.0
        return round((self.daily_used / self.daily_limit) * 100, 1)


# ─────────────────────────────────────────────
# Document Table
# ─────────────────────────────────────────────

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")

    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(LONGTEXT, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="documents")
    analyses: Mapped[list["AnalysisResult"]] = relationship(
        "AnalysisResult", back_populates="document", cascade="all, delete-orphan"
    )
    chat_histories: Mapped[list["ChatHistory"]] = relationship(
        "ChatHistory", back_populates="document", cascade="all, delete-orphan"
    )

    @property
    def file_size_mb(self) -> float:
        return round(self.file_size_bytes / (1024 * 1024), 2)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


# ─────────────────────────────────────────────
# Analysis Result Table
# ─────────────────────────────────────────────

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    __table_args__ = (
        Index("ix_analysis_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    analysis_type: Mapped[str] = mapped_column(String(20), default="summary", nullable=False)
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[Optional[str]] = mapped_column(LONGTEXT, nullable=True)

    provider: Mapped[str] = mapped_column(String(20), default="gemini", nullable=False)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    key_points: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    extra_data: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)

    is_successful: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    document: Mapped["Document"] = relationship("Document", back_populates="analyses")
    user: Mapped["User"] = relationship("User")


# ─────────────────────────────────────────────
# Chat History Table
# ─────────────────────────────────────────────

class ChatHistory(Base):
    __tablename__ = "chat_histories"
    __table_args__ = (
        Index("ix_chat_user_created", "user_id", "created_at"),
        Index("ix_chat_session", "session_id"),
        Index("ix_chat_document_created", "document_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        CHAR(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )

    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    session_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(LONGTEXT, nullable=False)

    provider: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    feedback: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="chat_histories")
    document: Mapped[Optional["Document"]] = relationship("Document", back_populates="chat_histories")
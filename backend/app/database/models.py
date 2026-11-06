"""SQLAlchemy ORM models for structured document metadata."""

from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DocumentRecord(Base):
    """Structured record for an uploaded document."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(String(64), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False, index=True)
    file_type = Column(String(32), nullable=False, index=True)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    page_count = Column(Integer, default=1, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="indexed", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    chunks = relationship("DocumentChunkRecord", back_populates="document", cascade="all, delete-orphan")


class DocumentChunkRecord(Base):
    """Structured record for chunk metadata."""

    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(128), unique=True, nullable=False, index=True)
    doc_id = Column(String(64), ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, default=1, nullable=False)
    chunk_index = Column(Integer, default=0, nullable=False)
    token_count_estimate = Column(Integer, default=0, nullable=False)
    char_start = Column(Integer, default=0, nullable=False)
    char_end = Column(Integer, default=0, nullable=False)

    document = relationship("DocumentRecord", back_populates="chunks")

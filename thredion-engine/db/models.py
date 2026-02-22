"""
Thredion Engine — Database Models
SQLAlchemy ORM models for the cognitive memory engine.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, LargeBinary, ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Memory(Base):
    """A single cognitive memory — a saved link with AI-enriched metadata."""
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False, unique=True, index=True)
    platform = Column(String(50), default="unknown")       # instagram, twitter, article
    title = Column(String(512), default="")
    content = Column(Text, default="")                       # original caption / text
    summary = Column(Text, default="")                       # AI-generated summary
    category = Column(String(100), default="Uncategorized")
    tags = Column(Text, default="[]")                        # JSON list
    topic_graph = Column(Text, default="[]")                 # JSON hierarchy
    embedding = Column(LargeBinary, nullable=True)           # pickled numpy array
    importance_score = Column(Float, default=50.0)
    importance_reasons = Column(Text, default="[]")          # JSON list of reasons
    thumbnail_url = Column(String(2048), default="")
    user_phone = Column(String(50), default="default")
    created_at = Column(DateTime, default=_utcnow)

    # Relationships
    connections_out = relationship(
        "Connection", foreign_keys="Connection.source_id",
        back_populates="source", cascade="all, delete-orphan",
    )
    connections_in = relationship(
        "Connection", foreign_keys="Connection.target_id",
        back_populates="target", cascade="all, delete-orphan",
    )


class Connection(Base):
    """An edge in the knowledge graph — links two related memories."""
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    similarity_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("source_id", "target_id", name="uq_connection_pair"),
    )

    source = relationship("Memory", foreign_keys=[source_id], back_populates="connections_out")
    target = relationship("Memory", foreign_keys=[target_id], back_populates="connections_in")


class ResurfacedMemory(Base):
    """Tracks when an older memory is resurfaced because a new one is similar."""
    __tablename__ = "resurfaced_memories"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    triggered_by_id = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, default="")
    similarity_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=_utcnow)

    memory = relationship("Memory", foreign_keys=[memory_id])
    triggered_by = relationship("Memory", foreign_keys=[triggered_by_id])

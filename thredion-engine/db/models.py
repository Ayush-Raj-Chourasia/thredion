"""
Thredion Engine — Database Models
SQLAlchemy ORM models for the cognitive memory engine aligned with Supabase PostgreSQL schema.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, String, Float, Text, DateTime, LargeBinary, ForeignKey,
    UniqueConstraint, Integer
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    """A registered user, identified by their WhatsApp phone number."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(200), default="")
    email = Column(String(200), default="")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Backwards compatibility alias for older code using .phone
    @property
    def phone(self):
        return self.phone_number
    
    @phone.setter
    def phone(self, value):
        self.phone_number = value


class OTPCode(Base):
    """Temporary OTP codes sent via WhatsApp for authentication."""
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True) # Likely still integer or matches users
    phone = Column(String(50), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class Memory(Base):
    """A single cognitive memory — a saved link with AI-enriched metadata."""
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source = Column(String(50), default="unknown")       # instagram, twitter, article, youtube
    source_url = Column(String(2048), nullable=True, index=True)
    original_input = Column(Text, nullable=False)
    cleaned_text = Column(Text, default="")
    processing_status = Column(String(20), default="pending")  # pending|processing|completed|failed
    
    title = Column(String(512), default="")
    summary = Column(Text, default="")
    key_points = Column(JSONB, default=[])
    category = Column(String(100), default="Uncategorized")
    tags = Column(JSONB, default=[])
    importance_score = Column(Float, default=0.0)
    importance_reasons = Column(JSONB, default=[])
    embedding = Column(LargeBinary, nullable=True) # bytea in postgres
    
    resurfaced_count = Column(Integer, default=0)
    last_resurfaced_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Aliases for compatibility
    @property
    def url(self):
        return self.source_url
    
    @property
    def content(self):
        return self.original_input


class Connection(Base):
    """An edge in the knowledge graph — links two related memories."""
    __tablename__ = "connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    similarity_score = Column(Float, nullable=False, default=0.0)
    connection_type = Column(String(50), default="similar")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class ResurfacedMemory(Base):
    """Tracks when an older memory is resurfaced because a new one is similar."""
    __tablename__ = "resurfaced_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    triggered_by_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=True)
    resurfaced_at = Column(DateTime(timezone=True), default=_utcnow)
    reason = Column(Text, default="")
    similarity_score = Column(Float, default=0.0)
    user_action = Column(Text, default="none")
    created_at = Column(DateTime(timezone=True), default=_utcnow)

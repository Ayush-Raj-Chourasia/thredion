"""
Thredion Engine — Database Models
SQLAlchemy ORM models for the cognitive memory engine aligned with Supabase PostgreSQL schema.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, String, Float, Text, DateTime, LargeBinary, ForeignKey,
    UniqueConstraint, Integer, JSON, UUID
)
from sqlalchemy.orm import relationship
from db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    """A registered user, identified by their WhatsApp phone number."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), default="")
    email = Column(String(200), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
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
    key_points = Column(JSON, default=[])
    category = Column(String(100), default="Uncategorized")
    tags = Column(JSON, default=[])
    importance_score = Column(Float, default=0.0)
    importance_reasons = Column(JSON, default=[])
    
    # Cognitive & Metadata fields
    thumbnail_url = Column(String(2048), nullable=True)
    topic_graph = Column(JSON, default=[])
    content_quality = Column(String(50), default="pending")
    cognitive_mode = Column(String(50), default="learn")
    bucket = Column(String(100), default="Uncategorized")
    
    # Transcription fields
    transcript = Column(Text, nullable=True)
    transcript_length = Column(Integer, default=0)
    transcript_source = Column(String(50), nullable=True)
    transcription_job_id = Column(String(100), nullable=True)
    transcription_status = Column(String(50), default="none")
    processing_error = Column(Text, nullable=True)
    is_video = Column(Boolean, default=False)
    
    embedding = Column(LargeBinary, nullable=True) # bytea in postgres
    
    resurfaced_count = Column(Integer, default=0)
    last_resurfaced_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Aliases for compatibility
    @property
    def url(self):
        return self.source_url
    
    @property
    def platform(self):
        return self.source
    
    @property
    def content(self):
        return self.original_input
    
    @property
    def user_phone(self):
        # This is a bit tricky since we don't have the user object here usually
        # But for serialization it might be needed. 
        # api/routes.py uses it.
        return "" # Default or handle in route


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

class CognitiveEntry(Base):
    """Spec-compliant unified storage for cognitive entries (Learn/Think/Reflect)."""
    __tablename__ = "cognitive_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    input_type = Column(String(50), nullable=False)  # link, voice, text
    cognitive_mode = Column(String(50), nullable=False) # learn, think, reflect
    original_input = Column(Text, nullable=False)
    source_url = Column(String(2048), nullable=True)
    cleaned_text = Column(Text, default="")
    summary = Column(Text, default="")
    title = Column(String(512), default="")
    key_points = Column(JSON, default=[])
    bucket = Column(String(100), default="Uncategorized")
    tags = Column(JSON, default=[])
    actionability_score = Column(Float, default=0.0)
    emotional_tone = Column(String(100), default="")
    confidence_score = Column(Float, default=0.0)
    resurfaced_count = Column(Integer, default=0)
    last_resurfaced_at = Column(DateTime(timezone=True), nullable=True)
    processing_status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class Bucket(Base):
    """Spec-compliant bucket system (Cap at 20 per user)."""
    __tablename__ = "buckets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    entry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (UniqueConstraint('user_id', 'name', name='_user_bucket_uc'),)

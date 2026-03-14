"""
Thredion Engine — Database Models
SQLAlchemy ORM models for the cognitive memory engine.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, Integer, String, Float, Text, DateTime, LargeBinary, ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


# ── Auth Models ───────────────────────────────────────────────


class User(Base):
    """A registered user, identified by their WhatsApp phone number."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    last_login = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class OTPCode(Base):
    """Temporary OTP codes sent via WhatsApp for authentication."""
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(50), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    expires_at = Column(DateTime, nullable=False)


# ── Memory Models ─────────────────────────────────────────────


class Memory(Base):
    """A single cognitive memory — a saved link with AI-enriched metadata."""
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False, index=True)
    platform = Column(String(50), default="unknown")       # instagram, twitter, article, youtube
    title = Column(String(512), default="")
    content = Column(Text, default="")                       # original caption / text / description
    summary = Column(Text, default="")                       # AI-generated summary
    category = Column(String(100), default="Uncategorized")
    tags = Column(Text, default="[]")                        # JSON list
    topic_graph = Column(Text, default="[]")                 # JSON hierarchy
    embedding = Column(LargeBinary, nullable=True)           # pickled numpy array
    importance_score = Column(Float, default=50.0)
    importance_reasons = Column(Text, default="[]")          # JSON list of reasons
    thumbnail_url = Column(String(2048), default="")
    user_phone = Column(String(50), default="default", index=True)
    created_at = Column(DateTime, default=_utcnow)
    
    # ── NEW: Video Transcription Fields ────────────────────────
    transcript = Column(Text, default="", nullable=True)     # Full video transcript
    transcript_length = Column(Integer, default=0)           # Character count of transcript
    transcript_source = Column(String(20), default="pending") # local|groq|openai|failed
    video_duration = Column(Integer, default=0)              # Duration in seconds
    is_video = Column(Boolean, default=False)                # Flag: is this video content?
    
    # ── NEW: Cognitive Structure Fields ────────────────────────
    cognitive_mode = Column(String(20), default="learn")     # learn|think|reflect
    title_generated = Column(String(512), default="")        # AI-generated title
    key_points = Column(Text, default="[]")                  # JSON array of key insights
    bucket = Column(String(100), default="Uncategorized")    # Semantic bucket/category
    actionability_score = Column(Float, default=0.0)         # 0-1 score
    emotional_tone = Column(String(50), default="")          # neutral|excited|anxious|etc
    confidence_score = Column(Float, default=0.0)            # 0-1 confidence
    
    # ── NEW: Async Job Tracking ────────────────────────────────
    transcription_job_id = Column(String(100), default=None, nullable=True, index=True)
    transcription_status = Column(String(20), default="pending")  # pending|processing|completed|failed
    processing_error = Column(Text, default=None, nullable=True)
    processed_at = Column(DateTime, default=None, nullable=True)

    # ── NEW: Realistic Architecture Fields ──────────────────────
    source_type = Column(String(50), default="metadata_only")  # yt_transcript_api|yt_subtitle|local_asr|
                                                                  # cookies_asr|caption_only|post_text_only|etc
    failure_reason = Column(Text, default=None, nullable=True)   # Human-readable failure reason
    failure_class = Column(String(20), default=None, nullable=True)  # transient|auth|permanent|unsupported
    
    credits_spent = Column(Float, default=0.0)                  # Track third-party API costs
    fallback_attempted = Column(Boolean, default=False)         # Did we try multiple methods?
    extraction_time_ms = Column(Integer, default=0)             # Extraction duration
    
    transcript_quality_score = Column(Float, default=None, nullable=True)  # 0-1 quality
    content_hash = Column(String(64), default=None, nullable=True)  # SHA256 for dedup
    canonical_url = Column(String(2048), default=None, nullable=True, index=True)  # Normalized URL
    
    cached_until = Column(DateTime, default=None, nullable=True)  # When to re-check if failed
    last_failure_at = Column(DateTime, default=None, nullable=True)  # Last error time
    
    job_id = Column(String(100), default=None, nullable=True, unique=True, index=True)  # Async job ref
    job_status = Column(String(20), default="completed")  # queued|extracting|transcribing|
                                                            # classifying|completed|failed|partial|unavailable
    job_priority = Column(Integer, default=5)              # 1=urgent, 10=background
    
    detected_language = Column(String(10), default=None, nullable=True)  # "en", "es", etc

    __table_args__ = (
        UniqueConstraint("url", "user_phone", name="uq_memory_url_user"),
        UniqueConstraint("canonical_url", "user_phone", name="uq_memory_canonical_user"),
    )

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

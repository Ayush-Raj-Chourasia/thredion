
from datetime import datetime
from typing import Optional, List, Literal, Dict
from pydantic import BaseModel, Field
from uuid import UUID

# ── User Models ──────────────────

class UserBase(BaseModel):
    phone_number: str
    username: Optional[str] = None
    email: Optional[str] = None

class User(UserBase):
    id: UUID
    pending_weekly_summary: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ── Cognitive Entry Models ───────

class CognitiveEntryBase(BaseModel):
    input_type: Literal["link", "voice", "text"]
    cognitive_mode: Literal["learn", "think", "reflect"]
    original_input: str
    source_url: Optional[str] = None

class CognitiveEntryCreate(CognitiveEntryBase):
    pass

class CognitiveEntry(CognitiveEntryBase):
    id: UUID
    user_id: UUID
    cleaned_text: Optional[str] = None
    summary: Optional[str] = None
    title: Optional[str] = None
    key_points: List[str] = []
    bucket: Optional[str] = None
    tags: List[str] = []
    actionability_score: float = 0.0
    emotional_tone: Optional[str] = None
    confidence_score: float = 0.0
    resurfaced_count: int = 0
    last_resurfaced_at: Optional[datetime] = None
    processing_status: Literal["pending", "processing", "completed", "failed"] = "pending"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ── Structured Output Model ──────

class LLMStructuredOutput(BaseModel):
    cognitive_mode: Literal["learn", "think", "reflect"]
    title: str = Field(description="Concise title, max 10 words")
    summary: str = Field(description="2-3 sentence summary of the core content/idea")
    key_points: List[str] = Field(description="List of key insights")
    bucket: str = Field(description="Broad category name")
    tags: List[str] = Field(description="Relevant tags")
    actionability_score: float = Field(ge=0.0, le=1.0, description="0.0 to 1.0 score")
    emotional_tone: str = Field(description="One word: neutral/curious/anxious/excited/reflective/motivated/frustrated/hopeful")
    confidence_score: float = Field(ge=0.0, le=1.0, description="0.0 to 1.0 confidence")

# ── Dashboard & API Support ──────

class WeeklySummary(BaseModel):
    entries_by_mode: Dict[str, int]
    entries_by_bucket: List[dict]
    top_entries: List[CognitiveEntry]
    most_active_bucket: Optional[str]
    total_count: int

class ProcessRequest(BaseModel):
    phone_number: str
    message_text: Optional[str] = None
    voice_file_url: Optional[str] = None
    source_url: Optional[str] = None

"""
Thredion Engine — Pydantic Schemas
Request / response models for the API layer.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────

class MemoryCreate(BaseModel):
    url: str
    user_phone: str = "default"


class ProcessRequest(BaseModel):
    url: str
    user_phone: str = "default"


# ── Responses ─────────────────────────────────────────────────

class MemoryResponse(BaseModel):
    id: int
    url: str
    platform: str
    title: str
    content: str
    summary: str
    category: str
    tags: list[str] = []
    topic_graph: list[str] = []
    importance_score: float
    importance_reasons: list[str] = []
    thumbnail_url: str
    user_phone: str
    created_at: datetime
    connections: list[ConnectionBrief] = []

    class Config:
        from_attributes = True


class ConnectionBrief(BaseModel):
    connected_memory_id: int
    connected_memory_title: str
    connected_memory_summary: str
    connected_memory_category: str
    similarity_score: float


class ResurfacedResponse(BaseModel):
    id: int
    memory_id: int
    memory_title: str
    memory_summary: str
    memory_category: str
    memory_url: str
    triggered_by_id: int
    triggered_by_title: str
    reason: str
    similarity_score: float
    created_at: datetime


class GraphNode(BaseModel):
    id: int
    title: str
    category: str
    importance_score: float
    url: str


class GraphEdge(BaseModel):
    source: int
    target: int
    weight: float


class KnowledgeGraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class StatsResponse(BaseModel):
    total_memories: int
    total_connections: int
    total_resurfaced: int
    categories: dict[str, int]
    avg_importance: float
    top_category: str


class BotReply(BaseModel):
    summary: str
    category: str
    importance_score: float
    resurfaced: list[str] = []
    message: str


# Forward reference resolution
MemoryResponse.model_rebuild()

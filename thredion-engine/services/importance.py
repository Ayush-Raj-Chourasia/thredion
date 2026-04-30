"""
Thredion Engine — Importance Scorer
Computes an explainable importance score for each memory.
"""

import json
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from db.models import Memory, Connection
from services.embeddings import embedding_to_vector, cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class ImportanceResult:
    score: float
    reasons: list[str]


def compute_importance(
    memory: Memory,
    db: Session,
    all_memories: list[Memory] | None = None,
) -> ImportanceResult:
    """
    Calculate an explainable importance score for a memory (0-100).

    Scoring dimensions:
    1. Content Richness   (0-25)  — How much meaningful content
    2. Novelty            (0-25)  — How different from existing memories
    3. Connectivity       (0-25)  — How many connections it forms
    4. Topic Relevance    (0-25)  — Alignment with user's interests
    """
    reasons: list[str] = []

    # ── 1. Content Richness (0-25) ───────────────────────────
    richness = _score_richness(memory)
    reasons.append(f"Content Richness: {richness}/25")

    # ── 2. Novelty (0-25) ────────────────────────────────────
    novelty = _score_novelty(memory, db, all_memories)
    reasons.append(f"Novelty: {novelty}/25")

    # ── 3. Connectivity Potential (0-25) ─────────────────────
    connectivity = _score_connectivity(memory, db)
    reasons.append(f"Connectivity: {connectivity}/25")

    # ── 4. Topic Relevance (0-25) ────────────────────────────
    relevance = _score_relevance(memory, db, all_memories)
    reasons.append(f"Topic Relevance: {relevance}/25")

    # ── Final Score ──────────────────────────────────────────
    total = richness + novelty + connectivity + relevance
    total = max(0.0, min(100.0, total))

    if total >= 80:
        reasons.append("High-value insight — keep this one close!")
    elif total >= 60:
        reasons.append("Solid content — worth revisiting.")
    elif total >= 40:
        reasons.append("Moderate value — may gain relevance over time.")
    else:
        reasons.append("Low priority — but still saved for you.")

    return ImportanceResult(score=round(total, 1), reasons=reasons)


def _score_richness(memory: Memory) -> float:
    """Score based on content length, summary quality, and tags."""
    score = 0.0
    content = memory.content or ""
    summary = memory.summary or ""
    tags = memory.tags if isinstance(memory.tags, list) else (json.loads(memory.tags) if memory.tags else [])

    # Content length
    word_count = len(content.split())
    if word_count > 100:
        score += 10
    elif word_count > 50:
        score += 7
    elif word_count > 20:
        score += 4
    else:
        score += 2

    # Summary exists and is meaningful
    if len(summary) > 30:
        score += 5
    elif len(summary) > 10:
        score += 3

    # Has tags
    if len(tags) >= 3:
        score += 5
    elif len(tags) >= 1:
        score += 3

    # Has title
    if memory.title and len(memory.title) > 5:
        score += 5

    return min(25.0, score)


def _score_novelty(
    memory: Memory, db: Session, all_memories: list[Memory] | None = None,
) -> float:
    """Score based on how different this memory is from existing ones."""
    if not memory.embedding:
        return 15.0  # Default mid-range novelty

    new_vec = embedding_to_vector(memory.embedding)
    if new_vec is None:
        return 15.0

    if all_memories is None:
        all_memories = (
            db.query(Memory)
            .filter(Memory.id != memory.id)
            .filter(Memory.user_id == memory.user_id)
            .filter(Memory.embedding.isnot(None))
            .all()
        )

    if not all_memories:
        return 25.0  # First memory is always novel

    # Calculate average similarity to existing memories
    similarities = []
    for m in all_memories:
        if m.id == memory.id:
            continue
        vec = embedding_to_vector(m.embedding)
        if vec is not None:
            sim = cosine_similarity(new_vec, vec)
            similarities.append(sim)

    if not similarities:
        return 25.0

    avg_sim = sum(similarities) / len(similarities)
    max_sim = max(similarities)

    # Lower similarity = higher novelty
    # avg_sim close to 0 → very novel (score ~25)
    # avg_sim close to 1 → not novel (score ~0)
    novelty = (1 - avg_sim) * 20 + (1 - max_sim) * 5

    return min(25.0, max(0.0, round(novelty, 1)))


def _score_connectivity(memory: Memory, db: Session) -> float:
    """Score based on how many connections this memory has or will form."""
    connections_count = (
        db.query(Connection)
        .filter(
            (Connection.source_id == memory.id) | (Connection.target_id == memory.id)
        )
        .count()
    )

    if connections_count >= 5:
        return 25.0
    elif connections_count >= 3:
        return 20.0
    elif connections_count >= 2:
        return 15.0
    elif connections_count >= 1:
        return 10.0
    else:
        return 5.0


def _score_relevance(
    memory: Memory, db: Session, all_memories: list[Memory] | None = None,
) -> float:
    """Score based on alignment with user's frequently saved categories."""
    if all_memories is None:
        all_memories = (
            db.query(Memory)
            .filter(Memory.id != memory.id)
            .filter(Memory.user_id == memory.user_id)
            .all()
        )

    if not all_memories:
        return 15.0

    # Count category frequency
    category_counts: dict[str, int] = {}
    for m in all_memories:
        cat = m.category or "Uncategorized"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    total = sum(category_counts.values())
    if total == 0:
        return 15.0

    my_category = memory.category or "Uncategorized"
    my_count = category_counts.get(my_category, 0)
    frequency_ratio = my_count / total

    # High frequency → user is interested in this topic → higher relevance
    # But also reward rare categories slightly (diversity bonus)
    if frequency_ratio > 0.3:
        score = 22.0  # Strong match with user interests
    elif frequency_ratio > 0.15:
        score = 18.0
    elif frequency_ratio > 0.05:
        score = 14.0
    elif my_count == 0:
        score = 10.0  # New category — diversity bonus
    else:
        score = 12.0

    return min(25.0, score)

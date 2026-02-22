"""
Thredion Engine — Core Processing Pipeline
The main orchestrator that chains extraction → embedding → classification →
knowledge graph → importance → resurfacing.
"""

import json
import logging

from sqlalchemy.orm import Session

from db.models import Memory
from services.extractor import extract_from_url
from services.embeddings import generate_embedding
from services.classifier import classify_content
from services.knowledge_graph import build_connections
from services.importance import compute_importance
from services.resurfacing import find_resurfaceable

logger = logging.getLogger(__name__)


def process_url(url: str, user_phone: str, db: Session) -> dict:
    """
    Full cognitive pipeline: URL → extract → embed → classify → graph → score → resurface.
    Returns a dict with all results for the WhatsApp reply and API response.
    """
    # ── Step 1: Extract content from the URL ─────────────────
    logger.info(f"[Pipeline] Extracting content from {url}")
    extracted = extract_from_url(url)

    combined_text = f"{extracted.title} {extracted.content}".strip()
    if not combined_text:
        combined_text = url

    # ── Step 2: Generate embedding ───────────────────────────
    logger.info("[Pipeline] Generating embedding")
    embedding_bytes = generate_embedding(combined_text)

    # ── Step 3: Classify and summarize ───────────────────────
    logger.info("[Pipeline] Classifying content")
    classification = classify_content(combined_text, url)

    # ── Step 4: Save to database ─────────────────────────────
    memory = Memory(
        url=url,
        platform=extracted.platform,
        title=extracted.title or classification.summary[:100],
        content=extracted.content,
        summary=classification.summary,
        category=classification.category,
        tags=json.dumps(classification.tags),
        topic_graph=json.dumps(classification.topic_graph),
        embedding=embedding_bytes,
        thumbnail_url=extracted.thumbnail_url,
        user_phone=user_phone,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    logger.info(f"[Pipeline] Saved memory #{memory.id}")

    # ── Step 5: Build knowledge graph connections ────────────
    logger.info("[Pipeline] Building knowledge graph connections")
    connections = build_connections(memory, db)

    # ── Step 6: Compute importance score ─────────────────────
    logger.info("[Pipeline] Computing importance score")
    importance = compute_importance(memory, db)
    memory.importance_score = importance.score
    memory.importance_reasons = json.dumps(importance.reasons)
    db.commit()

    # ── Step 7: Check for resurfaceable memories ─────────────
    logger.info("[Pipeline] Checking for resurfaceable memories")
    resurfaced = find_resurfaceable(memory, db)

    # ── Build result ─────────────────────────────────────────
    result = {
        "memory_id": memory.id,
        "url": url,
        "platform": extracted.platform,
        "title": memory.title,
        "summary": classification.summary,
        "category": classification.category,
        "tags": classification.tags,
        "topic_graph": classification.topic_graph,
        "importance_score": importance.score,
        "importance_reasons": importance.reasons,
        "connections": connections,
        "resurfaced": resurfaced,
        "thumbnail_url": extracted.thumbnail_url,
    }

    logger.info(
        f"[Pipeline] Complete — Memory #{memory.id} | "
        f"Category: {classification.category} | "
        f"Importance: {importance.score} | "
        f"Connections: {len(connections)} | "
        f"Resurfaced: {len(resurfaced)}"
    )

    return result

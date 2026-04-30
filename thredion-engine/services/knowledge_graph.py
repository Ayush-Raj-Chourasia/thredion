"""
Thredion Engine — Knowledge Graph Builder
Automatically connects related memories based on semantic similarity.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from core.config import settings
from db.models import Memory, Connection
from services.embeddings import embedding_to_vector, cosine_similarity

logger = logging.getLogger(__name__)


def build_connections(new_memory: Memory, db: Session) -> list[dict]:
    """
    Find and create connections between a new memory and existing ones.
    Returns list of created connections with details.
    """
    if not new_memory.embedding:
        logger.warning(f"Memory {new_memory.id} has no embedding — skipping graph build.")
        return []

    new_vec = embedding_to_vector(new_memory.embedding)
    if new_vec is None:
        return []

    # Fetch other memories with embeddings belonging to the same user
    existing = (
        db.query(Memory)
        .filter(Memory.id != new_memory.id)
        .filter(Memory.user_id == new_memory.user_id)
        .filter(Memory.embedding.isnot(None))
        .all()
    )

    connections_created = []
    similarities = []

    for memory in existing:
        existing_vec = embedding_to_vector(memory.embedding)
        if existing_vec is None:
            continue

        sim = cosine_similarity(new_vec, existing_vec)

        if sim >= settings.SIMILARITY_THRESHOLD:
            similarities.append((memory, sim))

    # Sort by similarity and keep top N
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_connections = similarities[: settings.MAX_CONNECTIONS]

    for memory, sim in top_connections:
        # Check if connection already exists
        existing_conn = (
            db.query(Connection)
            .filter(
                ((Connection.source_id == new_memory.id) & (Connection.target_id == memory.id))
                | ((Connection.source_id == memory.id) & (Connection.target_id == new_memory.id))
            )
            .first()
        )

        if existing_conn:
            continue

        conn = Connection(
            user_id=new_memory.user_id,
            source_id=new_memory.id,
            target_id=memory.id,
            similarity_score=round(sim, 4),
        )
        db.add(conn)
        connections_created.append({
            "connected_memory_id": memory.id,
            "connected_memory_title": memory.title or memory.summary[:50],
            "connected_memory_category": memory.category,
            "similarity_score": round(sim, 4),
        })

    if connections_created:
        db.commit()
        logger.info(
            f"Created {len(connections_created)} connections for memory {new_memory.id}"
        )

    return connections_created


def get_full_graph(db: Session, user_id: str = "") -> dict:
    """
    Build the knowledge graph for the dashboard, scoped to a user.
    Returns nodes and edges.
    """
    from db.database import SupabaseSession
    if isinstance(db, SupabaseSession):
        memories = db.get_memories(user_id, limit=1000)
        connections = db.get_connections(user_id)
        
        mem_ids = {str(getattr(m, 'id')) for m in memories}
        
        nodes = [
            {
                "id": getattr(m, 'id'),
                "title": getattr(m, 'title') or (getattr(m, 'summary', '')[:40] if getattr(m, 'summary') else f"Memory #{getattr(m, 'id')}"),
                "category": getattr(m, 'category'),
                "importance_score": getattr(m, 'importance_score', 0),
                "url": getattr(m, 'url'),
            }
            for m in memories
        ]
        
        edges = [
            {
                "source": getattr(c, 'source_id'),
                "target": getattr(c, 'target_id'),
                "weight": getattr(c, 'similarity_score', 0.0),
            }
            for c in connections
            if str(getattr(c, 'source_id')) in mem_ids and str(getattr(c, 'target_id')) in mem_ids
        ]
        
        return {"nodes": nodes, "edges": edges}

    q = db.query(Memory)
    if user_id:
        q = q.filter(Memory.user_id == user_id)
    memories = q.all()
    mem_ids = {m.id for m in memories}
    connections = [
        c for c in db.query(Connection).all()
        if c.source_id in mem_ids and c.target_id in mem_ids
    ]

    nodes = [
        {
            "id": m.id,
            "title": m.title or (m.summary[:40] if m.summary else f"Memory #{m.id}"),
            "category": m.category,
            "importance_score": m.importance_score,
            "url": m.url,
        }
        for m in memories
    ]

    edges = [
        {
            "source": c.source_id,
            "target": c.target_id,
            "weight": c.similarity_score,
        }
        for c in connections
    ]

    return {"nodes": nodes, "edges": edges}


def get_memory_connections(memory_id: int, db: Session) -> list[dict]:
    """Get all connections for a specific memory."""
    from db.database import SupabaseSession
    if isinstance(db, SupabaseSession):
        # We need a custom method to get connections for a specific memory
        # since SupabaseSession currently only has get_connections by user_id.
        res = db.sb.table("connections").select("*").or_(f"source_id.eq.{memory_id},target_id.eq.{memory_id}").execute()
        connections = res.data or []
        
        result = []
        for conn in connections:
            other_id = conn['target_id'] if conn['source_id'] == memory_id else conn['source_id']
            other_res = db.sb.table("memories").select("*").eq("id", other_id).limit(1).execute()
            if other_res.data:
                other = other_res.data[0]
                result.append({
                    "connected_memory_id": other['id'],
                    "connected_memory_title": other.get('title') or other.get('summary', '')[:50],
                    "connected_memory_summary": other.get('summary'),
                    "connected_memory_category": other.get('category'),
                    "similarity_score": conn.get('similarity_score', 0.0),
                })
        return result

    connections = (
        db.query(Connection)
        .filter(
            (Connection.source_id == memory_id) | (Connection.target_id == memory_id)
        )
        .all()
    )

    result = []
    for conn in connections:
        # Determine the connected memory (the other end)
        if conn.source_id == memory_id:
            other = db.query(Memory).filter(Memory.id == conn.target_id).first()
        else:
            other = db.query(Memory).filter(Memory.id == conn.source_id).first()

        if other:
            result.append({
                "connected_memory_id": other.id,
                "connected_memory_title": other.title or other.summary[:50],
                "connected_memory_summary": other.summary,
                "connected_memory_category": other.category,
                "similarity_score": conn.similarity_score,
            })

    return result

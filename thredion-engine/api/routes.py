"""
Thredion Engine — REST API Routes
Endpoints for the cognitive dashboard and manual interactions.
"""

import asyncio
import json
import logging
import re

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.database import get_db
from db.models import Memory, Connection, ResurfacedMemory
from services.pipeline import process_url
from services.knowledge_graph import get_full_graph, get_memory_connections
from services.resurfacing import get_recent_resurfaced

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["memories"])

# ── SSE Event Bus ─────────────────────────────────────────────
# Simple in-process pub/sub for server-sent events

_sse_subscribers: list[asyncio.Queue] = []


def notify_change(event_type: str = "update", data: str = ""):
    """Broadcast a change event to all SSE subscribers."""
    payload = json.dumps({"type": event_type, "data": data})
    dead = []
    for q in _sse_subscribers:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _sse_subscribers.remove(q)


async def _sse_generator(queue: asyncio.Queue):
    """Yield SSE-formatted events from the queue."""
    try:
        while True:
            payload = await asyncio.wait_for(queue.get(), timeout=30)
            yield f"data: {payload}\n\n"
    except asyncio.TimeoutError:
        # Send a keep-alive comment to prevent connection timeout
        yield ": keepalive\n\n"
    except asyncio.CancelledError:
        return


async def _sse_stream(queue: asyncio.Queue):
    """Infinite SSE stream with keep-alive."""
    try:
        while True:
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=25)
                yield f"data: {payload}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
    except asyncio.CancelledError:
        return
    finally:
        if queue in _sse_subscribers:
            _sse_subscribers.remove(queue)


@router.get("/events")
async def sse_events():
    """Server-Sent Events endpoint for real-time dashboard updates."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    _sse_subscribers.append(queue)
    return StreamingResponse(
        _sse_stream(queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Memories ──────────────────────────────────────────────────


@router.get("/memories")
def list_memories(
    search: str = Query("", description="Search term"),
    category: str = Query("", description="Filter by category"),
    sort: str = Query("newest", description="Sort: newest, oldest, importance"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all memories with optional search, filter, and sort."""
    query = db.query(Memory)

    if search:
        term = f"%{search}%"
        query = query.filter(
            Memory.title.ilike(term)
            | Memory.summary.ilike(term)
            | Memory.content.ilike(term)
            | Memory.category.ilike(term)
            | Memory.tags.ilike(term)
        )

    if category:
        query = query.filter(Memory.category == category)

    if sort == "oldest":
        query = query.order_by(Memory.created_at.asc())
    elif sort == "importance":
        query = query.order_by(Memory.importance_score.desc())
    else:
        query = query.order_by(Memory.created_at.desc())

    memories = query.limit(limit).all()

    return [_serialize_memory(m) for m in memories]


@router.get("/memories/{memory_id}")
def get_memory(memory_id: int, db: Session = Depends(get_db)):
    """Get a single memory with its connections."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    result = _serialize_memory(memory)
    result["connections"] = get_memory_connections(memory_id, db)
    return result


@router.post("/memories")
def create_memory(
    url: str = Query(..., description="URL to save"),
    user_phone: str = Query("default", description="User identifier"),
    db: Session = Depends(get_db),
):
    """Manually add a new memory via URL."""
    url = url.strip()
    if not re.match(r'^https?://', url):
        raise HTTPException(status_code=400, detail="Invalid URL — must start with http:// or https://")
    try:
        result = process_url(url, user_phone, db)
        notify_change("memory_added", str(result.get("memory_id", "")))
        return result
    except Exception as e:
        logger.error(f"Memory creation failed for {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Creation failed: {str(e)}")


@router.delete("/memories/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    """Delete a memory and all its related connections/resurfaced entries."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    # Delete related connections (both directions)
    db.query(Connection).filter(
        (Connection.source_id == memory_id) | (Connection.target_id == memory_id)
    ).delete(synchronize_session=False)
    # Delete related resurfaced entries
    db.query(ResurfacedMemory).filter(
        (ResurfacedMemory.memory_id == memory_id) | (ResurfacedMemory.triggered_by_id == memory_id)
    ).delete(synchronize_session=False)
    db.delete(memory)
    db.commit()
    notify_change("memory_deleted", str(memory_id))
    return {"detail": "Memory deleted", "id": memory_id}


# ── Process Endpoint ──────────────────────────────────────────


@router.post("/process")
def process_endpoint(
    url: str = Query(..., description="URL to process"),
    user_phone: str = Query("default"),
    db: Session = Depends(get_db),
):
    """Process a URL through the full cognitive pipeline (for testing)."""
    url = url.strip()
    if not re.match(r'^https?://', url):
        raise HTTPException(status_code=400, detail="Invalid URL — must start with http:// or https://")
    try:
        result = process_url(url, user_phone, db)
        notify_change("memory_added", str(result.get("memory_id", "")))
        return result
    except Exception as e:
        logger.error(f"Pipeline error for {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ── Knowledge Graph ───────────────────────────────────────────


@router.get("/graph")
def get_knowledge_graph(db: Session = Depends(get_db)):
    """Get the full knowledge graph (nodes + edges)."""
    return get_full_graph(db)


# ── Resurfaced Insights ──────────────────────────────────────


@router.get("/resurfaced")
def get_resurfaced(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get recently resurfaced memories."""
    return get_recent_resurfaced(db, limit)


# ── Statistics ────────────────────────────────────────────────


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    total_memories = db.query(func.count(Memory.id)).scalar() or 0
    total_connections = db.query(func.count(Connection.id)).scalar() or 0
    total_resurfaced = db.query(func.count(ResurfacedMemory.id)).scalar() or 0

    # Category distribution
    categories_raw = (
        db.query(Memory.category, func.count(Memory.id))
        .group_by(Memory.category)
        .all()
    )
    categories = {cat: count for cat, count in categories_raw}

    avg_importance = (
        db.query(func.avg(Memory.importance_score)).scalar() or 0.0
    )

    top_category = max(categories, key=categories.get) if categories else "None"

    return {
        "total_memories": total_memories,
        "total_connections": total_connections,
        "total_resurfaced": total_resurfaced,
        "categories": categories,
        "avg_importance": round(avg_importance, 1),
        "top_category": top_category,
    }


# ── Categories ────────────────────────────────────────────────


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get all categories with counts."""
    results = (
        db.query(Memory.category, func.count(Memory.id))
        .group_by(Memory.category)
        .order_by(func.count(Memory.id).desc())
        .all()
    )
    return [{"category": cat, "count": count} for cat, count in results]


# ── Random Inspiration ───────────────────────────────────────


@router.get("/random")
def get_random_memory(db: Session = Depends(get_db)):
    """Get a random memory for the 'Random Inspiration' feature."""
    memory = db.query(Memory).order_by(func.random()).first()
    if not memory:
        raise HTTPException(status_code=404, detail="No memories yet")
    return _serialize_memory(memory)


# ── Helpers ───────────────────────────────────────────────────


def _serialize_memory(memory: Memory) -> dict:
    """Convert a Memory ORM object to a JSON-serializable dict."""
    return {
        "id": memory.id,
        "url": memory.url,
        "platform": memory.platform,
        "title": memory.title,
        "content": memory.content[:500] if memory.content else "",
        "summary": memory.summary,
        "category": memory.category,
        "tags": json.loads(memory.tags) if memory.tags else [],
        "topic_graph": json.loads(memory.topic_graph) if memory.topic_graph else [],
        "importance_score": memory.importance_score,
        "importance_reasons": (
            json.loads(memory.importance_reasons) if memory.importance_reasons else []
        ),
        "thumbnail_url": memory.thumbnail_url,
        "user_phone": memory.user_phone,
        "created_at": memory.created_at.isoformat() if memory.created_at else "",
    }

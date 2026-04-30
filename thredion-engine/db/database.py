"""
Thredion Engine — Database Setup
Dual-mode database layer:
  - Production (HF Spaces): Uses Supabase REST API over HTTPS (port 443)
    because the direct PostgreSQL endpoint is IPv6-only and unreachable.
  - Local dev: Uses SQLAlchemy + psycopg2 direct connection.

The Supabase REST client (`supabase-py`) communicates over HTTPS,
which works on every platform including restricted containers.
"""

import os
import logging
from datetime import datetime, timezone

from core.config import settings

logger = logging.getLogger("thredion")

# ── Supabase REST Client (production) ────────────────────────

_supabase_client = None

def _get_supabase():
    """Lazy-init Supabase REST client."""
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info(f"Supabase REST client initialized: {settings.SUPABASE_URL}")
    return _supabase_client


def _use_supabase_rest():
    """Decide whether to use Supabase REST API instead of direct PostgreSQL."""
    # Use REST if we have Supabase credentials AND we're in a restricted environment
    # (HF Spaces, or explicit env var)
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return False
    # Force REST mode via env var, or auto-detect HF Spaces
    if os.getenv("USE_SUPABASE_REST", "").lower() == "true":
        return True
    if os.getenv("SPACE_ID") is not None:
        return True
    # Check if direct DB connection is likely to fail (IPv6-only host)
    if "postgresql" in settings.DATABASE_URL.lower():
        import socket
        try:
            from urllib.parse import urlparse
            parsed = urlparse(settings.DATABASE_URL)
            host = parsed.hostname
            if host:
                socket.getaddrinfo(host, parsed.port or 5432, socket.AF_INET)
                return False  # IPv4 available, use direct connection
        except socket.gaierror:
            logger.warning(f"No IPv4 for DB host, switching to Supabase REST API")
            return True
    return False


USE_REST = _use_supabase_rest()
logger.info(f"Database mode: {'Supabase REST API' if USE_REST else 'Direct PostgreSQL/SQLite'}")


# ── SQLAlchemy fallback (local dev) ──────────────────────────

if not USE_REST:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, declarative_base

    connect_args = {}
    if "sqlite" in settings.DATABASE_URL.lower():
        connect_args = {"check_same_thread": False}

    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        echo=False,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
else:
    # Stubs so imports don't crash
    engine = None
    SessionLocal = None
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


# ── Supabase REST helpers ────────────────────────────────────

class SupabaseRow:
    """Lightweight object that mimics a SQLAlchemy model row."""
    def __init__(self, data: dict):
        self._data = data
        for k, v in data.items():
            setattr(self, k, v)
            
    def get(self, key, default=None):
        return self._data.get(key, default)
        
    def __getattr__(self, name):
        # Prevent AttributeError for missing columns
        return None
    
    def __repr__(self):
        return f"<SupabaseRow {self._data}>"


class SupabaseSession:
    """
    Minimal session-like wrapper around the Supabase REST client.
    Provides just enough interface to satisfy the existing code.
    """
    def __init__(self):
        self.sb = _get_supabase()
    
    def query_table(self, table_name: str):
        """Get a query builder for a table."""
        return self.sb.table(table_name)
    
    def get_user_by_phone(self, phone: str):
        """Look up a user by phone number."""
        result = self.sb.table("users").select("*").eq("phone_number", phone).limit(1).execute()
        if result.data:
            return SupabaseRow(result.data[0])
        return None
    
    def get_user_by_id(self, user_id: str):
        """Look up a user by ID."""
        result = self.sb.table("users").select("*").eq("id", str(user_id)).limit(1).execute()
        if result.data:
            return SupabaseRow(result.data[0])
        return None
    
    def get_memories(self, user_id: str, sort="newest", category=None, search=None, limit=50, offset=0):
        """Fetch memories for a user with filtering and sorting."""
        q = self.sb.table("memories").select("*").eq("user_id", str(user_id))
        if category and category != "all":
            q = q.eq("category", category)
        if search:
            q = q.ilike("title", f"%{search}%")
        if sort == "newest":
            q = q.order("created_at", desc=True)
        elif sort == "oldest":
            q = q.order("created_at", desc=False)
        elif sort == "importance":
            q = q.order("importance_score", desc=True)
        q = q.range(offset, offset + limit - 1)
        result = q.execute()
        return [SupabaseRow(r) for r in (result.data or [])]
    
    def count_memories(self, user_id: str):
        """Count total memories for a user."""
        result = self.sb.table("memories").select("id", count="exact").eq("user_id", str(user_id)).execute()
        return result.count or 0
    
    def get_memory_by_id(self, memory_id: str, user_id: str = None):
        """Fetch a single memory by ID."""
        q = self.sb.table("memories").select("*").eq("id", str(memory_id))
        if user_id:
            q = q.eq("user_id", str(user_id))
        result = q.limit(1).execute()
        if result.data:
            return SupabaseRow(result.data[0])
        return None
    
    def delete_memory(self, memory_id: str, user_id: str):
        """Delete a memory."""
        self.sb.table("memories").delete().eq("id", str(memory_id)).eq("user_id", str(user_id)).execute()
    
    def get_connections(self, user_id: str):
        """Fetch connections for a user."""
        result = self.sb.table("connections").select("*").eq("user_id", str(user_id)).execute()
        return [SupabaseRow(r) for r in (result.data or [])]
    
    def count_connections(self, user_id: str):
        """Count connections for a user."""
        result = self.sb.table("connections").select("id", count="exact").eq("user_id", str(user_id)).execute()
        return result.count or 0
    
    def get_resurfaced(self, user_id: str, limit=20):
        """Fetch resurfaced memories."""
        result = (self.sb.table("resurfaced_memories")
                  .select("*")
                  .eq("user_id", str(user_id))
                  .order("resurfaced_at", desc=True)
                  .limit(limit)
                  .execute())
        return [SupabaseRow(r) for r in (result.data or [])]
    
    def get_categories(self, user_id: str):
        """Get distinct categories for a user's memories."""
        result = (self.sb.table("memories")
                  .select("category")
                  .eq("user_id", str(user_id))
                  .execute())
        categories = set()
        for r in (result.data or []):
            cat = r.get("category", "Uncategorized")
            if cat:
                categories.add(cat)
        return sorted(categories)
    
    def get_stats(self, user_id: str):
        """Get dashboard stats for a user."""
        memories = self.sb.table("memories").select("id,category,importance_score,source,created_at", count="exact").eq("user_id", str(user_id)).execute()
        connections = self.sb.table("connections").select("id", count="exact").eq("user_id", str(user_id)).execute()
        resurfaced = self.sb.table("resurfaced_memories").select("id", count="exact").eq("user_id", str(user_id)).execute()
        
        total_memories = memories.count or 0
        total_connections = connections.count or 0
        total_resurfaced = resurfaced.count or 0
        
        # Calculate category distribution
        cat_counts = {}
        source_counts = {}
        total_importance = 0.0
        for m in (memories.data or []):
            cat = m.get("category", "Uncategorized")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            src = m.get("source", "unknown")
            source_counts[src] = source_counts.get(src, 0) + 1
            total_importance += float(m.get("importance_score", 0) or 0)
        
        avg_importance = total_importance / total_memories if total_memories > 0 else 0
        
        return {
            "total_memories": total_memories,
            "total_connections": total_connections,
            "total_resurfaced": total_resurfaced,
            "categories": cat_counts,
            "sources": source_counts,
            "average_importance": round(avg_importance, 2),
        }
    
    # Compatibility stubs
    def close(self):
        pass
    
    def commit(self):
        pass
    
    def rollback(self):
        pass
    
    def flush(self):
        pass


# ── Dependency: get_db ───────────────────────────────────────

def get_db():
    """
    Dependency: yields a database session.
    Returns either a SQLAlchemy session or a SupabaseSession.
    """
    if USE_REST:
        session = SupabaseSession()
        try:
            yield session
        finally:
            pass  # No cleanup needed for REST client
    else:
        init_db()
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


# ── Init (SQLAlchemy only) ───────────────────────────────────

_db_init_attempted = False

def init_db():
    """Initialize database tables (SQLAlchemy mode only)."""
    global _db_init_attempted
    if _db_init_attempted or USE_REST:
        return
    
    try:
        from db.models import User, OTPCode, Memory, Connection, ResurfacedMemory  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
        _db_init_attempted = True
    except Exception as e:
        logger.warning(f"Could not create tables: {type(e).__name__}: {e}")
        _db_init_attempted = False

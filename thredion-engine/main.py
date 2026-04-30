"""
Thredion Engine — Main Application
FastAPI entry point for the AI Cognitive Memory Engine.

IMPORTANT: Railway must have SUPABASE_DB_PASSWORD environment variable set.
"""

import logging
import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime

# Add the project root to path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.database import init_db
from api.routes import router as api_router
from api.whatsapp import router as whatsapp_router
from api.auth import router as auth_router
from app.api.cognitive import router as cognitive_router
from fastapi.responses import JSONResponse
import traceback

# ── Logging ───────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("thredion")

# ── Lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("  THREDION ENGINE — AI Cognitive Memory Engine")
    logger.info("=" * 60)
    
    # Initialize database tables on startup
    try:
        init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
    
    logger.info(f"Embedding model: {settings.EMBEDDING_MODEL}")
    
    # Pre-warm the embedding model in a background thread
    import threading
    def _prewarm():
        try:
            from services.embeddings import generate_embedding
            generate_embedding("warmup")
            logger.info("Embedding model pre-warmed ✓")
        except Exception as e:
            logger.warning(f"Embedding pre-warm failed: {e}")
    threading.Thread(target=_prewarm, daemon=True).start()
    
    yield
    logger.info("Thredion Engine shutting down.")

# ── FastAPI App ───────────────────────────────────────────────

app = FastAPI(
    title="Thredion Engine",
    description="AI Cognitive Memory Engine",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc()
        }
    )

# ── Routers ───────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(api_router)
app.include_router(whatsapp_router)
app.include_router(cognitive_router)

# ── Health & Root ─────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.5",
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/")
def root():
    return {
        "name": "Thredion Engine",
        "version": "1.0.5",
        "status": "running",
        "db_url_type": "postgresql" if "postgresql" in settings.DATABASE_URL.lower() else "sqlite"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

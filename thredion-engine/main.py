"""
Thredion Engine — Main Application
FastAPI entry point for the AI Cognitive Memory Engine.
"""

import logging
import sys
import os

# Add the project root to path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.database import init_db
from api.routes import router as api_router
from api.whatsapp import router as whatsapp_router

# ── Logging ───────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("thredion")

# ── FastAPI App ───────────────────────────────────────────────

app = FastAPI(
    title="Thredion Engine",
    description=(
        "AI Cognitive Memory Engine — transforms social media saves "
        "into an intelligent, searchable, self-organizing knowledge system."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3001",
        "https://thredion.vercel.app",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────

app.include_router(api_router)
app.include_router(whatsapp_router)

# ── Startup ───────────────────────────────────────────────────


@app.on_event("startup")
def startup():
    logger.info("=" * 60)
    logger.info("  THREDION ENGINE — AI Cognitive Memory Engine")
    logger.info("=" * 60)
    init_db()
    logger.info("Database initialized.")
    logger.info(f"Embedding model: {settings.EMBEDDING_MODEL}")
    logger.info(f"OpenAI configured: {'Yes' if settings.OPENAI_API_KEY else 'No (using fallback)'}")
    logger.info(f"Twilio configured: {'Yes' if settings.TWILIO_ACCOUNT_SID else 'No'}")
    logger.info(f"Frontend URL: {settings.FRONTEND_URL}")
    logger.info(f"Docs: http://localhost:{settings.PORT}/docs")
    logger.info("=" * 60)


# ── Root Endpoint ─────────────────────────────────────────────


@app.get("/")
def root():
    return {
        "name": "Thredion Engine",
        "version": "1.0.0",
        "status": "running",
        "description": "AI Cognitive Memory Engine",
        "docs": "/docs",
        "endpoints": {
            "memories": "/api/memories",
            "graph": "/api/graph",
            "resurfaced": "/api/resurfaced",
            "stats": "/api/stats",
            "categories": "/api/categories",
            "random": "/api/random",
            "process": "/api/process",
            "whatsapp_webhook": "/api/whatsapp/webhook",
        },
    }


# ── Run ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

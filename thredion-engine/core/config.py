"""
Thredion Engine — Configuration
Central configuration management for the cognitive memory engine.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./thredion.db")

    # ── OpenAI ────────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ── Twilio WhatsApp ───────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

    # ── Embedding Configuration ───────────────────────────────
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers")
    EMBEDDING_DIMENSION: int = 384  # MiniLM-L6-v2 dimension

    # ── Cognitive Thresholds ──────────────────────────────────
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.55"))
    RESURFACING_THRESHOLD: float = float(os.getenv("RESURFACING_THRESHOLD", "0.60"))
    MAX_CONNECTIONS: int = int(os.getenv("MAX_CONNECTIONS", "5"))

    # ── Categories ────────────────────────────────────────────
    CATEGORIES: list = [
        "Fitness", "Coding", "Design", "Food", "Travel",
        "Business", "Science", "Music", "Art", "Fashion",
        "Education", "Technology", "Health", "Finance", "Motivation",
        "Entertainment", "Sports", "Lifestyle", "DIY", "Photography",
    ]

    # ── Frontend ──────────────────────────────────────────────
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # ── Server ────────────────────────────────────────────────
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()

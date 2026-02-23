"""
Thredion Engine — Configuration
Central configuration management for the cognitive memory engine.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# On Azure Linux App Service, /home is persistent across deploys.
# Locally, use ./thredion.db in the current directory.
_default_db_path = "sqlite:///./thredion.db"
if os.path.isdir("/home"):
    os.makedirs("/home/data", exist_ok=True)
    _default_db_path = "sqlite:////home/data/thredion.db"


class Settings:
    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", _default_db_path)

    # ── OpenAI ────────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ── Twilio WhatsApp ───────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

    # ── Authentication ────────────────────────────────────────
    JWT_SECRET: str = os.getenv("JWT_SECRET", "thredion-secret-change-in-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "168"))  # 7 days
    OTP_EXPIRY_MINUTES: int = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))

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

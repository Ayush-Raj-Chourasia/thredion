"""
Thredion Engine — Database Setup
SQLite database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# Build connection args based on database type
# check_same_thread is SQLite-only; PostgreSQL doesn't accept it
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


def get_db():
    """Dependency: yields a database session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined in models. Fail gracefully in production."""
    import os
    import logging
    
    logger = logging.getLogger("thredion")
    is_production = os.getenv("ENVIRONMENT") == "production" or "railway" in os.getenv("HOSTNAME", "").lower()
    
    # SQLite-specific reset (delete file)
    if os.getenv("RESET_DATABASE") == "true" and "sqlite" in settings.DATABASE_URL.lower():
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            logger.info(f"RESET_DATABASE=true: Deleting SQLite database {db_path}")
            os.remove(db_path)
        else:
            logger.warning(f"RESET_DATABASE=true: SQLite file not found: {db_path}")
    
    # PostgreSQL reset would require dropping tables via SQL (not implemented for safety)
    if os.getenv("RESET_DATABASE") == "true" and "postgresql" in settings.DATABASE_URL.lower():
        logger.warning("RESET_DATABASE=true: PostgreSQL reset not implemented (manual drop required for safety)")
    
    try:
        from db.models import User, OTPCode, Memory, Connection, ResurfacedMemory  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables ensured to exist")
    except Exception as e:
        if is_production:
            # In production (Railway/Supabase), tables should already exist from migration
            # Log the error but don't crash the app
            logger.warning(f"⚠ Could not create/verify database tables (expected in production): {type(e).__name__}: {str(e)}")
            logger.warning("  Tables should exist from Supabase migration. If missing, run migrations manually.")
        else:
            # In development, this is a real error
            logger.error(f"✗ Failed to initialize database: {e}", exc_info=True)
            raise

"""
Thredion Engine — Database Migration
Adds video transcription and cognitive structure fields to memories table.

Run this ONCE after deployment:
    python -m alembic upgrade head
    Or manually run these SQL commands in your database.
"""

# ── SQL for PostgreSQL ────────────────────────────────────────

SQL_POSTGRES = """
-- Add video transcription fields
ALTER TABLE memories ADD COLUMN IF NOT EXISTS transcript TEXT DEFAULT '';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS transcript_length INTEGER DEFAULT 0;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS transcript_source VARCHAR(20) DEFAULT 'pending';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS video_duration INTEGER DEFAULT 0;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS is_video BOOLEAN DEFAULT FALSE;

-- Add cognitive structure fields
ALTER TABLE memories ADD COLUMN IF NOT EXISTS cognitive_mode VARCHAR(20) DEFAULT 'learn';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS title_generated VARCHAR(512) DEFAULT '';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS key_points TEXT DEFAULT '[]';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS bucket VARCHAR(100) DEFAULT 'Uncategorized';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS actionability_score FLOAT DEFAULT 0.0;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS emotional_tone VARCHAR(50) DEFAULT '';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 0.0;

-- Add async job tracking fields
ALTER TABLE memories ADD COLUMN IF NOT EXISTS transcription_job_id VARCHAR(100) DEFAULT NULL;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS transcription_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS processing_error TEXT DEFAULT NULL;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP DEFAULT NULL;

-- Create index for job status queries
CREATE INDEX IF NOT EXISTS idx_transcription_job_id ON memories(transcription_job_id);
CREATE INDEX IF NOT EXISTS idx_transcription_status ON memories(transcription_status);
CREATE INDEX IF NOT EXISTS idx_cognitive_mode ON memories(cognitive_mode);
CREATE INDEX IF NOT EXISTS idx_bucket ON memories(bucket);
"""

# ── SQL for SQLite ────────────────────────────────────────

SQL_SQLITE = """
-- SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS
-- So we need to use a workaround

-- Note: SQLite changes are handled automatically by SQLAlchemy
-- Just ensure your db/models.py has the correct field definitions
"""

# ── Helper function to run migrations ────────────────────

def run_migrations(db_url: str):
    """Run migrations based on database type."""
    from sqlalchemy import create_engine, text
    
    engine = create_engine(db_url)
    
    if 'postgresql' in db_url:
        with engine.connect() as conn:
            conn.execute(text(SQL_POSTGRES))
            conn.commit()
        print("✅ PostgreSQL migrations completed")
    elif 'sqlite' in db_url:
        print("✅ SQLite uses SQLAlchemy ORM, migrations handled automatically")
    else:
        print("Unknown database type, skipping migrations")


if __name__ == "__main__":
    from core.config import settings
    run_migrations(settings.DATABASE_URL)

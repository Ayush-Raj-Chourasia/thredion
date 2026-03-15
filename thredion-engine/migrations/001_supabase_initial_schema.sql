-- Supabase PostgreSQL Schema for Thredion Engine
-- Run this in Supabase SQL Editor to set up the database

-- ── Enable Required Extensions ──────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Users Table ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT UNIQUE NOT NULL,
    username TEXT,
    email TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── Memories Table (Core cognitive entries) ──────────────────
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Input metadata
    source TEXT NOT NULL,  -- 'url', 'voice', 'text', 'whatsapp'
    source_url TEXT,
    original_input TEXT NOT NULL,
    
    -- Processing
    cleaned_text TEXT,
    processing_status TEXT DEFAULT 'pending' 
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    
    -- LLM-generated structure
    title TEXT,
    summary TEXT,
    key_points JSONB DEFAULT '[]',
    category TEXT,
    tags JSONB DEFAULT '[]',
    
    -- Scores & confidence
    actionability_score FLOAT DEFAULT 0.0,
    relevance_score FLOAT DEFAULT 0.0,
    confidence_score FLOAT DEFAULT 0.0,
    emotional_tone TEXT,
    
    -- Resurfacing
    resurfaced_count INTEGER DEFAULT 0,
    last_resurfaced_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── Connections Table (Knowledge graph) ──────────────────────
CREATE TABLE IF NOT EXISTS connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_1_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    memory_2_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    
    similarity_score FLOAT NOT NULL,
    connection_type TEXT,  -- 'thematic', 'topic', 'emotional'
    
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT no_self_connections CHECK (memory_1_id != memory_2_id)
);

-- ── Resurfaced Memories Table (Tracking revisits) ────────────
CREATE TABLE IF NOT EXISTS resurfaced_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    
    resurfaced_at TIMESTAMPTZ DEFAULT now(),
    reason TEXT,  -- 'weekly_summary', 'similar_item', 'manual_revisit'
    user_action TEXT,  -- 'viewed', 'archived', 'liked'
    
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ── Indexes (for query performance) ────────────────────────
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(processing_status);
CREATE INDEX IF NOT EXISTS idx_connections_user_id ON connections(user_id);
CREATE INDEX IF NOT EXISTS idx_connections_memory_1 ON connections(memory_1_id);
CREATE INDEX IF NOT EXISTS idx_resurfaced_user_id ON resurfaced_memories(user_id);

-- ── Row Level Security (RLS) ────────────────────────────────
-- Ensure users can only access their own data
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE resurfaced_memories ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read/write their own data only
CREATE POLICY "Users can access own data" ON users
    FOR ALL USING (auth.uid()::text = id::text OR true);  -- Allow service role

CREATE POLICY "Users can access own memories" ON memories
    FOR ALL USING (user_id = auth.uid()::uuid);

CREATE POLICY "Users can access own connections" ON connections
    FOR ALL USING (user_id = auth.uid()::uuid);

CREATE POLICY "Users can access own resurfaced" ON resurfaced_memories
    FOR ALL USING (user_id = auth.uid()::uuid);

-- ── Auto-update updated_at Trigger ─────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

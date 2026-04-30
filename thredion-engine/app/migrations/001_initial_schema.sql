-- Initial Initial Schema for Cognitive Layer
-- Prompt 2 implementation

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table (aligned with bot-first capture)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number TEXT UNIQUE NOT NULL,
    username TEXT,
    email TEXT,
    pending_weekly_summary JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Buckets Table
CREATE TABLE IF NOT EXISTS buckets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    entry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, name)
);

-- 3. Cognitive Entries Table (Main Storage)
CREATE TABLE IF NOT EXISTS cognitive_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    input_type TEXT NOT NULL CHECK (input_type IN ('link', 'voice', 'text')),
    cognitive_mode TEXT NOT NULL CHECK (cognitive_mode IN ('learn', 'think', 'reflect')),
    original_input TEXT NOT NULL,
    source_url TEXT,
    cleaned_text TEXT,
    summary TEXT,
    title TEXT,
    key_points JSONB DEFAULT '[]',
    bucket TEXT,
    tags JSONB DEFAULT '[]',
    actionability_score FLOAT DEFAULT 0.0,
    emotional_tone TEXT,
    confidence_score FLOAT DEFAULT 0.0,
    resurfaced_count INTEGER DEFAULT 0,
    last_resurfaced_at TIMESTAMPTZ,
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_entries_user_id ON cognitive_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_entries_bucket ON cognitive_entries(bucket);
CREATE INDEX IF NOT EXISTS idx_entries_mode ON cognitive_entries(cognitive_mode);
CREATE INDEX IF NOT EXISTS idx_entries_created ON cognitive_entries(created_at);
CREATE INDEX IF NOT EXISTS idx_entries_status ON cognitive_entries(processing_status);

-- Updated_at Trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_cognitive_entries_updated_at
    BEFORE UPDATE ON cognitive_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) - Basic Setup
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE cognitive_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE buckets ENABLE ROW LEVEL SECURITY;

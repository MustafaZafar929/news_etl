-- Enable the vector extension for AI features
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the main table
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,      -- Prevents duplicate articles
    source_domain TEXT NOT NULL,   -- e.g., 'cnn', 'fox'
    title TEXT NOT NULL,
    published_date TIMESTAMP,
    content_summary TEXT,          -- The raw text
    embedding vector(384),         -- Space for the AI vector (added now for future use)
    cluster_id UUID,               -- Space for grouping (added now for future use)
    inserted_at TIMESTAMP DEFAULT NOW()
);

-- Create an index to make sorting by date fast
CREATE INDEX idx_articles_date ON articles(published_date DESC);
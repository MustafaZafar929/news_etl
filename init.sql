-- Enable the vector extension for AI features
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the main table
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link TEXT UNIQUE NOT NULL,     -- Changed from url to link
    source_domain TEXT NOT NULL,   -- e.g., 'cnn', 'fox'
    title TEXT NOT NULL,
    published_date TIMESTAMP,
    content_summary TEXT,          -- The raw text
    embedding vector(384),         -- Space for the AI vector
    cluster_id UUID,               -- Space for grouping
    inserted_at TIMESTAMP DEFAULT NOW()
);

-- Create the summaries table
CREATE TABLE IF NOT EXISTS cluster_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id UUID NOT NULL,
    summary_text TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Create an index to make sorting by date fast
CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(published_date DESC);
-- ==============================================================================
-- VeriWeave — Supabase PostgreSQL + pgvector Cloud Database Setup
-- "Retrieve intelligently. Reason contextually. Respond reliably."
-- ==============================================================================

-- 1. Enable the pgvector extension for dense embedding similarity search
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Primary Vector Store Table (stores 384-dimensional dense vectors)
-- Compatible with all-MiniLM-L6-v2 and Cloudflare bge-small-en-v1.5
CREATE TABLE IF NOT EXISTS veriweave_documents (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(128) UNIQUE NOT NULL,
    doc_id VARCHAR(64) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    page_number INTEGER NOT NULL DEFAULT 1,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    text TEXT NOT NULL,
    char_start INTEGER DEFAULT 0,
    char_end INTEGER DEFAULT 0,
    token_count_estimate INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fast metadata filter indexes
CREATE INDEX IF NOT EXISTS idx_veriweave_doc_id ON veriweave_documents (doc_id);
CREATE INDEX IF NOT EXISTS idx_veriweave_filename ON veriweave_documents (filename);

-- HNSW Vector Index for approximate nearest neighbor cosine search (<=> operator)
CREATE INDEX IF NOT EXISTS idx_veriweave_embedding_hnsw 
ON veriweave_documents 
USING hnsw (embedding vector_cosine_ops);

-- 3. Structured Document Record Table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(64) UNIQUE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(32) NOT NULL,
    file_size_bytes INTEGER DEFAULT 0 NOT NULL,
    page_count INTEGER DEFAULT 1 NOT NULL,
    chunk_count INTEGER DEFAULT 0 NOT NULL,
    status VARCHAR(32) DEFAULT 'indexed' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
);

-- 4. Structured Document Chunks Table
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(128) UNIQUE NOT NULL,
    doc_id VARCHAR(64) REFERENCES documents(doc_id) ON DELETE CASCADE,
    page_number INTEGER DEFAULT 1 NOT NULL,
    chunk_index INTEGER DEFAULT 0 NOT NULL,
    token_count_estimate INTEGER DEFAULT 0 NOT NULL,
    char_start INTEGER DEFAULT 0 NOT NULL,
    char_end INTEGER DEFAULT 0 NOT NULL
);

-- 5. Document Blob Persistence Table (ephemeral cloud container survival)
CREATE TABLE IF NOT EXISTS document_blobs (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(64) UNIQUE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(64) DEFAULT 'application/octet-stream' NOT NULL,
    data BYTEA,
    text_content TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
);

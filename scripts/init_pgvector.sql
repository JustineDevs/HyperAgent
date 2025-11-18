-- Initialize pgvector extension for PostgreSQL
-- This script runs automatically when the postgres container is first created

-- Create extension if not exists
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS hyperagent;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA hyperagent TO hyperagent_user;

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension initialized successfully';
END $$;


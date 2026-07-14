-- Initialize PostgreSQL for SCONIA
-- Enable required extensions

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable vector extension for embeddings (if using pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create additional indexes for performance
-- These will be created by Alembic migrations, but can be added here for initial setup

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE sconia_db TO sconia_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sconia_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sconia_user;

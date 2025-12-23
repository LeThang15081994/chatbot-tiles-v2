-- Switch to correct database
\c gachai_db


-- 1. Create dbo schema
CREATE SCHEMA IF NOT EXISTS dbo
AUTHORIZATION gachai_db;

-- 2. Set dbo as default schema for app user
ALTER ROLE gachai_db
SET search_path = dbo, public;

-- 3. (Recommended) Lock down public schema
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO gachai_db;

-- 4. Create system_logs table
CREATE TABLE dbo.system_logs (
    id BIGSERIAL PRIMARY KEY,
    service_name TEXT NOT NULL,       -- chatbot | image-search | api
    level TEXT NOT NULL CHECK (
        level IN ('INFO', 'WARN', 'ERROR', 'FATAL')
    ),
    message TEXT NOT NULL,
    error_type TEXT,
    stack_trace TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- 5. Indexes
CREATE INDEX idx_system_logs_service
  ON dbo.system_logs(service_name);

CREATE INDEX idx_system_logs_level
  ON dbo.system_logs(level);

CREATE INDEX idx_system_logs_created_at
  ON dbo.system_logs(created_at);

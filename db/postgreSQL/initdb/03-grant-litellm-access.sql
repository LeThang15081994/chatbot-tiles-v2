-- Grant access to litellm database for gachai_db user
-- This allows LiteLLM Router to use the same PostgreSQL instance
\c litellm

-- Grant all privileges on litellm database to gachai_db user
GRANT ALL PRIVILEGES ON DATABASE litellm TO gachai_db;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO gachai_db;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO gachai_db;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO gachai_db;


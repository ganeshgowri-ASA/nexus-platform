<<<<<<< HEAD
-- Initialize NEXUS Database
-- This script is automatically run when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas for modules
CREATE SCHEMA IF NOT EXISTS etl;
CREATE SCHEMA IF NOT EXISTS integration_hub;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA etl TO nexus;
GRANT ALL PRIVILEGES ON SCHEMA integration_hub TO nexus;

-- Create initial users/roles if needed
-- Additional setup can be added here
=======
-- NEXUS Platform Database Initialization Script
-- This script sets up the initial database schema and extensions

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create database if not exists (for reference)
-- This is typically run by Docker entrypoint

-- Set timezone
SET timezone = 'UTC';

-- Create schemas
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA analytics TO nexus;
GRANT ALL PRIVILEGES ON SCHEMA audit TO nexus;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    old_data JSONB,
    new_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit.audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit.audit_log(created_at DESC);

-- Grant permissions on audit table
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO nexus;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA audit TO nexus;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database initialization complete!';
END $$;
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE

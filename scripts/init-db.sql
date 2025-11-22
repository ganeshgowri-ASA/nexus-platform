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

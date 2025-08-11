-- PostgreSQL initialization script for xiaozhi-esp32-server
-- This script will be executed when the PostgreSQL container starts for the first time

-- Create the database (already created by POSTGRES_DB environment variable)
-- CREATE DATABASE xiaozhi_esp32_server;

-- Connect to the database
\c xiaozhi_esp32_server;

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'Asia/Shanghai';

-- Create a comment for the database
COMMENT ON DATABASE xiaozhi_esp32_server IS 'XiaoZhi ESP32 Server Database - PostgreSQL Version';

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE xiaozhi_esp32_server TO postgres;

-- Log initialization completion
SELECT 'PostgreSQL database initialization completed for xiaozhi_esp32_server' as status;
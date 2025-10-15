-- Content Library Table for Music and Stories
-- Author: System
-- Date: 2025-08-29
-- Description: Creates table to store music and story content metadata for the mobile app library

CREATE TABLE content_library (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    romanized VARCHAR(255),
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(10) NOT NULL CHECK (content_type IN ('music', 'story')),
    category VARCHAR(50) NOT NULL,
    alternatives TEXT,
    aws_s3_url VARCHAR(500),
    duration_seconds INT DEFAULT NULL,
    file_size_bytes BIGINT DEFAULT NULL,
    is_active SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_content_type_category ON content_library (content_type, category);
CREATE INDEX idx_title ON content_library (title);
CREATE INDEX idx_active ON content_library (is_active);
CREATE INDEX idx_created_at ON content_library (created_at);

COMMENT ON TABLE content_library IS 'Content library for music and stories available on devices';
COMMENT ON COLUMN content_library.alternatives IS 'JSON array of alternative search terms';
COMMENT ON COLUMN content_library.aws_s3_url IS 'S3 URL for the audio file';
COMMENT ON COLUMN content_library.duration_seconds IS 'Duration in seconds';
COMMENT ON COLUMN content_library.file_size_bytes IS 'File size in bytes';
COMMENT ON COLUMN content_library.is_active IS '1=active, 0=inactive';
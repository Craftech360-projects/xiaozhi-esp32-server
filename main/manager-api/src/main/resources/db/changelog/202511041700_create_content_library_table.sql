-- ============================================================================
-- Migration: Create Content Library Table
-- Date: 2025-11-04 17:00
-- Description: Create table to store music and story content metadata
-- ============================================================================

-- Create content_library table
CREATE TABLE IF NOT EXISTS `content_library` (
  `id` VARCHAR(36) NOT NULL COMMENT 'Primary key (UUID)',
  `title` VARCHAR(255) NOT NULL COMMENT 'Content title',
  `romanized` VARCHAR(255) DEFAULT NULL COMMENT 'Romanized title for non-Latin scripts',
  `filename` VARCHAR(255) NOT NULL COMMENT 'File name',
  `content_type` VARCHAR(50) NOT NULL COMMENT 'Type of content (music or story)',
  `category` VARCHAR(100) DEFAULT NULL COMMENT 'Content category',
  `alternatives` TEXT DEFAULT NULL COMMENT 'Alternative titles/spellings as JSON array',
  `aws_s3_url` VARCHAR(500) DEFAULT NULL COMMENT 'S3 URL for the content file',
  `duration_seconds` INT DEFAULT NULL COMMENT 'Duration in seconds',
  `file_size_bytes` BIGINT DEFAULT NULL COMMENT 'File size in bytes',
  `is_active` TINYINT(1) DEFAULT 1 COMMENT 'Whether content is active',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation timestamp',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
  PRIMARY KEY (`id`),
  KEY `idx_content_type` (`content_type`),
  KEY `idx_category` (`category`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Content library for music and stories';

-- Insert some sample data (optional - remove in production)
INSERT INTO `content_library` (`id`, `title`, `romanized`, `filename`, `content_type`, `category`, `alternatives`, `aws_s3_url`, `duration_seconds`, `file_size_bytes`, `is_active`)
VALUES
  (UUID(), 'Twinkle Twinkle Little Star', 'Twinkle Twinkle Little Star', 'twinkle_twinkle.mp3', 'music', 'Nursery Rhymes', '["Twinkle Star", "Little Star"]', NULL, 120, 2400000, 1),
  (UUID(), 'The ABC Song', 'The ABC Song', 'abc_song.mp3', 'music', 'Educational', '["Alphabet Song", "ABCs"]', NULL, 90, 1800000, 1),
  (UUID(), 'Old MacDonald Had a Farm', 'Old MacDonald Had a Farm', 'old_macdonald.mp3', 'music', 'Nursery Rhymes', '["Old MacDonald", "E-I-E-I-O"]', NULL, 150, 3000000, 1),
  (UUID(), 'The Three Little Pigs', 'The Three Little Pigs', 'three_little_pigs.mp3', 'story', 'Fairy Tales', '["3 Little Pigs", "Three Pigs"]', NULL, 300, 6000000, 1),
  (UUID(), 'Goldilocks and the Three Bears', 'Goldilocks and the Three Bears', 'goldilocks.mp3', 'story', 'Fairy Tales', '["Goldilocks", "Three Bears"]', NULL, 360, 7200000, 1);

-- Verify table creation
SELECT 'content_library table created successfully' AS status;

-- ============================================================================
-- Migration Notes:
-- 1. This table stores metadata for all music and story content
-- 2. The alternatives field stores JSON array of alternative titles
-- 3. is_active flag allows soft deletion of content
-- 4. Indexes optimize common query patterns
-- ============================================================================
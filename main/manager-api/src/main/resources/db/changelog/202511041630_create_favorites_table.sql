-- ============================================================================
-- Migration: Create User Favorites Table
-- Date: 2025-11-04 16:30
-- Description: Create table to store user favorites for music and stories
-- ============================================================================

-- Create user_favorites table
CREATE TABLE IF NOT EXISTS `user_favorites` (
  `id` VARCHAR(36) NOT NULL COMMENT 'Primary key (UUID)',
  `user_id` VARCHAR(36) NOT NULL COMMENT 'User ID from Supabase Auth',
  `content_id` VARCHAR(36) NOT NULL COMMENT 'References content_library.id',
  `content_type` ENUM('music', 'story') NOT NULL COMMENT 'Type of content (music or story)',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When favorite was added',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_content` (`user_id`, `content_id`),
  KEY `idx_user_type` (`user_id`, `content_type`),
  KEY `idx_content_id` (`content_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='User favorites for music and stories';

-- Verify table creation
SELECT 'user_favorites table created successfully' AS status;

-- ============================================================================
-- Migration Notes:
-- 1. Favorites are user-specific (scoped by user_id)
-- 2. Each user can favorite a content item only once (UNIQUE constraint)
-- 3. content_id references content_library.id (no FK constraint to avoid dependency)
-- 4. Separate index for efficient queries by user+type
-- 5. content_type enum ensures only valid types ('music' or 'story')
-- ============================================================================

-- Add default value for textbook_title column
-- This fixes the issue where MyBatis Plus is not including the textbook_title field in INSERT

ALTER TABLE `rag_textbook_metadata` 
MODIFY COLUMN `textbook_title` VARCHAR(255) DEFAULT 'Untitled Textbook' COMMENT 'Complete textbook title';
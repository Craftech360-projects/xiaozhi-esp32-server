-- Add creator column to rag_textbook_metadata table
-- This aligns with the BaseEntity.creator field expected by MyBatis Plus

ALTER TABLE `rag_textbook_metadata` 
ADD COLUMN `creator` BIGINT COMMENT 'User who initiated processing (from BaseEntity)' 
AFTER `created_by`;

-- Update existing records to copy created_by to creator if they exist
UPDATE `rag_textbook_metadata` 
SET `creator` = `created_by` 
WHERE `created_by` IS NOT NULL;
-- Add missing creator column to rag_content_chunks table
-- This column is required by BaseEntity inheritance but was missing from initial table creation

ALTER TABLE `rag_content_chunks` 
ADD COLUMN `creator` BIGINT COMMENT 'User who created the chunk (from BaseEntity)' 
AFTER `updated_at`;

-- Update the column to be consistent with other tables that have this field
-- This maintains compatibility with MyBatis Plus BaseEntity auto-population
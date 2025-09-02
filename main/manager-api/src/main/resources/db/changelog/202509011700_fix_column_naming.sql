-- Fix column naming to match MyBatis Plus conventions
-- MyBatis Plus expects snake_case column names for camelCase Java fields
-- BaseEntity.createDate field should map to create_date column

-- Drop the incorrectly named column
ALTER TABLE `rag_textbook_metadata` 
DROP COLUMN `createDate`;

-- Add the correctly named column
ALTER TABLE `rag_textbook_metadata` 
ADD COLUMN `create_date` DATETIME COMMENT 'Created date from BaseEntity (createDate field maps to create_date column)' 
AFTER `creator`;

-- Copy data from existing created_at column
UPDATE `rag_textbook_metadata` 
SET `create_date` = `created_at` 
WHERE `created_at` IS NOT NULL;
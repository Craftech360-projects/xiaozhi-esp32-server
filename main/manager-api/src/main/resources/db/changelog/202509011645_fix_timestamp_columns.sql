-- Fix timestamp column names to match BaseEntity expectations
-- BaseEntity expects 'createDate' but table has 'created_at' and 'updated_at'

-- Add the expected columns from BaseEntity
ALTER TABLE `rag_textbook_metadata` 
ADD COLUMN `createDate` DATETIME COMMENT 'Created date from BaseEntity (createDate field)' 
AFTER `creator`;

-- Copy data from existing columns
UPDATE `rag_textbook_metadata` 
SET `createDate` = `created_at` 
WHERE `created_at` IS NOT NULL;

-- Note: We keep both column sets for now to avoid breaking other code that might depend on created_at/updated_at
-- The BaseEntity will use createDate column going forward
-- Add missing date columns to rag_content_chunks table
-- The BaseEntity requires create_date and update_date columns for MyBatis Plus auto-population

-- Check if create_date column exists, if not add it
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = DATABASE() 
     AND TABLE_NAME = 'rag_content_chunks' 
     AND COLUMN_NAME = 'create_date') > 0,
    'SELECT "create_date column already exists"',
    'ALTER TABLE rag_content_chunks ADD COLUMN create_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER creator'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check if update_date column exists, if not add it  
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = DATABASE() 
     AND TABLE_NAME = 'rag_content_chunks' 
     AND COLUMN_NAME = 'update_date') > 0,
    'SELECT "update_date column already exists"',
    'ALTER TABLE rag_content_chunks ADD COLUMN update_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER create_date'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Update existing records to have proper create_date values if they were null
UPDATE rag_content_chunks 
SET create_date = created_at, update_date = updated_at 
WHERE create_date IS NULL OR update_date IS NULL;
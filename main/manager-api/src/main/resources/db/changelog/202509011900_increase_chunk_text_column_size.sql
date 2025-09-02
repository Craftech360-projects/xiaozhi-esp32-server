-- Increase chunk_text column size from TEXT to LONGTEXT to handle larger content chunks
-- TEXT can hold up to 65,535 characters (64KB)
-- LONGTEXT can hold up to 4,294,967,295 characters (4GB)

ALTER TABLE `rag_content_chunks` 
MODIFY COLUMN `chunk_text` LONGTEXT NOT NULL COMMENT 'Actual text content of the chunk';
-- Manual migration script to add toy configuration fields
-- Run this directly on the database if Liquibase migration hasn't run

-- Check if columns exist before adding them
ALTER TABLE activated_toys 
ADD COLUMN IF NOT EXISTS toy_name VARCHAR(255) DEFAULT 'Cheeko';

ALTER TABLE activated_toys 
ADD COLUMN IF NOT EXISTS toy_role VARCHAR(255) DEFAULT 'Story Teller';

ALTER TABLE activated_toys 
ADD COLUMN IF NOT EXISTS toy_language VARCHAR(100) DEFAULT 'English';

ALTER TABLE activated_toys 
ADD COLUMN IF NOT EXISTS toy_voice VARCHAR(255) DEFAULT 'Sparkles for Kids';

ALTER TABLE activated_toys 
ADD COLUMN IF NOT EXISTS additional_instructions TEXT;

-- Update any existing records with defaults
UPDATE activated_toys 
SET toy_name = COALESCE(toy_name, 'Cheeko'),
    toy_role = COALESCE(toy_role, 'Story Teller'),
    toy_language = COALESCE(toy_language, 'English'),
    toy_voice = COALESCE(toy_voice, 'Sparkles for Kids')
WHERE toy_name IS NULL 
   OR toy_role IS NULL 
   OR toy_language IS NULL 
   OR toy_voice IS NULL;

-- Fix any records where child_name is null or empty
UPDATE activated_toys 
SET child_name = 'Buddy' 
WHERE child_name IS NULL OR child_name = '';

-- Verify the changes
SELECT column_name, data_type, character_maximum_length, column_default
FROM information_schema.columns
WHERE table_name = 'activated_toys'
ORDER BY ordinal_position;
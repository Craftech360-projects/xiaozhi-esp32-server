-- Manual migration script for Railway MySQL
-- Compatible with MySQL versions that don't support IF NOT EXISTS for columns

-- First, let's check the current structure
SHOW COLUMNS FROM activated_toys;

-- Add toy_name column if it doesn't exist
ALTER TABLE activated_toys 
ADD COLUMN toy_name VARCHAR(255) DEFAULT 'Cheeko';

-- Add toy_role column
ALTER TABLE activated_toys 
ADD COLUMN toy_role VARCHAR(255) DEFAULT 'Story Teller';

-- Add toy_language column
ALTER TABLE activated_toys 
ADD COLUMN toy_language VARCHAR(100) DEFAULT 'English';

-- Add toy_voice column
ALTER TABLE activated_toys 
ADD COLUMN toy_voice VARCHAR(255) DEFAULT 'Sparkles for Kids';

-- Add additional_instructions column
ALTER TABLE activated_toys 
ADD COLUMN additional_instructions TEXT;

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

-- Show the final structure
SHOW COLUMNS FROM activated_toys;
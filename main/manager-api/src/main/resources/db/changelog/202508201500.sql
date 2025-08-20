-- liquibase formatted sql

-- changeset abraham:202508201500-1
-- comment: Add toy configuration fields to activated_toys table

ALTER TABLE activated_toys 
ADD COLUMN IF NOT EXISTS toy_name VARCHAR(255) DEFAULT 'Cheeko',
ADD COLUMN IF NOT EXISTS toy_role VARCHAR(255) DEFAULT 'Story Teller',
ADD COLUMN IF NOT EXISTS toy_language VARCHAR(100) DEFAULT 'English',
ADD COLUMN IF NOT EXISTS toy_voice VARCHAR(255) DEFAULT 'Sparkles for Kids',
ADD COLUMN IF NOT EXISTS additional_instructions TEXT;

-- Update existing records with default values
UPDATE activated_toys 
SET toy_name = 'Cheeko' 
WHERE toy_name IS NULL;

UPDATE activated_toys 
SET toy_role = 'Story Teller' 
WHERE toy_role IS NULL;

UPDATE activated_toys 
SET toy_language = 'English' 
WHERE toy_language IS NULL;

UPDATE activated_toys 
SET toy_voice = 'Sparkles for Kids' 
WHERE toy_voice IS NULL;

-- Fix any existing records where child_name might have been set incorrectly
UPDATE activated_toys 
SET child_name = 'Buddy' 
WHERE child_name IS NULL OR child_name = '';
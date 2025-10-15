-- Create parent_profile table for mobile app user profiles
-- This table stores additional profile information for parents using the mobile app

-- Drop the table if it exists (to clean up from failed migration)
DROP TABLE IF EXISTS parent_profile CASCADE;

-- Create the table
CREATE TABLE parent_profile (
    id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    supabase_user_id VARCHAR(255),
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone_number VARCHAR(50),
    preferred_language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(100) DEFAULT 'UTC',
    notification_preferences JSONB,
    onboarding_completed BOOLEAN DEFAULT false,
    terms_accepted_at TIMESTAMP,
    privacy_policy_accepted_at TIMESTAMP,
    creator BIGINT,
    create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updater BIGINT,
    update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uk_parent_profile_user_id UNIQUE (user_id),
    CONSTRAINT uk_parent_profile_supabase_user_id UNIQUE (supabase_user_id)
);

-- Add foreign key constraint (sys_user table should exist at this point in migrations)
ALTER TABLE parent_profile ADD CONSTRAINT fk_parent_profile_user_id FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE;

-- Create indexes
CREATE INDEX idx_email ON parent_profile(email);
CREATE INDEX idx_phone_number ON parent_profile(phone_number);

COMMENT ON TABLE parent_profile IS 'Parent profile table for mobile app users';
COMMENT ON COLUMN parent_profile.id IS 'Primary key ID';
COMMENT ON COLUMN parent_profile.user_id IS 'Foreign key to sys_user table';
COMMENT ON COLUMN parent_profile.supabase_user_id IS 'Supabase user ID for reference';
COMMENT ON COLUMN parent_profile.full_name IS 'Parent full name';
COMMENT ON COLUMN parent_profile.email IS 'Parent email address';
COMMENT ON COLUMN parent_profile.phone_number IS 'Parent phone number';
COMMENT ON COLUMN parent_profile.preferred_language IS 'Preferred language code (en, es, fr, etc.)';
COMMENT ON COLUMN parent_profile.timezone IS 'User timezone';
COMMENT ON COLUMN parent_profile.notification_preferences IS 'JSON object with notification settings';
COMMENT ON COLUMN parent_profile.onboarding_completed IS 'Whether onboarding is completed';
COMMENT ON COLUMN parent_profile.terms_accepted_at IS 'When terms of service were accepted';
COMMENT ON COLUMN parent_profile.privacy_policy_accepted_at IS 'When privacy policy was accepted';
COMMENT ON COLUMN parent_profile.creator IS 'User who created this record';
COMMENT ON COLUMN parent_profile.create_date IS 'Creation timestamp';
COMMENT ON COLUMN parent_profile.updater IS 'User who last updated this record';
COMMENT ON COLUMN parent_profile.update_date IS 'Last update timestamp';
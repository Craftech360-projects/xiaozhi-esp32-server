-- Create kid_profile table for storing children profiles linked to devices
-- Each user (parent) can have multiple kids, and each device can be assigned to one kid

CREATE TABLE IF NOT EXISTS kid_profile (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  name VARCHAR(100) NOT NULL,
  date_of_birth DATE NOT NULL,
  gender VARCHAR(20) DEFAULT NULL,
  interests TEXT,
  avatar_url VARCHAR(500) DEFAULT NULL,
  creator BIGINT DEFAULT NULL,
  create_date TIMESTAMP DEFAULT NULL,
  updater BIGINT DEFAULT NULL,
  update_date TIMESTAMP DEFAULT NULL,
  CONSTRAINT fk_kid_profile_user FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_kid_profile_user_id ON kid_profile (user_id);

COMMENT ON TABLE kid_profile IS 'Kid profiles table';
COMMENT ON COLUMN kid_profile.id IS 'Primary key';
COMMENT ON COLUMN kid_profile.user_id IS 'FK to sys_user table (parent)';
COMMENT ON COLUMN kid_profile.name IS 'Child name';
COMMENT ON COLUMN kid_profile.date_of_birth IS 'Child date of birth';
COMMENT ON COLUMN kid_profile.gender IS 'Child gender (male/female/other)';
COMMENT ON COLUMN kid_profile.interests IS 'JSON array of child interests';
COMMENT ON COLUMN kid_profile.avatar_url IS 'Avatar URL';
COMMENT ON COLUMN kid_profile.creator IS 'Creator user ID';
COMMENT ON COLUMN kid_profile.create_date IS 'Creation date';
COMMENT ON COLUMN kid_profile.updater IS 'Last updater user ID';
COMMENT ON COLUMN kid_profile.update_date IS 'Last update date';

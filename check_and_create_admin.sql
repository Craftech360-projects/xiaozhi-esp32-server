-- Check if any users exist
SELECT COUNT(*) as user_count FROM sys_user;

-- Check existing users
SELECT id, username, super_admin, status FROM sys_user;

-- Create admin user if no users exist
-- Password: admin123 (BCrypt encoded)
-- You can generate a new BCrypt password using online tools or the Java API
INSERT INTO sys_user (id, username, password, super_admin, status, create_date, creator)
SELECT 
    1,
    'admin',
    '$2a$10$mG.gBdNuCBzJLMZ7LYaiiOoqL1V7rFJFgPcHKxrPKGZxK19lJ5/q6', -- This is BCrypt hash for 'admin123'
    1,
    1,
    NOW(),
    1
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'admin');

-- Verify the admin user was created
SELECT id, username, super_admin, status FROM sys_user WHERE username = 'admin';
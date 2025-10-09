-- Direct SQL Test Setup for Kid Profile
-- This bypasses the API and creates everything directly in the database

-- Step 1: Check existing data
SELECT 'Current Users:' as info;
SELECT id, username, status FROM sys_user LIMIT 5;

SELECT 'Current Devices:' as info;
SELECT id, mac_address, user_id, agent_id, kid_id FROM ai_device WHERE mac_address = '68:25:dd:bb:f3:a0';

SELECT 'Current Kid Profiles:' as info;
SELECT id, user_id, name, date_of_birth, gender FROM kid_profile;

-- Step 2: Create/Update test user (if admin doesn't exist)
-- Password is 'managerpassword' hashed with BCrypt
INSERT INTO sys_user (id, username, password, super_admin, status, creator, create_date, updater, update_date)
VALUES (1, 'admin', '$2a$10$i9M5BuW3YMhXCKxZQjvPfeXHzv.wG7.y0PFPvF5F0.zzLWXz4Y0xG', 1, 1, 1, NOW(), 1, NOW())
ON DUPLICATE KEY UPDATE username=username;

-- Step 3: Create test kid profile for user_id = 1
-- Note: 'id' is the PRIMARY KEY (auto-increment, unique)
-- 'name' is just a field and can be duplicate (multiple kids can have same name)
INSERT INTO kid_profile (
    user_id,
    name,
    date_of_birth,
    gender,
    interests,
    avatar_url,
    creator,
    create_date,
    updater,
    update_date
) VALUES (
    1,  -- admin user
    'Rahul',
    '2014-10-09',  -- 10 years old
    'male',
    '["games", "sports", "science"]',
    'https://example.com/avatar.jpg',
    1,
    NOW(),
    1,
    NOW()
);

-- Get the auto-generated kid_id (this is the unique PRIMARY KEY)
SET @kid_id = LAST_INSERT_ID();
SELECT @kid_id as created_kid_id, 'This is the unique kid profile ID' as note;

-- Step 4: Check if device exists, if not create it
SELECT id INTO @device_exists FROM ai_device WHERE mac_address = '68:25:dd:bb:f3:a0' LIMIT 1;

-- If device doesn't exist, create it
INSERT INTO ai_device (
    id,
    user_id,
    mac_address,
    agent_id,
    last_connected_at,
    creator,
    create_date,
    updater,
    update_date
)
SELECT
    UUID(),
    1,  -- admin user
    '68:25:dd:bb:f3:a0',
    (SELECT id FROM ai_agent LIMIT 1),  -- use first available agent
    NOW(),
    1,
    NOW(),
    1,
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM ai_device WHERE mac_address = '68:25:dd:bb:f3:a0'
);

-- Step 5: Link kid to device
UPDATE ai_device
SET kid_id = @kid_id
WHERE mac_address = '68:25:dd:bb:f3:a0';

-- Step 6: Verify everything
SELECT 'Final Verification:' as info;

SELECT
    d.id as device_id,
    d.mac_address,
    d.user_id,
    d.agent_id,
    d.kid_id,
    k.name as kid_name,
    TIMESTAMPDIFF(YEAR, k.date_of_birth, CURDATE()) as kid_age,
    k.gender,
    k.interests
FROM ai_device d
LEFT JOIN kid_profile k ON d.kid_id = k.id
WHERE d.mac_address = '68:25:dd:bb:f3:a0';

SELECT '✅ Setup Complete! Now test the API endpoint:' as info;
SELECT 'curl -X POST http://localhost:8002/toy/config/child-profile-by-mac -H "Content-Type: application/json" -H "Authorization: Bearer managerpassword" -d \'{"macAddress":"68:25:dd:bb:f3:a0"}\'' as test_command;

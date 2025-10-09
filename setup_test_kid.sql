-- Setup Test Kid Profile and Link to Device
-- Run this in MySQL after running the migrations

-- Step 1: Check if kid_profile table exists and has the column
SHOW TABLES LIKE 'kid_profile';
DESCRIBE kid_profile;

-- Step 2: Check if ai_device has kid_id column
DESCRIBE ai_device;

-- Step 3: Find an existing user (or use user_id = 1 for admin)
SELECT id, username FROM sys_user LIMIT 5;

-- Step 4: Insert test kid profile
-- Replace user_id with actual user ID from step 3
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
    1,  -- user_id (change if needed)
    'Rahul',
    '2014-10-09',  -- 10 years old
    'male',
    '["games", "sports", "science"]',
    'https://example.com/avatar.jpg',
    1,  -- creator
    NOW(),
    1,  -- updater
    NOW()
);

-- Step 5: Get the kid_id we just created
SELECT id, name, date_of_birth, gender FROM kid_profile ORDER BY id DESC LIMIT 1;

-- Step 6: Check if device exists for the MAC address
SELECT id, mac_address, user_id, agent_id, kid_id
FROM ai_device
WHERE mac_address = '68:25:dd:bb:f3:a0';

-- Step 7: Link kid to device
-- If device doesn't exist, you need to create it first
-- Replace <KID_ID> with the ID from Step 5
UPDATE ai_device
SET kid_id = (SELECT id FROM kid_profile WHERE name = 'Rahul' ORDER BY id DESC LIMIT 1)
WHERE mac_address = '68:25:dd:bb:f3:a0';

-- Step 8: Verify the link
SELECT
    d.id as device_id,
    d.mac_address,
    d.kid_id,
    k.name as kid_name,
    k.date_of_birth,
    k.gender,
    k.interests
FROM ai_device d
LEFT JOIN kid_profile k ON d.kid_id = k.id
WHERE d.mac_address = '68:25:dd:bb:f3:a0';

-- Step 9: If device doesn't exist, create one (optional)
-- Uncomment and run if needed:
/*
INSERT INTO ai_device (
    id,
    user_id,
    mac_address,
    agent_id,
    kid_id,
    creator,
    create_date
) VALUES (
    UUID(),
    1,  -- user_id
    '68:25:dd:bb:f3:a0',
    'default-agent-id',  -- replace with actual agent_id
    (SELECT id FROM kid_profile WHERE name = 'Rahul' ORDER BY id DESC LIMIT 1),
    1,
    NOW()
);
*/

-- Manual Railway Data Export Template
-- Please run these commands on your Railway database and save the results

-- Export users
SELECT CONCAT(
    'INSERT INTO sys_user (id, username, password, super_admin, status, create_date, updater, creator, update_date) VALUES (',
    IFNULL(id, 'NULL'), ', ',
    IFNULL(CONCAT('"', username, '"'), 'NULL'), ', ',
    IFNULL(CONCAT('"', password, '"'), 'NULL'), ', ',
    IFNULL(super_admin, 'NULL'), ', ',
    IFNULL(status, 'NULL'), ', ',
    IFNULL(CONCAT('"', create_date, '"'), 'NULL'), ', ',
    IFNULL(updater, 'NULL'), ', ',
    IFNULL(creator, 'NULL'), ', ',
    IFNULL(CONCAT('"', update_date, '"'), 'NULL'),
    ');'
) AS insert_statement
FROM sys_user;

-- Check user count
SELECT COUNT(*) as user_count FROM sys_user;

-- Show user details
SELECT id, username, super_admin, status FROM sys_user;

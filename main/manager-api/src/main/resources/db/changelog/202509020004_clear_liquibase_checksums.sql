-- Clear Liquibase checksums for modified changesets
-- This allows the updated TTS configurations to be applied
-- -------------------------------------------------------

-- Update the checksum for the modified changeset
UPDATE databasechangelog
SET md5sum = NULL
WHERE id = '202509020001' AND author = 'claude';

-- Clear any locks
DELETE FROM databasechangeloglock WHERE id = 1;
INSERT INTO databasechangeloglock (id, locked, lockgranted, lockedby) VALUES (1, false, NULL, NULL);
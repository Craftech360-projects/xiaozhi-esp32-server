-- Clear checksum for the modified TTS configuration changeset
-- This allows the updated changeset with placeholder API keys to be applied
-- -------------------------------------------------------------------------

-- Clear the checksum for the modified changeset 202509020005
UPDATE databasechangelog
SET md5sum = NULL
WHERE id = '202509020005' AND author = 'claude';
-- Change force_update column from SMALLINT to BOOLEAN for PostgreSQL compatibility

-- Step 1: Drop the existing default value
ALTER TABLE ai_ota ALTER COLUMN force_update DROP DEFAULT;

-- Step 2: Convert the column type (0 -> false, any other value -> true)
ALTER TABLE ai_ota ALTER COLUMN force_update TYPE BOOLEAN USING (force_update != 0);

-- Step 3: Set the new default value
ALTER TABLE ai_ota ALTER COLUMN force_update SET DEFAULT FALSE;

-- Step 4: Update comment
COMMENT ON COLUMN ai_ota.force_update IS 'Force update flag: false=No, true=Yes';

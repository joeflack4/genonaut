-- Migration Script: Resolve ID Collisions and Create Shared Sequence
--
-- Purpose: Reassign IDs in content_items partition to avoid collisions with
--          content_items_auto, then create a shared sequence for both partitions.
--
-- Strategy:
--   1. Identify colliding IDs
--   2. Reassign content_items IDs to start from 2000000 (above max auto ID of 1112000)
--   3. Update all foreign key references
--   4. Create shared sequence starting from new max
--
-- IMPORTANT: This script should be run in a transaction and can be rolled back if needed.
--
-- Estimated time: 5-10 minutes (depends on FK update performance)

BEGIN;

-- ============================================================================
-- STEP 1: Create temporary mapping table for old ID -> new ID
-- ============================================================================

CREATE TEMP TABLE content_items_id_mapping (
    old_id INTEGER NOT NULL,
    new_id INTEGER NOT NULL,
    PRIMARY KEY (old_id)
);

-- Populate mapping: only for IDs that collide
-- New IDs start at 2000000 (well above max auto ID of 1112000)
INSERT INTO content_items_id_mapping (old_id, new_id)
SELECT
    ci.id AS old_id,
    2000000 + ROW_NUMBER() OVER (ORDER BY ci.id) - 1 AS new_id
FROM content_items ci
WHERE ci.id IN (
    -- Find all colliding IDs
    SELECT id
    FROM content_items_all
    GROUP BY id
    HAVING COUNT(*) > 1
);

-- Display mapping stats
SELECT
    COUNT(*) AS total_ids_to_reassign,
    MIN(old_id) AS min_old_id,
    MAX(old_id) AS max_old_id,
    MIN(new_id) AS min_new_id,
    MAX(new_id) AS max_new_id
FROM content_items_id_mapping;

-- ============================================================================
-- STEP 2: Disable foreign key constraints (for performance)
-- ============================================================================

-- We'll update FKs manually, so temporarily disable triggers
SET session_replication_role = replica;

-- ============================================================================
-- STEP 3: Update foreign key references in all related tables
-- ============================================================================

-- 3.1: generation_jobs.content_id
UPDATE generation_jobs gj
SET content_id = m.new_id
FROM content_items_id_mapping m
WHERE gj.content_id = m.old_id;

-- 3.2: user_interactions.content_item_id
UPDATE user_interactions ui
SET content_item_id = m.new_id
FROM content_items_id_mapping m
WHERE ui.content_item_id = m.old_id;

-- 3.3: recommendations.content_item_id
UPDATE recommendations r
SET content_item_id = m.new_id
FROM content_items_id_mapping m
WHERE r.content_item_id = m.old_id;

-- 3.4: user_notifications.related_content_id
UPDATE user_notifications un
SET related_content_id = m.new_id
FROM content_items_id_mapping m
WHERE un.related_content_id = m.old_id;

-- 3.5: flagged_content.content_item_id
UPDATE flagged_content fc
SET content_item_id = m.new_id
FROM content_items_id_mapping m
WHERE fc.content_item_id = m.old_id;

-- 3.6: content_items_ext.source_id
UPDATE content_items_ext cie
SET source_id = m.new_id
FROM content_items_id_mapping m
WHERE cie.source_id = m.old_id;

-- ============================================================================
-- STEP 4: Update IDs in content_items table
-- ============================================================================

-- Update the primary key values
UPDATE content_items ci
SET id = m.new_id
FROM content_items_id_mapping m
WHERE ci.id = m.old_id;

-- ============================================================================
-- STEP 5: Re-enable foreign key constraints
-- ============================================================================

SET session_replication_role = DEFAULT;

-- ============================================================================
-- STEP 6: Verify no more collisions
-- ============================================================================

SELECT
    'After reassignment - Colliding IDs' AS check_name,
    COUNT(*) AS collision_count
FROM (
    SELECT id
    FROM content_items_all
    GROUP BY id
    HAVING COUNT(*) > 1
) AS collisions;

-- Should return 0 collisions

-- ============================================================================
-- STEP 7: Find new maximum ID across both partitions
-- ============================================================================

SELECT
    'New max ID across all partitions' AS metric,
    MAX(id) AS value
FROM content_items_all;

-- ============================================================================
-- STEP 8: Create shared sequence for both partitions
-- ============================================================================

-- For IDENTITY columns, we need to:
-- 1. Drop the IDENTITY constraint
-- 2. Create a shared sequence
-- 3. Set DEFAULT to use the shared sequence

-- Drop IDENTITY from content_items
ALTER TABLE content_items
    ALTER COLUMN id DROP IDENTITY IF EXISTS;

-- Drop IDENTITY from content_items_auto
ALTER TABLE content_items_auto
    ALTER COLUMN id DROP IDENTITY IF EXISTS;

-- Create new shared sequence starting above current max
-- Using 3000000 to leave plenty of room for growth
CREATE SEQUENCE content_items_id_seq START WITH 3000000;

-- Grant usage on sequence
GRANT USAGE, SELECT ON SEQUENCE content_items_id_seq TO PUBLIC;

-- Set DEFAULT to use shared sequence for content_items
ALTER TABLE content_items
    ALTER COLUMN id SET DEFAULT nextval('content_items_id_seq');

-- Set DEFAULT to use shared sequence for content_items_auto
ALTER TABLE content_items_auto
    ALTER COLUMN id SET DEFAULT nextval('content_items_id_seq');

-- ============================================================================
-- STEP 9: Final verification
-- ============================================================================

-- Verify sequence is set correctly
SELECT
    tablename,
    pg_get_serial_sequence(tablename::regclass::text, 'id') AS sequence_name
FROM (
    VALUES ('content_items'), ('content_items_auto')
) AS t(tablename);

-- Count records in each partition
SELECT
    'content_items' AS partition,
    COUNT(*) AS record_count
FROM content_items
UNION ALL
SELECT
    'content_items_auto',
    COUNT(*)
FROM content_items_auto
ORDER BY partition;

-- Display sample of reassigned IDs
SELECT
    id,
    title,
    created_at
FROM content_items
ORDER BY id DESC
LIMIT 10;

-- ============================================================================
-- COMMIT or ROLLBACK
-- ============================================================================

-- Review the output above. If everything looks good, the transaction will commit.
-- If you see errors above, the transaction will have been rolled back automatically.

COMMIT;

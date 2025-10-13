-- Benchmark: Tag Query Performance Comparison
-- Comparing JSONB array queries vs junction table queries
-- Database: genonaut_demo
-- Date: 2025-10-13

-- Test tag: '2D' (UUID: 6dbf6875-6752-4aec-bf2d-dc84eee57061)
-- Expected count: 48,078 content items

\timing on

\echo '========================================'
\echo 'Benchmark 1: Single Tag Filter'
\echo '========================================'

\echo ''
\echo 'OLD APPROACH: JSONB Array containment (@>)'
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, created_at
FROM content_items
WHERE tags @> ARRAY['6dbf6875-6752-4aec-bf2d-dc84eee57061'::uuid]
ORDER BY created_at DESC
LIMIT 20;

\echo ''
\echo 'NEW APPROACH: Junction Table JOIN'
EXPLAIN (ANALYZE, BUFFERS)
SELECT ci.id, ci.title, ci.created_at
FROM content_items ci
WHERE ci.id IN (
    SELECT content_id
    FROM content_tags
    WHERE content_source = 'regular'
      AND tag_id = '6dbf6875-6752-4aec-bf2d-dc84eee57061'::uuid
)
ORDER BY ci.created_at DESC
LIMIT 20;

\echo ''
\echo '========================================'
\echo 'Benchmark 2: Multiple Tags (ANY matching)'
\echo '========================================'

\echo ''
\echo 'OLD APPROACH: JSONB Array OR clauses'
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, created_at
FROM content_items
WHERE tags @> ARRAY['6dbf6875-6752-4aec-bf2d-dc84eee57061'::uuid]
   OR tags @> ARRAY['993a844b-b4a5-42ec-a714-4710aaa0bf01'::uuid]
ORDER BY created_at DESC
LIMIT 20;

\echo ''
\echo 'NEW APPROACH: Junction Table with IN'
EXPLAIN (ANALYZE, BUFFERS)
SELECT ci.id, ci.title, ci.created_at
FROM content_items ci
WHERE ci.id IN (
    SELECT content_id
    FROM content_tags
    WHERE content_source = 'regular'
      AND tag_id IN ('6dbf6875-6752-4aec-bf2d-dc84eee57061'::uuid,
                     '993a844b-b4a5-42ec-a714-4710aaa0bf01'::uuid)
)
ORDER BY ci.created_at DESC
LIMIT 20;

\echo ''
\echo '========================================'
\echo 'Benchmark 3: Multiple Tags (ALL matching)'
\echo '========================================'

\echo ''
\echo 'OLD APPROACH: JSONB Array containment with both'
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, created_at
FROM content_items
WHERE tags @> ARRAY['6dbf6875-6752-4aec-bf2d-dc84eee57061'::uuid,
                     '993a844b-b4a5-42ec-a714-4710aaa0bf01'::uuid]
ORDER BY created_at DESC
LIMIT 20;

\echo ''
\echo 'NEW APPROACH: Junction Table with GROUP BY HAVING'
EXPLAIN (ANALYZE, BUFFERS)
SELECT ci.id, ci.title, ci.created_at
FROM content_items ci
WHERE ci.id IN (
    SELECT content_id
    FROM content_tags
    WHERE content_source = 'regular'
      AND tag_id IN ('6dbf6875-6752-4aec-bf2d-dc84eee57061'::uuid,
                     '993a844b-b4a5-42ec-a714-4710aaa0bf01'::uuid)
    GROUP BY content_id
    HAVING COUNT(DISTINCT tag_id) = 2
)
ORDER BY ci.created_at DESC
LIMIT 20;

\echo ''
\echo '========================================'
\echo 'Benchmark 4: Full Gallery Query Simulation'
\echo '========================================'

\echo ''
\echo 'OLD APPROACH: UNION of user + community with JSONB filter'
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM (
    SELECT id, title, created_at, creator_id, 'regular' as source_type
    FROM content_items
    WHERE creator_id = (SELECT id FROM users LIMIT 1)
      AND tags @> ARRAY['6dbf6875-6752-4aec-bf2d-dc84eee57061'::uuid]
    UNION ALL
    SELECT id, title, created_at, creator_id, 'regular' as source_type
    FROM content_items
    WHERE creator_id != (SELECT id FROM users LIMIT 1)
      AND tags @> ARRAY['6dbf6875-6752-4aec-bf2d-dc84eee57061'::uuid]
) combined
ORDER BY created_at DESC
LIMIT 20;

\echo ''
\echo 'NEW APPROACH: Single query with junction table'
EXPLAIN (ANALYZE, BUFFERS)
SELECT ci.id, ci.title, ci.created_at, ci.creator_id, 'regular' as source_type
FROM content_items ci
WHERE ci.id IN (
    SELECT content_id
    FROM content_tags
    WHERE content_source = 'regular'
      AND tag_id = '6dbf6875-6752-4aec-bf2d-dc84eee57061'::uuid
)
ORDER BY ci.created_at DESC
LIMIT 20;

\echo ''
\echo '========================================'
\echo 'Summary'
\echo '========================================'
\echo 'Check execution times and buffer usage above'
\echo 'Junction table should show:'
\echo '- Lower execution time'
\echo '- Index usage on content_tags'
\echo '- Fewer buffer accesses'
\echo '========================================'

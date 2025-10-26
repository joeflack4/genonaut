-- Benchmark: Tag Query Performance with Junction Table
-- Database: genonaut_demo
-- Date: 2025-10-13 (Updated after tags column removal)
--
-- NOTE: The old JSONB array approach has been removed.
-- These queries test the current junction table implementation.
--
-- Test tag: '2D' (UUID: 6dbf6875-6752-4aec-bf2d-dc84eee57061)
-- Expected count: ~48,078 content items

\timing on

\echo '========================================'
\echo 'Benchmark 1: Single Tag Filter'
\echo '========================================'

\echo ''
\echo 'Junction Table JOIN with IN subquery'
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
\echo 'Junction Table with IN (matches ANY tag)'
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
\echo 'Junction Table with GROUP BY HAVING (matches ALL tags)'
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
\echo 'Junction Table query (all content with tag, sorted by date)'
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
\echo 'All queries use the content_tags junction table'
\echo 'Performance targets:'
\echo '  - Single tag query: < 50ms'
\echo '  - Multiple tags (ANY): < 100ms'
\echo '  - Multiple tags (ALL): < 150ms'
\echo '  - Gallery simulation: < 100ms'
\echo ''
\echo 'Verify:'
\echo '  - Index Scan on idx_content_tags_tag_content'
\echo '  - Low buffer reads (< 1000)'
\echo '  - Planning time < 5ms'
\echo '========================================'

# Performance Test Failure Analysis - 2025-10-17

## Reminders
REMINDER: don't use the dev db 'genonaut'. use 'genonaut_demo' and 'genonaut_test'
REMINDER: Don't manually edit migration files

## Executive Summary


Gallery tag filtering queries are taking 7–13 seconds (target: 3s). The main culprits are: (1) tag filtering via 
`EXISTS` against a very large junction table (**content_tags ~88M rows**), (2) late sorting with `OFFSET/LIMIT`, and 
(3) duplicated work across source tables before unioning. We will prioritize **cursor (keyset) pagination** and a 
**partitioned parent table** to eliminate `OFFSET` costs and manual unions, then layer **pre-JOIN tag filtering** and 
**focused index cleanup**. Redis caching remains a quick win but will be added after measuring uncached performance.

## Test Failures Overview

Four performance tests failed with the following timings:

1. **test_canonical_tag_query_performance (integration)**: 13.15s (target: 3s)
2. **test_tag_query_with_multiple_tags (integration)**: 9.35s (target: 3s)
3. **test_canonical_tag_query_performance (performance)**: 7.91s (target: 3s)
4. **test_measure_query_performance_detailed (performance)**: 7.37s average (target: 3s)

All failures involve tag filtering on the unified content endpoint with these parameters:
- Tag filter: anime tag (UUID: dfbb88fc-3c31-468f-a2d7-99605206c985)
- All 4 content source types selected (user-regular, user-auto, community-regular, community-auto)
- User ID filter
- Sort by created_at DESC
- Page 1, page_size 25

## Database Statistics

Critical metrics from the demo database:

| Table | Row Count | Notes |
|-------|-----------|-------|
| content_tags | 88,146,610 | Junction table - MASSIVE |
| content_items_auto | 1,104,089 | Auto-generated content |
| content_items | 65,204 | User-created content |
| Anime tag matches | 870,885 | ~1% of junction table |

The content_tags junction table COUNT(*) query alone takes **11.4 seconds**.

## Root Cause Analysis

### 1. Inefficient Query Pattern

The current implementation (genonaut/api/services/content_service.py:96-148) uses EXISTS subqueries for tag filtering:

```python
# For "any" matching: content must have AT LEAST ONE of the specified tags
exists_clause = self.db.query(ContentTag.content_id).filter(
    ContentTag.content_id == content_model.id,
    ContentTag.content_source == content_source,
    ContentTag.tag_id.in_(unique_tags)
).exists()
return query.filter(exists_clause)
```

This approach requires:
- 4 separate UNION queries (one per content source type) (update: now should be 2 union queries: content_items (user 
  data + community data) & content_items_auto (user data + community data))
- Each with an EXISTS subquery scanning the 88M row junction table
- Then sorting the combined result set
- Finally applying LIMIT/OFFSET for pagination

### 2. Massive Junction Table

With 88+ million rows in content_tags:
- Average ~75 tags per content item (88M / 1.17M total items)
- Index scans are still slow due to sheer volume
- EXISTS clause evaluated for each row in the result set before UNION

### 3. UNION Before Filtering

The query architecture:
1. Builds 4 separate queries (user-regular, user-auto, community-regular, community-auto)
2. Applies EXISTS tag filter to each
3. UNIONs them together
4. Creates subquery to allow ordering
5. Applies ORDER BY
6. Applies LIMIT/OFFSET

This means tag filtering happens 4 times, once per query before UNION.

### 4. No Query Result Caching

Identical queries (same tag, same user, same filters) are re-executed from scratch every time with no caching layer.

### 5. Suboptimal Index Usage

Current indexes on content_tags:
- Primary key: (content_id, content_source, tag_id)
- idx_content_tags_tag_content: (tag_id, content_id)
- idx_content_tags_content: (content_id, content_source)

The idx_content_tags_tag_content index should help, but with 870K+ matching rows for the anime tag, index scans are still expensive.

## Performance Optimization Proposals

### Proposal 1: Materialized Views for Popular Tags - (no; maybe later)

Create materialized views for frequently accessed tag combinations.

**Benefits:**
- Pre-computed results for common queries
- Eliminates EXISTS subquery overhead
- Can be refreshed periodically (e.g., every 5 minutes)
- Dramatic speedup for popular tags

**Drawbacks:**
- Slight data staleness (acceptable for gallery browsing)
- Storage overhead for materialized views
- Requires refresh strategy

**Implementation Checklist:**
- [ ] Identify top 10-20 most queried tags from application logs
- [ ] Create materialized view schema for tag-filtered content
- [ ] Add CONCURRENTLY refresh support for zero-downtime updates
- [ ] Implement background refresh job (Celery task every 5 min)
- [ ] Update content_service to check materialized views first
- [ ] Add fallback to regular query for uncached tags
- [ ] Monitor materialized view storage usage
- [ ] Add indexes on materialized views for user_id filtering
- [ ] Add tests for materialized view freshness
- [ ] Document refresh strategy and cache hit rates

---

### Proposal 2: Query Result Caching (Redis) - (yes, but last)

**Note**: This is implemented LAST to measure uncached query performance improvements first.

Cache query results for common filter combinations in Redis.

**Benefits:**
- Fastest possible response for cached queries (< 100ms)
- Works for any tag, not just popular ones
- Reduces database load significantly
- Easy to implement with existing Redis infrastructure

**Drawbacks:**
- Cache invalidation complexity
- Memory overhead in Redis
- Potential stale data if invalidation strategy is wrong

**Implementation Checklist:**

**Phase 2.1: Cache Key Design**
- [ ] Design cache key structure (sorted tags + user + filters + sort)
- [ ] Implement canonicalization function (consistent key generation)
- [ ] Add versioning to cache keys (for schema changes)
- [ ] Handle edge cases (empty tags, null filters)

**Phase 2.2: Cache Layer Implementation**
- [ ] Add cache check at start of `get_unified_content_paginated`
- [ ] Serialize/deserialize response objects (JSON or MessagePack)
- [ ] Set TTL (5-10 minutes recommended, configurable)
- [ ] Add cache write on successful query
- [ ] Handle Redis connection errors gracefully (fall through to DB)

**Phase 2.3: Cache Invalidation**
- [ ] Add cache invalidation on content creation
- [ ] Add cache invalidation on content update (tags changed)
- [ ] Add cache invalidation on content deletion
- [ ] Implement pattern-based invalidation (e.g., all queries with tag X)
- [ ] Add manual cache clear endpoint (admin only)

**Phase 2.4: Cache Bypass & Warming**
- [ ] Add `cache_bypass` flag to API endpoint (for real-time needs)
- [ ] Implement cache warming for popular tag combinations
- [ ] Create Celery task to prewarm cache (optional)
- [ ] Add cache refresh strategy (update stale entries in background)

**Phase 2.5: Monitoring & Metrics**
- [ ] Add cache hit/miss logging
- [ ] Track cache hit rate percentage
- [ ] Monitor Redis memory usage
- [ ] Add metrics for cache invalidation frequency
- [ ] Create dashboard or logging for cache performance

**Phase 2.6: Backend Testing**
- [ ] Unit test: cache key generation and canonicalization
- [ ] Unit test: serialization/deserialization
- [ ] Integration test: cache hit returns correct data
- [ ] Integration test: cache miss queries database
- [ ] Integration test: cache invalidation on content changes
- [ ] Integration test: cache bypass flag works
- [ ] Verify `make test` passes

**Phase 2.7: Performance Verification**
- [ ] Measure cached query response time (target: < 100ms)
- [ ] Measure uncached query response time (should match non-cached improvements)
- [ ] Test cache hit rate with realistic traffic patterns
- [ ] Verify cache doesn't impact write performance
- [ ] Document performance improvements (cached vs uncached)

**Phase 2.8: Documentation**
- [ ] Document caching strategy in `docs/api.md` or `docs/performance.md`
- [ ] Document cache key format and invalidation rules
- [ ] Add configuration examples (TTL, cache size limits)
- [ ] Document cache warming strategy
- [ ] Update `README.md` with caching features
- [ ] Run full test suite: `make test-all`

---

### Proposal 3: Denormalized Tag Array Column - (no)

Add a tag_ids UUID[] column to content_items and content_items_auto tables.

**Benefits:**
- Eliminates JOIN with junction table
- Can use PostgreSQL array operators (@> for contains)
- GIN index on tag_ids[] for fast lookups
- Simpler query structure

**Drawbacks:**
- Data duplication (tags in both junction table and content tables)
- Requires migration for existing data
- Increased storage per content row
- Sync complexity between array column and junction table

**Implementation Checklist:**
- [ ] Add tag_ids UUID[] column to content_items (nullable initially)
- [ ] Add tag_ids UUID[] column to content_items_auto (nullable initially)
- [ ] Create GIN index on content_items.tag_ids
- [ ] Create GIN index on content_items_auto.tag_ids
- [ ] Write data migration to populate tag_ids from junction table
- [ ] Run migration on demo database and measure performance
- [ ] Update ContentService.create_content to populate tag_ids
- [ ] Update ContentService.update_content to sync tag_ids
- [ ] Add database triggers to keep tag_ids in sync with junction table
- [ ] Update _apply_tag_filter to use array operators instead of EXISTS
- [ ] Run performance tests comparing new approach
- [ ] Make tag_ids NOT NULL after migration complete
- [ ] Update tests to verify tag_ids sync
- [ ] Document sync strategy and trade-offs

---

### Proposal 4: Optimized Index Strategy (yes; consolidated with Proposal 5)

**Note**: Many of these index optimizations are covered in Proposal 5 (Pre-JOIN Tag Filtering) and Proposal 11
(Partitioned Parent Table). This section consolidates any remaining index work not covered elsewhere.

Create composite indexes optimized for the exact query patterns.

**Benefits:**
- No schema changes required
- Can improve performance immediately
- Works with existing query structure
- Low risk

**Drawbacks:**
- Limited gains with 88M row table alone
- Index size overhead
- May not reach 3s target without other optimizations

**Implementation Checklist:**

**Phase 4.1: Baseline Analysis**
- [ ] Run EXPLAIN (ANALYZE, BUFFERS) on current slow queries
- [ ] Document current index usage and query plans
- [ ] Identify missing indexes from query analysis
- [ ] Check existing index sizes and bloat

**Phase 4.2: Index Creation (if not covered in Proposals 5/11)**
- [ ] Verify all indexes from Proposal 5 are created
- [ ] Verify all indexes from Proposal 11 are created
- [ ] Create any additional composite indexes identified
- [ ] Run VACUUM ANALYZE on all affected tables

**Phase 4.3: Index Cleanup**
- [ ] Identify redundant indexes (overlapping coverage)
- [ ] Remove redundant indexes to save space and maintenance overhead
- [ ] Monitor index bloat and schedule maintenance
- [ ] Document index maintenance strategy

**Phase 4.4: Performance Verification**
- [ ] Run EXPLAIN (ANALYZE, BUFFERS) on queries post-indexing
- [ ] Measure query performance improvements
- [ ] Document index sizes vs performance gains
- [ ] Verify index-only scans where possible

**Phase 4.5: Documentation**
- [ ] Add index strategy to `docs/db.md`
- [ ] Document index maintenance procedures
- [ ] Add monitoring queries for index bloat
- [ ] Update `README.md` if maintenance tasks changed

### Proposal 5: Pre-JOIN Tag Filtering (yes)

#### Summary
Move tag filtering **into the junction table first** and only then JOIN to `content_items` / `content_items_auto`. This 
shrinks intermediate sets and lets indexes do the heavy lifting. Pair this with Redis L1 caching and keyset (cursor) 
pagination for stable latency. Add a runtime heuristic (codified in Python) to pick the best AND-strategy per query.

#### Benefits
- Smaller intermediate result sets before touching wide content rows
- Better use of indexes (tag-first scans)
- No schema changes
- Plays well with Redis caching and later MVs (optional)

#### Drawbacks
- More complex query composition (AND across many tags)
- UNION and cursor pagination need careful handling
- Requires stats + a small planner to choose strategies

#### Required Indexes
Junction (`content_tags`):
```sql
-- PK you already have
-- PRIMARY KEY (content_id, content_source, tag_id);

-- Tag-first covering; include content_source iff you filter by it often
CREATE INDEX IF NOT EXISTS idx_content_tags_tag_src_content
ON content_tags (tag_id, content_source, content_id);

-- For reverse lookups / deletes by content
CREATE INDEX IF NOT EXISTS idx_content_tags_content_src
ON content_tags (content_id, content_source);
```

Content tables:
```sql
-- For keyset pagination and stable ordering
CREATE INDEX IF NOT EXISTS idx_content_items_sort ON content_items (created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_content_items_auto_sort ON content_items_auto (created_at DESC, id DESC);
```

#### Query Patterns (AND semantics)

> “Match all tags” = return content that has **every** tag in the user’s filter.

##### A) K ≤ 3 (very small): Self-joins (fastest)
```sql
SELECT c1.content_id
FROM content_tags c1
JOIN content_tags c2 USING (content_id)
JOIN content_tags c3 USING (content_id)
WHERE c1.tag_id = $a AND c2.tag_id = $b AND c3.tag_id = $c
  AND c1.content_source = $src AND c2.content_source = $src AND c3.content_source = $src;
```

##### B) 4 ≤ K ≤ medium_threshold: Group/HAVING
```sql
SELECT ct.content_id
FROM content_tags ct
WHERE ct.tag_id = ANY($tags) AND ct.content_source = $src
GROUP BY ct.content_id
HAVING COUNT(DISTINCT ct.tag_id) = cardinality($tags);
```

##### C) Large/Variable K or Skewed Popular Tags: Two-phase (rarest-first)
```sql
WITH seed AS (
  SELECT ct.content_id
  FROM content_tags ct
  WHERE ct.tag_id = $rarest AND ct.content_source = $src
  ORDER BY ct.content_id
  LIMIT :seed_candidate_cap  -- tune
),
matched AS (
  SELECT ct.content_id
  FROM content_tags ct
  JOIN seed s USING (content_id)
  WHERE ct.tag_id = ANY($tags) AND ct.content_source = $src
  GROUP BY ct.content_id
  HAVING COUNT(DISTINCT ct.tag_id) = cardinality($tags)
)
SELECT ci.*
FROM content_items ci
JOIN matched m ON m.content_id = ci.id
ORDER BY ci.created_at DESC, ci.id DESC
LIMIT :limit;
```
> Optionally seed with **two** rarest tags when the rarest alone is still too common.

**Why two-phase?** It caps the candidate set early using the rarest tag(s). This protects the Group/HAVING step from exploding on common tags.

#### UNION + Keyset Pagination
When unifying `content_items` and `content_items_auto`:
```sql
WITH filtered AS ( /* produce (id, created_at, src) from each table, AND-filtered */ )
SELECT *
FROM filtered
WHERE (created_at, id) < (:cursor_ts, :cursor_id)  -- omit on first page
ORDER BY created_at DESC, id DESC
LIMIT :limit;
```
Use a base64 cursor encoding of `{ts, id, src}`. Reset the cursor when filters/sort change. Keep a backstack for “prev” navigation.

#### Heuristic Planner (Runtime) 
Pick the strategy per request in the API layer (Python) using maintained tag statistics.

**Inputs**
- `K = len(tags)`
- `card(tag_i)` = recent distinct `content_id` count for each tag (from a stats table or HyperLogLog sketches)
- `rarest_count = min(card(tag_i))` after sorting by rarity

**Decision**
1. If `K ≤ cfg.small_k_threshold` → **Self-join**.
2. Else if `rarest_count ≤ cfg.group_having_rarest_ceiling` → **Group/HAVING**.
3. Else → **Two-phase (rarest-first)**, optionally with 2-tag seed if `rarest_count > cfg.two_phase_dual_seed_floor`.
4. Always fall back to **Group/HAVING** if the seed would exceed `cfg.seed_candidate_cap` too often (protects memory/temp I/O).

**Pseudo-code**
```python
def pick_strategy(tags, stats, cfg):
    K = len(tags)
    rarest_first = sorted(tags, key=lambda t: stats.cardinality(t))
    rarest = rarest_first[0]
    rarest_count = stats.cardinality(rarest)

    if K <= cfg.small_k_threshold:
        return "self_join"

    if rarest_count <= cfg.group_having_rarest_ceiling:
        return "group_having"

    if rarest_count > cfg.two_phase_dual_seed_floor and K >= cfg.two_phase_min_k_for_dual_seed:
        return "two_phase_dual_seed"
    return "two_phase_single_seed"
```
Emit the selected strategy + estimates into logs for tuning.


#### Configuration Knobs (`config/base.json`)
Add a section so you can tune without redeploying logic:

```json
{
  "performance": {
    "query_planner_tag_prejoin_for_content_queries": {
      "small_k_threshold": 3,
      "group_having_rarest_ceiling": 50000,
      "two_phase_min_k_for_dual_seed": 7,
      "two_phase_dual_seed_floor": 150000,
      "seed_candidate_cap": 50000,
      "max_work_mem_mb": 256,
      "enable_two_phase": true,
      "enable_group_having": true,
      "enable_self_join": true,
      "stats": {
        "source": "table",                 // table | redis | hybrid
        "table_name": "tag_cardinality_stats",
        "freshness_seconds": 3600,
        "fallback_default_count": 1000000  // used if a tag has no stats
      },
      "telemetry": {
        "log_strategy_choice": true,
        "log_estimates": true,
        "sample_rate": 0.1
      }
    }    
  }
}
```

**Notes**
- `group_having_rarest_ceiling`: if the rarest tag is already selective enough, the simple Group/HAVING is fine.
- `seed_candidate_cap`: hard stop on seed set size to avoid big temp sorts/joins.
- `two_phase_dual_seed_floor`: when even the rarest is very common, seed with two rarest tags.
- Stats can be maintained via nightly jobs, or incrementally with Redis counters/HLLs.

#### API Integration (SQLAlchemy outline)
- Build a normalized **query signature** (sorted tags, user scope, sort) for Redis caching keys.
- Choose strategy via the heuristic above.
- Render SQL templated per strategy and bind params.
- Use keyset pagination; store `nextCursor` alongside results for the client.
- Cache the first page in Redis with TTL (5–10m). Prewarm heavy hitters.

#### Telemetry & Benchmarks
Track:
- Chosen strategy, K, rarest_count, estimated candidates
- P50/P95 latency, rows scanned, temp bytes
- Cache hits/misses, nextCursor utilization

Not for current phase of implementation: Periodically export `EXPLAIN (ANALYZE, BUFFERS)` samples to validate thresholds, then adjust `config/base.json` knobs.

#### Tests
- Unit: strategy selection for a matrix of (K, rarest_count)
- SQL correctness for each strategy (K=1..10; mixed sources)
- Pagination continuity (no gaps/dupes) across deletes/updates
- Load tests with skewed/common tags and random combinations

#### Future: Optional Materialized Views
If a tiny set of tags/pairs dominate over time, introduce MVs for those heavy-hitters to make cache misses cheap. Keep Redis as L1 either way.

#### 🧭 Pre-JOIN Tag Filtering — Implementation Checklist

**Phase 5.1: Index Setup**
- [ ] Create index: `idx_content_tags_tag_src_content` ON content_tags (tag_id, content_source, content_id)
- [ ] Create index: `idx_content_tags_content_src` ON content_tags (content_id, content_source)
- [ ] Verify indexes exist on content tables for pagination (created_at DESC, id DESC)
- [ ] Run VACUUM ANALYZE on content_tags
- [ ] Test index usage with EXPLAIN on sample queries

**Phase 5.2: Tag Cardinality Stats Infrastructure**
- [ ] Create `tag_cardinality_stats` table (tag_id, content_source, cardinality, updated_at)
- [ ] Add indexes on (tag_id, content_source)
- [ ] Write query to populate stats from content_tags
- [ ] Create Celery task to refresh stats (hourly or nightly)
- [ ] Add fallback logic for missing stats (use configurable default)

**Phase 5.3: Configuration Setup**
- [ ] Add `query_planner_tag_prejoin_for_content_queries` section to `config/base.json`
- [ ] Define thresholds: `small_k_threshold`, `group_having_rarest_ceiling`, etc.
- [ ] Add stats source config (table | redis | hybrid)
- [ ] Add telemetry config (logging, sampling rate)
- [ ] Load config in application startup

**Phase 5.4: Strategy Selector (Heuristic Planner)**
- [ ] Implement `pick_strategy()` function in Python
- [ ] Accept inputs: tags list, stats service, config
- [ ] Return strategy name: "self_join" | "group_having" | "two_phase_single" | "two_phase_dual"
- [ ] Add logging for strategy choice and estimates
- [ ] Unit test with various (K, rarest_count) combinations

**Phase 5.5: Core Query Strategies - Self-Join (K ≤ 3)**
- [ ] Implement self-join SQL generation for K=1, K=2, K=3
- [ ] Build SQLAlchemy query dynamically based on tag count
- [ ] Add WHERE clauses: c1.tag_id = $a AND c2.tag_id = $b, etc.
- [ ] Ensure content_source filter applied to all self-joins
- [ ] Unit test: correctness for K=1, K=2, K=3

**Phase 5.6: Core Query Strategies - Group/HAVING**
- [ ] Implement group/HAVING SQL for medium K (4 ≤ K ≤ ceiling)
- [ ] Use `WHERE ct.tag_id = ANY($tags)` for filtering
- [ ] Add `GROUP BY ct.content_id`
- [ ] Add `HAVING COUNT(DISTINCT ct.tag_id) = cardinality($tags)`
- [ ] Unit test: correctness for K=4, K=7, K=10

**Phase 5.7: Core Query Strategies - Two-Phase (Rarest-First)**
- [ ] Implement rarest-tag seed CTE
- [ ] Implement matched CTE with GROUP/HAVING over seed
- [ ] Add support for dual-seed (two rarest tags) when needed
- [ ] Add `seed_candidate_cap` limit
- [ ] Unit test: correctness for large K, very common tags

**Phase 5.8: Query Integration with Content Service**
- [ ] Update `_apply_tag_filter` method to use strategy selector
- [ ] Generate SQL based on chosen strategy
- [ ] Integrate with existing UNION logic (or partitioned parent if available)
- [ ] Ensure works with cursor pagination
- [ ] Add structured logging for query execution

**Phase 5.9: Backend Testing**
- [ ] Unit test: strategy selector logic for edge cases
- [ ] Unit test: SQL generation for each strategy (K=1..15)
- [ ] Integration test: query correctness across all strategies
- [ ] Integration test: mixed sources (items vs auto)
- [ ] Integration test: pagination continuity (no gaps/dupes)
- [ ] Integration test: verify stats table usage
- [ ] Verify `make test` passes

**Phase 5.10: Performance Testing**
- [ ] Benchmark self-join vs old EXISTS for K ≤ 3
- [ ] Benchmark group/HAVING vs old EXISTS for medium K
- [ ] Benchmark two-phase vs old EXISTS for large K
- [ ] Test with popular tags (anime: 870K+ matches)
- [ ] Test with rare tags (< 100 matches)
- [ ] Document performance improvements

**Phase 5.11: Telemetry & Monitoring**
- [ ] Add structured logging: strategy, K, rarest_count, estimated candidates
- [ ] Log P50/P95 query latency
- [ ] Track rows scanned, temp space used
- [ ] Add sampling (e.g., 10% of queries)
- [ ] Create dashboard or log queries for later analysis

**Phase 5.12: Documentation**
- [ ] Document strategy selection logic in `docs/db.md` or `docs/performance.md`
- [ ] Add configuration examples to docs
- [ ] Document index requirements
- [ ] Add EXPLAIN examples for each strategy
- [ ] Update `README.md` if query patterns changed
- [ ] Run full test suite: `make test-all`

### Proposal 6: Pagination Cursor Optimization (yes)

Implement cursor-based pagination specifically for tag-filtered queries.

**Benefits:**
- Eliminates OFFSET overhead
- Faster subsequent page loads
- More consistent performance across pages
- Works well with large result sets

**Drawbacks:**
- Can't jump to arbitrary pages
- Complex cursor encoding for multi-table UNION
  - Note: This is addressed by utilizing: "Proposal 11: Partitioned Parent Table — `content_items_all`" 
- Requires UI changes for cursor-based navigation

**Implementation Checklist:**

**Phase 6.1: Design & Backend Core**
- [x] Design cursor format for unified queries (encode: created_at, id, source_type)
- [x] Add cursor parameter to `get_unified_content` endpoint schema (Pydantic models) - Already exists in PaginationRequest
- [x] Implement cursor encoding function (base64 of JSON with created_at, id, source_type)
- [x] Implement cursor decoding function with validation
- [x] Add cursor validation and error handling (invalid format, expired cursors)

**Phase 6.2: Query Implementation**
- [x] Replace OFFSET with WHERE (created_at, id) < cursor for each subquery
- [x] Ensure cursor works correctly with DESC ordering
- [x] Handle edge cases (deleted items, updated timestamps, gaps in data)
- [x] Test cursor stability across tag filter changes

**Phase 6.3: Backend Testing**
- [x] Unit test: cursor encoding/decoding
- [x] Unit test: cursor validation (invalid formats, edge cases)
- [x] Integration test: pagination continuity (no gaps/duplicates) - Already exists in test_cursor_pagination.py
- [x] Integration test: cursor across different tag filters - Already exists in test_cursor_pagination.py
- [x] Integration test: cursor with deleted/updated items - Already exists in test_cursor_pagination.py
- [x] Verify `make test` passes - 1071 passed, 78 skipped

**Phase 6.4: Frontend Updates**
- [x] Update API client to accept/return cursor parameters
- [x] Update gallery page to use cursor pagination (next/prev buttons)
- [x] Handle cursor in URL query params for bookmarking
- [x] Add loading states for cursor-based navigation (inherited from existing pagination)
- [x] Test frontend pagination flow

**Phase 6.5: Frontend Testing**
- [ ] E2E test: navigate through pages using cursors (deferred - optional enhancement)
- [ ] E2E test: verify no duplicate items across pages (deferred - optional enhancement)
- [ ] E2E test: verify bookmarking with cursor works (deferred - optional enhancement)
- [x] Verify `make frontend-test` passes - 337 passed, 5 skipped
- [x] Verify `make test` passes - 1071 passed, 78 skipped

**Phase 6.6: Documentation & Cleanup**
- [x] Document cursor implementation in performance report
- [ ] Document cursor format in API docs (`docs/api.md`) (optional - defer to end)
- [ ] Add cursor examples to API documentation (optional - defer to end)
- [ ] Update `README.md` if pagination behavior changed (no user-facing changes)
- [ ] Add comments in code explaining cursor format
- [x] Run full test suite: `make test-all` and `make frontend-test`

### Proposal 7: Read Replicas for Tag Queries (no)

Route tag-filtered gallery queries to dedicated read replicas.

**Benefits:**
- Offloads expensive queries from primary database
- Can scale horizontally with more replicas
- Reduces contention on primary for writes
- Production-ready scaling strategy

**Drawbacks:**
- Infrastructure complexity
- Replication lag (slight data staleness)
- Requires connection pooling updates
- Cost of additional database instances

**Implementation Checklist:**
- [ ] Set up PostgreSQL read replica
- [ ] Configure streaming replication
- [ ] Update database connection pool to support read/write split
- [ ] Route get_unified_content queries to read replica
- [ ] Monitor replication lag
- [ ] Add fallback to primary if replica unavailable
- [ ] Test performance improvement with replica
- [ ] Document read replica setup and configuration
- [ ] Add replica health checks
- [ ] Update deployment documentation

### Proposal 8: Tag Facet Aggregation Table (yes)

**Note**: This is partially covered by Proposal 5's `tag_cardinality_stats` table. This expands it for UI/faceting needs.

Create aggregation tables for tag popularity and content counts.

**Benefits:**
- Fast tag popularity queries for UI
- Can pre-filter unpopular tags
- Helps with faceted search UI
- Reduces load for count queries
- Supports "popular tags" features

**Drawbacks:**
- Requires periodic updates
- Doesn't solve core filtering performance (but supports Proposal 5)
- Additional storage overhead (minimal)

**Implementation Checklist:**

**Phase 8.1: Table Schema**
- [ ] Review `tag_cardinality_stats` from Proposal 5 (may already exist)
- [ ] Extend table if needed: add display_count, last_updated fields
- [ ] Add indexes on (tag_id), (content_source), and composite
- [ ] Add indexes on (cardinality DESC) for popularity queries

**Phase 8.2: Aggregation Logic**
- [ ] Write query to compute tag counts from content_tags
- [ ] Add query to compute per-source counts (items vs auto)
- [ ] Handle edge cases (tags with no content, deleted tags)
- [ ] Test aggregation query performance

**Phase 8.3: Celery Background Job**
- [ ] Create Celery task: `refresh_tag_cardinality_stats`
- [ ] Schedule task (hourly or nightly based on update frequency needs)
- [ ] Add error handling and logging
- [ ] Add monitoring for job duration and success rate

**Phase 8.4: API Endpoints**
- [ ] Add GET /api/v1/tags/popular endpoint (top N tags by count)
- [ ] Add tag counts to existing tag list endpoints
- [ ] Add filtering by min/max count
- [ ] Return counts in tag search results

**Phase 8.5: Frontend Integration**
- [ ] Update tag selector to show counts next to tag names
- [ ] Add "popular tags" section to UI
- [ ] Sort tags by popularity in dropdowns
- [ ] Show tag distribution visualizations (if applicable)

**Phase 8.6: Testing**
- [ ] Unit test: aggregation query correctness
- [ ] Integration test: Celery task execution
- [ ] API test: popular tags endpoint
- [ ] E2E test: tag selector shows counts correctly
- [ ] Verify `make test` and `make frontend-test` pass

**Phase 8.7: Documentation**
- [ ] Document aggregation strategy in `docs/db.md`
- [ ] Document Celery task schedule
- [ ] Add API endpoint docs for popular tags
- [ ] Update `README.md` with new features
- [ ] Run full test suite: `make test-all` and `make frontend-test`

### Proposal 9: Database Partitioning for content_tags (no; not now)

Partition content_tags table by content_source or tag_id ranges.

**Benefits:**
- Parallel query execution across partitions
- Smaller index sizes per partition
- Faster maintenance operations (VACUUM, etc.)
- Better query planner optimization

**Drawbacks:**
- Complex migration for existing 88M rows
- Partition key selection is critical
- Some query patterns may not benefit
- PostgreSQL version requirements

**Implementation Checklist:**
- [ ] Analyze query patterns to choose partition key (content_source recommended)
- [ ] Design partition strategy (2 partitions: regular, auto)
- [ ] Create new partitioned table structure
- [ ] Write migration to move data to partitioned table
- [ ] Test migration on copy of demo database
- [ ] Update indexes for partitioned structure
- [ ] Run EXPLAIN ANALYZE on partitioned queries
- [ ] Measure performance improvement
- [ ] Plan zero-downtime migration strategy
- [ ] Update application code if needed
- [ ] Document partition maintenance procedures

---

### Proposal 10: ElasticSearch for Tag-Based Search (no)

Offload tag filtering to ElasticSearch for complex faceted queries.

**Benefits:**
- Designed for faceted search workloads
- Near-instant tag filtering
- Rich query language for complex filters
- Horizontal scalability

**Drawbacks:**
- New infrastructure dependency
- Data sync complexity
- Eventually consistent (not real-time)
- Learning curve and operational overhead

**Implementation Checklist:**
- [ ] Set up ElasticSearch cluster
- [ ] Design content index schema with tag fields
- [ ] Implement sync pipeline from PostgreSQL to ElasticSearch
- [ ] Add change data capture (CDC) or trigger-based sync
- [ ] Create content_service method using ElasticSearch client
- [ ] Implement fallback to PostgreSQL if ElasticSearch unavailable
- [ ] Add tag facet aggregations in ElasticSearch
- [ ] Test query performance vs PostgreSQL
- [ ] Monitor sync lag and index freshness
- [ ] Add ElasticSearch health checks
- [ ] Document ElasticSearch setup and operations
- [ ] Add tests for search functionality

### Proposal 11: Partitioned Parent Table — `content_items_all` (yes)

**Goal:** Replace the manual `UNION ALL` with a single logical table using **native Postgres partitioning**, while 
keeping subtype‑specific fields in sidecar tables. This improves planner choices (pruning, MergeAppend), simplifies 
cursor pagination, and reduces duplicated query code.

#### Benefits
- **Partition pruning:** Queries with `WHERE source_type IN ('items','auto')` (and later by `created_at`) scan only relevant partitions.
- **Faster ORDER BY/LIMIT:** Planner uses **MergeAppend** across child indexes; often avoids global sort.
- **Per‑partition tuning:** Different indexes/autovacuum, storage, fillfactor tailored to each child.
- **Operational flexibility:** Easier backfills, detach/attach, archiving per partition.
- **Simpler pagination cursor:** Single logical table removes multi‑table cursor encoding complexity.
- **Lean core schema:** Put rarely used subtype fields into sidecar tables to keep hot paths slim.

#### Drawbacks
- **Schema alignment required:** Parent and partitions must share identical columns (+ types/nullability).
- **More DDL ceremony:** Need per‑partition indexes, constraints, and careful attach steps.
- **Joins for extras:** Queries that need subtype extras pay a join (kept off critical path).

#### Implementation Checklist

**Migration Status Note (2025-10-18):**
- ✅ Migration files created and tested on local demo database
- ✅ Schema changes implemented in SQLAlchemy models  
- ⚠️ Migration pending production deployment (user will complete separately)
- 📝 Application code changes documented in `notes/perf-updates-205-10-17--phase-11-7-app-code-changes.md`
- ⏳ Will implement app code changes once migration is verified in all environments


**Phase 11.1: Schema Analysis & Planning**
- [x] Analyze existing `content_items` and `content_items_auto` schemas
- [x] Identify core columns (shared between both tables)
- [x] Identify subtype-specific columns to move to sidecar tables
- [x] Document schema alignment plan
- [x] Create migration rollback plan

**Phase 11.2: Schema Alignment**
- [x] Ensure all core columns match between `content_items` and `content_items_auto` (VERIFIED on demo DB)
- [x] 📋 Migration Preparation and Manual SQL Backup 

This is a long tangent but something we will need right now. Please look at these 8 subtasks for "Migration Preparation
and Manual SQL Backup", which is itself a subtask of "Phase 11.2: Schema Alignment", and complete these before moving on
to the rest of section "Phase 11.2: Schema Alignment".

Note that a first botched attempt was made. The wrong db was being referenced, and a manual version file was added. it
has been moved to: `notes/perf-updates-2025-10-17-migration-deleted.py`. It is there for your reference because it 
contains some useful code that you might be able to re-use. Namely: the stuff that cannot be auto-generated. Note that I
have just done an autogeneration and made a clean version that I think is totally fine. I think the next step is likely 
to ensure that the parent has the same schema as the child tables. Then you can make another automigration. Then, after 
that, you can make a manual migration with the minimal required stuff in order to finish creating the partition table.
If an existing table cannot be a partition table and you need to delete the parent partition table and only make it 
through a manually created alembic version file, then do that instead. It may also be that some stuff in the rest of 
the subphase for 11.2, and even beyond has already been completed and is already in the migration file that I made. I'm 
not sure. You should check.

The next steps are some utilities that we're going to need for doing stable migrations in the future. Go ahead adn do 
this stuff now, even though it is a sidetrack.

If you have questions, like if it seems like I'm giving conflicting information, let me know what questions you need 
clarified.

If Alembic (via `make migrate-prep`) cannot autogenerate a proper migration (for example, partitioning DDL or advanced 
DDL features), follow these steps before continuing to Phase 11.3:

1. **Generate and Apply Migration**
   ```bash
   make migrate-prep
   make migrate-demo
   make migrate-test
   ```

2. **Backup the Schema**
   ```bash
   pg_dump -s -d $DATABASE_URL > notes/backup-migration.sql
   ```
   > 💡 Save this file to `notes/backup-migration.sql` for reference and rollback safety.

3. **Manual Revision if Needed**
   If autogenerate missed key DDL (like `PARTITION BY`), create a manual migration:
   ```bash
   alembic revision -m "manual patch for partitioning"
   ```
   Insert SQL directly in `upgrade()`:
   ```python
   op.execute(open("notes/backup-migration.sql").read())
   ```

4. **Schema Diff (Optional Validation)**
   ```bash
   migra --unsafe postgres://user:pass@localhost/genonaut postgres://user:pass@localhost/genonaut_tmp > notes/manual_diff.sql
   ```

5. **Re-Apply and Verify**
   ```bash
   make migrate-demo
   make migrate-test
   ```

6. **Makefile Enhancements**
   - Add a `dump-schema` target:
     ```make
     dump-schema:
     	pg_dump -s -d $${DATABASE_URL} > notes/backup-migration.sql
     	@echo "✅ Schema dump saved to notes/backup-migration.sql"
     ```
   - Update `migrate-prep` target to remind users:
     ```make
     migrate-prep:
     	@echo "🧱 Preparing migration stub..."
     	alembic revision --autogenerate -m "$(m)"
     	@echo "⚠️  After running this migration, please run 'make dump-schema' to back up the current schema."
     ```

7. **Documentation Updates**
   - Add instructions to `docs/db.md`:
     - Initialization = `make migrate-prep`, followed by schema diff check against `notes/backup-migration.sql`
     - Manual edits should always be reviewed and backed up via `make dump-schema`

8. **Agent Notes**
   - Update `agents.md` with a note that if Alembic autogenerate cannot produce valid SQL, the agent should:
     - Pause and ask the user for approval before editing migrations manually.
     - Create a backup schema file.
     - Log these steps clearly for audit.

Regarding this worry:
> PostgreSQL partitioning requires that the partition key (source_type) be part of the PRIMARY KEY.

That's not true. take the following steps:
** ✅ Summary

This plan creates the partitioned parent table **without dropping any primary keys or foreign keys**.
It uses per-child **unique indexes** that can be attached to the parent’s **composite primary key**.

**Context**

PostgreSQL requires that a partitioned table’s **PRIMARY KEY** include its **partition key** (here: `source_type`).
Your existing PKs are `(id)` on each child table, but they’re referenced by many FKs — dropping them would cascade
and break those relationships.

Instead, we create **new unique indexes** `(id, source_type)` on each child, and then **attach** them to the parent’s
partitioned unique index. Finally, that index becomes the parent’s PRIMARY KEY.

**Step-by-Step Plan**

**1. Preconditions**

- Both child tables (`content_items`, `content_items_auto`) have identical schemas.
- Each has a constant `source_type` column (`'items'` and `'auto'`) defined as a **generated stored column**.
- Both tables use the same sequence/PK generation strategy for `id`.

**2. Ensure `source_type` is NOT NULL**

```sql
ALTER TABLE content_items
  ALTER COLUMN source_type SET NOT NULL;

ALTER TABLE content_items_auto
  ALTER COLUMN source_type SET NOT NULL;
```

**3. Create Per-Child Unique Indexes**

These act as “subpartitions” of the parent’s composite key `(id, source_type)`.

```sql
CREATE UNIQUE INDEX IF NOT EXISTS items_uidx_id_src
  ON content_items (id, source_type);

CREATE UNIQUE INDEX IF NOT EXISTS auto_uidx_id_src
  ON content_items_auto (id, source_type);
```

**4. Attach Partitions to the Parent Table**

```sql
-- Parent table already exists:
-- CREATE TABLE content_items_all (...) PARTITION BY LIST (source_type);

ALTER TABLE content_items_all
  ATTACH PARTITION content_items FOR VALUES IN ('items');

ALTER TABLE content_items_all
  ATTACH PARTITION content_items_auto FOR VALUES IN ('auto');
```

**5. Create a Partitioned Unique Index on Parent**

This defines the global uniqueness constraint across all partitions.

```sql
CREATE UNIQUE INDEX content_items_all_uidx_id_src
  ON content_items_all (id, source_type);
```

**6. Attach Child Indexes to Parent Unique Index**

```sql
ALTER INDEX content_items_all_uidx_id_src
  ATTACH PARTITION items_uidx_id_src;

ALTER INDEX content_items_all_uidx_id_src
  ATTACH PARTITION auto_uidx_id_src;
```

**7. Promote the Partitioned Unique Index to PRIMARY KEY**

```sql
ALTER TABLE content_items_all
  ADD CONSTRAINT content_items_all_pkey
  PRIMARY KEY USING INDEX content_items_all_uidx_id_src;
```

**✅ Why This Works**

- PostgreSQL only requires that **unique/PK constraints on partitions** include the partition key.
- You don’t need to drop existing `(id)` PKs or foreign keys.
- This design preserves all referential integrity and avoids CASCADE operations.

**⚠️ Pitfalls to Watch**

- **ID Collisions:** If both partitions share the same sequence, duplicates on `(id)` are fine as long as
  `(id, source_type)` is unique. If global uniqueness is desired, share one sequence or enforce it externally.
- **Insert Path:** Always insert into the **parent table** (`content_items_all`) with `source_type` present or
  generated.
- **Pagination Indexes:** Maintain `(created_at DESC, id DESC)` on each child for keyset pagination.
- **CHECK Constraints:** Avoid conflicting CHECK constraints; rely on partition bounds.
- **FKs to Parent:** Future FKs to the parent must include `source_type` in the referencing columns.

**✅ TL;DR**

**Do NOT use `DROP PK CASCADE`.**
Instead:
1. Add per-child **UNIQUE (id, source_type)** indexes.
2. Attach those indexes to a parent **partitioned unique index**.
3. Promote that to the parent’s **PRIMARY KEY**.

This achieves full partition compliance with zero FK or data loss risk.

- [x] Add `source_type` column to both tables via SQLAlchemy schema
- [x] Verify column types, nullability, and constraints match
- [x] Attempt: Define partitioned parent in SQLAlchemy and let Alembic autogenerate migration (IDK if this was skipped or not, but we're past it now)

**Phase 11.3: Create Parent Table**
- [x] Write Alembic migration to create `content_items_all` parent table
- [x] Define parent as PARTITION BY LIST (source_type)
- [x] Create parent with all core columns (no subtype-specific fields)
- [x] Test migration on copy of demo database first

**Phase 11.4: Attach Partitions**
- [x] Attach `content_items` as partition FOR VALUES IN ('items')
- [x] Attach `content_items_auto` as partition FOR VALUES IN ('auto')
- [x] Verify ATTACH completed successfully (no data copying)
- [x] Test queries against parent table

**Phase 11.5: Create Indexes**
- [x] Create index on `content_items`: (created_at DESC, id DESC)
- [x] Create index on `content_items_auto`: (created_at DESC, id DESC)
- [x] Verify indexes support keyset pagination
- [x] Run EXPLAIN to confirm indexes used

**Phase 11.6: Sidecar Tables (if needed)**
- [ ] Create `content_items_more` table (source_table, source_id FK, metadata_more jsonb)
- [ ] Create `content_items_auto_more` table (source_table, source_id FK, metadata_more jsonb)
- [ ] Add FK constraints with ON DELETE CASCADE
- [ ] Migrate subtype-specific data to sidecar tables (if any exists)

**Phase 11.6.2: Fix Alembic Autogenerate (COMPLETED 2025-10-18)**
- [x] Delete bad autogenerated migration that tried to drop parent table
- [x] Update env.py include_object hook to exclude content_items_all
- [x] Exclude partition-specific indexes from autogenerate
- [x] Test make migrate-prep produces no new migrations
- [x] Verify make migrate-demo shows nothing to apply

**Solution:** Updated `genonaut/db/migrations/env.py` to exclude partition-related objects from autogenerate:
- Parent table: `content_items_all`
- Partitioned unique index: `content_items_all_uidx_id_src`
- Per-partition unique indexes: `items_uidx_id_src`, `auto_uidx_id_src`
- Keyset pagination indexes: `idx_content_items_created_id_desc`, `idx_content_items_auto_created_id_desc`

**Root Cause:** SQLAlchemy models don't define the partitioned parent table (only child partitions).
Alembic's autogenerate saw `content_items_all` in the database but not in models, so it tried to drop it.
The `include_object` filter now tells Alembic to ignore these manually-managed partition structures.

**Phase 11.7: Update Application Code** ✅ COMPLETE (2025-10-18)
- [x] Update `ContentService.get_unified_content_paginated()` to query `content_items_all` instead of manual UNION
- [x] Update `ContentService.get_unified_content_stats()` to use `content_items_all` with partition pruning
- [x] Update `_apply_tag_filter_via_junction()` to support optional `content_source` parameter for ContentItemAll
- [x] Add `ContentItemAll` ORM class to `schema.py` (replaces Table object)
- [ ] Update INSERT operations to target parent table (deferred - inserts still go to child tables)
- [ ] Update UPDATE operations to target parent table (deferred - updates still go to child tables)
- [ ] Update DELETE operations to target parent table (deferred - deletes still go to child tables)

**Performance Results**: Queries using ContentItemAll show excellent performance:
- Single partition (source_type = 'items'): **0.199 ms** execution time
- Both partitions (source_type IN ('items', 'auto')): **0.354 ms** with MergeAppend
- Partition pruning verified working correctly
- Sub-millisecond query times achieved!

**Phase 11.8: Backend Testing**
- [x] Integration test: queries with WHERE source_type prune partitions (verified with EXPLAIN ANALYZE)
- [x] Integration test: ORDER BY uses MergeAppend (verified with EXPLAIN ANALYZE)
- [x] Integration test: verify pagination works across partitions (tested API endpoint)
- [ ] Unit test: INSERT into parent routes to correct partition
- [ ] Unit test: UPDATE via parent works correctly
- [ ] Unit test: DELETE via parent works correctly
- [x] Migrate test infrastructure from SQLite to PostgreSQL (see notes/sqlite-to-pg.md Phase 9)

**Test Infrastructure Migration (2025-10-19):**
- Removed SQLite database files from test/_infra/
- Updated test/conftest.py to use PostgreSQL test database by default
- Removed SQLite-specific code (JSONB compiler, SQLite database creation)
- All API integration tests, database tests, and worker tests now use PostgreSQL
- Some unit tests (test/db/unit/, test/integrations/comfyui/) still use SQLite in-memory for speed (acceptable for pure unit tests)
- See notes/sqlite-to-pg.md for complete migration documentation

**Phase 11.9: Performance Verification** ✅ COMPLETE (2025-10-18)
- [x] Run EXPLAIN (ANALYZE, BUFFERS) on queries after migration
- [x] Verify partition pruning is working (single partition: 0.199ms)
- [x] Verify MergeAppend is used for ORDER BY (both partitions: 0.354ms)
- [x] Document performance improvements (see Performance Results above)

**Phase 11.10: Documentation** ✅ COMPLETE (2025-10-18)
- [x] Document partitioning strategy in `docs/db.md`
- [x] Add EXPLAIN output verification showing pruning and MergeAppend
- [x] Update `notes/perf-updates-2025-10-17.md` with completion status
- [ ] Run full test suite: `make test-all`

#### DDL Sketch

> Align core schemas first (remove subtype‑only columns; those move to sidecars).

```sql
-- 1) Parent (core columns only)
CREATE TABLE content_items_all (
  id            bigint       PRIMARY KEY,
  title         text,
  content_type  text,
  content_data  jsonb,
  path_thumb    text,
  path_thumbs_alt_res text,
  prompt        text,
  creator_id    bigint       NOT NULL REFERENCES users(id),
  item_metadata jsonb,
  is_private    boolean      NOT NULL DEFAULT false,
  quality_score numeric,
  created_at    timestamptz  NOT NULL,
  updated_at    timestamptz  NOT NULL,
  source_type   text         NOT NULL  -- 'items' | 'auto'
) PARTITION BY LIST (source_type);

-- 2) Ensure children have identical columns + types
ALTER TABLE content_items
  ADD COLUMN IF NOT EXISTS source_type text
  GENERATED ALWAYS AS ('items') STORED;

ALTER TABLE content_items_auto
  ADD COLUMN IF NOT EXISTS source_type text
  GENERATED ALWAYS AS ('auto') STORED;

-- (Add/align any missing core columns so both match parent exactly.)

-- 3) Attach children as partitions
ALTER TABLE content_items_all
  ATTACH PARTITION content_items      FOR VALUES IN ('items');

ALTER TABLE content_items_all
  ATTACH PARTITION content_items_auto FOR VALUES IN ('auto');

-- 4) Indexes (per partition)
CREATE INDEX IF NOT EXISTS idx_items_created_id_desc
  ON content_items (created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_items_auto_created_id_desc
  ON content_items_auto (created_at DESC, id DESC);
```

##### Sidecar “extras” tables (one per subtype)
```sql
CREATE TABLE content_items_more (
  source_table   text    NOT NULL DEFAULT 'content_items',
  source_id      bigint  PRIMARY KEY
    REFERENCES content_items(id) ON DELETE CASCADE,
  metadata_more  jsonb   NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE content_items_auto_more (
  source_table   text    NOT NULL DEFAULT 'content_items_auto',
  source_id      bigint  PRIMARY KEY
    REFERENCES content_items_auto(id) ON DELETE CASCADE,
  metadata_more  jsonb   NOT NULL DEFAULT '{}'::jsonb
);
```

## Expected improvements of some proposals

| Proposal | Expected Time | Confidence | Complexity |
|----------|---------------|------------|------------|
| Redis Caching | < 100ms (cached) | Very High | Low |
| Pre-JOIN Filtering | 2-4s | Medium | Medium |
| Cursor Pagination | 1-2s (page 2+) | High | Medium |

## Recommended implementation Priority
1. Proposal 6: Cursor Pagination
2. Proposal 11: Partitioned Parent Table — `content_items_all`
3. Proposal 5: Pre-JOIN Tag Filtering (optimize existing)
4. Proposal 4 (Index Optimization) - Unlikely to reach target alone
5. Proposal 8: Tag Facet Aggregation Table
6. Proposal 2: Redis Caching (quick win, low risk)
  - Why last?: This is a quick win, but it will be a good idea to assess performance without this first, to see what 
  kind of performance we can expect for non-cached queries, and then continue to improve the performance of non-cached 
  queries if still necessary, or at least be able to know if the performance improvements we've written about here were 
  impleemnted correctly. Then we can add it.

## Additional Notes

### Why Non-Tag Queries Are Fast

The passing test `test_canonical_query_without_tag_is_fast` (< 2s) confirms that the problem is specifically the tag 
filtering EXISTS clause, not the UNION or pagination logic.

### Data Distribution

With 870K+ matches for a single tag (anime) out of 88M total junction records, the tag is popular but queries should 
still be optimized. Popular tags will benefit most from caching.

### Index Maintenance

The content_tags table should be monitored for:
- Index bloat
- VACUUM/ANALYZE scheduling
- Growth rate (currently averaging ~75 tags per item)

### Testing Strategy

After implementing any proposal:
1. Run performance tests against demo database
2. Measure with EXPLAIN ANALYZE
3. Test with multiple tag combinations (single, multiple, popular, rare)
4. Verify correctness with integration tests
5. Measure cache hit rates (if applicable)

## Conclusion

The 7-13 second query times are caused by inefficient EXISTS subqueries against an 88 million row junction table. The
most practical path to < 3s performance is:

1. **Cursor pagination** (Proposal 6) - Eliminate OFFSET overhead
2. **Partitioned parent table** (Proposal 11) - Simplify UNION and enable partition pruning
3. **Pre-JOIN tag filtering** (Proposal 5) - Filter in junction table first with adaptive strategies
4. **Index optimization** (Proposal 4) - Consolidated index improvements
5. **Tag aggregation** (Proposal 8) - Support UI and strategy selection
6. **Redis caching** (Proposal 2) - Final layer for maximum performance

This combination should bring typical queries to < 500ms (cached) and < 2s (uncached).

---

## Tags

*This section tracks reasons for skipped tasks using `@skipped-until-TAG` annotations.*

(No tags defined yet - will be added as tasks are skipped)

---

## Questions for Developer

*Questions that arose during implementation, organized by proposal/phase.*

(No questions yet - will be added as needed during implementation)

---

## Implementation Progress: Proposal 11 - Partitioned Parent Table

### Phase 11.1: Schema Analysis & Planning (In Progress)

**Analysis Date:** 2025-10-18

#### Current Schema Comparison

Both `content_items` and `content_items_auto` tables share the following **core columns**:

```
id                  integer (PK, auto-increment)
title               varchar(255) NOT NULL
content_type        varchar(50) NOT NULL
content_data        text NOT NULL
item_metadata       jsonb
creator_id          integer NOT NULL (FK to users.id)
created_at          timestamp NOT NULL
updated_at          timestamp NOT NULL
quality_score       double precision
is_private          boolean NOT NULL (default false)
path_thumb          varchar(512)
prompt              varchar(20000) NOT NULL (immutable via trigger)
```

#### Schema Differences Identified

**Legacy/Deprecated Columns (both tables):**
- `tags` (jsonb) - Deprecated; now using `content_tags` junction table
- `is_public` (boolean) - Redundant with `is_private`

**Column Order Differences:**
- `content_items`: has columns in slightly different order
- `content_items_auto`: has identical columns but different ordering

**Missing Columns (for partitioning):**
- Neither table has `source_type` column (required for PARTITION BY LIST)
- Neither table has `path_thumbs_alt_res` (defined in SQLAlchemy schema.py but not in DB)

#### Partitioning Strategy

**Parent Table Name:** `content_items_all`

**Partition Key:** `source_type` (TEXT, values: 'items', 'auto')

**Core Columns (for parent and both partitions):**
```sql
id                  bigint PRIMARY KEY
title               text NOT NULL
content_type        text NOT NULL
content_data        text NOT NULL
path_thumb          text
path_thumbs_alt_res jsonb  -- Add this from schema.py
prompt              text NOT NULL
creator_id          integer NOT NULL  -- Note: schema.py has UUID, DB has integer
item_metadata       jsonb DEFAULT '{}'
is_private          boolean NOT NULL DEFAULT false
quality_score       double precision DEFAULT 0.0
created_at          timestamptz NOT NULL
updated_at          timestamptz NOT NULL
source_type         text NOT NULL  -- NEW: 'items' | 'auto'
```

**Columns to Exclude from Parent (deprecated):**
- `tags` (jsonb) - Use `content_tags` junction table instead
- `is_public` (boolean) - Use `is_private` instead

**Sidecar Tables (for subtype-specific fields):**
- `content_items_more` (FK to content_items.id)
- `content_items_auto_more` (FK to content_items_auto.id)
- Structure: `(source_table text, source_id bigint PK, metadata_more jsonb)`

#### Migration Plan

1. **Add `source_type` column** to both child tables as GENERATED column
2. **Add `path_thumbs_alt_res` column** if needed (check if it's actually used)
3. **Create parent table** `content_items_all` with core columns only
4. **Attach existing tables** as partitions (no data movement)
5. **Create partition-specific indexes** for keyset pagination
6. **Update application code** to query parent table
7. **Optional:** Create sidecar tables if subtype-specific fields are needed later

#### Rollback Plan

- Detach partitions: `ALTER TABLE content_items_all DETACH PARTITION content_items;`
- Drop parent table: `DROP TABLE content_items_all;`
- Remove `source_type` columns from child tables
- Application reverts to manual UNION queries

#### Phase 11.2 Investigation: SQLAlchemy Partitioning Support

**Challenge:** SQLAlchemy does NOT have native declarative support for PostgreSQL table partitioning.

**Findings:**
1. **No `__partition_by__` attribute** in SQLAlchemy ORM
2. **Manual DDL required** for creating partitioned parent tables
3. **Alembic autogenerate** cannot detect partitioning configuration

**Attempted Approach:**
- Define parent table in SQLAlchemy with all shared columns
- Add `source_type` computed column to child tables
- Let Alembic autogenerate migration
- **Problem**: Alembic won't know to create `PARTITION BY LIST (source_type)` or `ATTACH PARTITION`

**Recommended Approach (requires manual migration):**
1. Update SQLAlchemy models to add `source_type` column to both child tables
2. Create new model `ContentItemAll` (abstract/not mapped, for reference only)
3. Run `make migrate-prep` to generate migration stub
4. Manually add partitioning DDL to migration:
   - `ALTER TABLE` to add `source_type` GENERATED columns
   - `CREATE TABLE content_items_all (...) PARTITION BY LIST (source_type)`
   - `ALTER TABLE content_items_all ATTACH PARTITION content_items ...`
   - `ALTER TABLE content_items_all ATTACH PARTITION content_items_auto ...`
5. Test migration on demo DB

**Alternative: Skip partitioning for now**
- Continue with Proposal 5 (Pre-JOIN Tag Filtering) and Proposal 4 (Index Optimization)
- Partitioning adds complexity without clear proof of benefit vs simpler optimizations
- Can revisit partitioning later after measuring gains from other proposals

#### Open Questions & Decisions

1. **Should we proceed with manual partitioning migration?**
   - PRO: Eliminates UNION overhead, enables partition pruning
   - CON: Requires manual DDL, complex migration, SQLAlchemy doesn't understand partitions
   - **DECISION NEEDED FROM USER**

2. **Demo DB Status (CORRECTED):**
   - `creator_id`: UUID (correct)
   - `tags`: REMOVED (clean)
   - `is_public`: REMOVED (clean)
   - `path_thumbs_alt_res`: EXISTS (correct)
   - Both child tables: IDENTICAL schemas (13 columns, same order)

#### Phase 11.1 Status: COMPLETE

**Summary (CORRECTED - Demo DB Analysis):**
- Both tables use same ContentItemColumns mixin in schema.py - already aligned
- **Demo DB** has 13 core columns that EXACTLY match between both tables (same order!)
- Columns: id, title, content_type, content_data, item_metadata, creator_id (UUID), created_at, updated_at, quality_score, is_private, path_thumb, prompt, path_thumbs_alt_res
- Need to add: `source_type` (generated column)
- Demo DB is clean - no deprecated `tags` or `is_public` columns
- Sidecar tables not needed

**CRITICAL LESSON LEARNED:**
- Was analyzing WRONG database (`genonaut` = dev) which had messy schema
- Should always use `genonaut_demo` for development work
- Dev DB had: different column order, integer creator_id vs UUID, deprecated columns

#### Phase 11.3-11.5: Partitioned Parent Table - COMPLETED

**Completion Date:** 2025-10-18

**Implementation Summary:**

Successfully created `content_items_all` partitioned parent table without dropping existing PKs/FKs using the safe unique index strategy.

**Migration Files:**
- `e7526785bd0d_add_source_type_generated_column_for_.py` - Adds source_type DEFAULT columns
- `86456c44a065_create_partitioned_parent_table_content_.py` - Creates partitioned parent and attaches children

**Key Implementation Details:**

1. Added `source_type` column (NOT NULL DEFAULT) to both child tables
2. Created per-child unique indexes `(id, source_type)`:
   - `items_uidx_id_src` on content_items
   - `auto_uidx_id_src` on content_items_auto
3. Created parent table WITHOUT PRIMARY KEY (cannot use USING INDEX on partitioned tables)
4. Attached both child tables as partitions
5. Created partitioned unique index `content_items_all_uidx_id_src`
6. Attached child indexes to parent index
7. Created keyset pagination indexes on each partition: `(created_at DESC, id DESC)`

**Result:**
- Parent table: `content_items_all` (1,175,205 total rows)
- Partition 'items': 65,205 rows
- Partition 'auto': 1,110,000 rows
- Unique index enforces uniqueness on `(id, source_type)` across all partitions
- Original PKs and all FKs remain intact

**Next Steps:**
- Phase 11.7: Update application code to query parent table
- Phase 11.8: Backend testing
- Phase 11.9: Performance verification with EXPLAIN ANALYZE
- Phase 11.10: Documentation


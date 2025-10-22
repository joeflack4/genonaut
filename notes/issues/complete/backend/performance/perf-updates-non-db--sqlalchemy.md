# Performance updates - non DB related

## Outer loop task list: Optimization areas
- [ ] **CRITICAL: Investigate and optimize SQLAlchemy ORM overhead**
  - This is the main bottleneck: 3.7s (95% of total time)
  - Multiple optimization strategies to explore
  - Expected improvement: 50-90% (1.5-3.3s savings)


## Investigation and problem solving, by topic
Use this section to create H3 (###) subsections, where you explore a given hypothesis (e.g. Pydantic serialization
(converting 25 content items with all fields to JSON)), and research it, understanding the code, timing how long it
takes that particular part of the code for the canonical query to execute, and coming up with possible solutions. Use
markdown checkboxes (- [ ]) to track your progress as you go, marking things off (- [x]) when you have completed a batch
of tasks.

### SQLAlchemy ORM Overhead Investigation ⚠️ CRITICAL BOTTLENECK (NOT IN OUTER LOOP)

See: "Report 3 - SQL Query Analysis and Timing"

**Problem**: SQLAlchemy `.all()` takes 3,761ms while raw SQL takes 5.4ms - a 700x slowdown!

**Current Behavior**:
- Database query execution: 5.4ms (excellent, well-optimized)
- SQLAlchemy `.all()` call: 3,761ms (BOTTLENECK!)
- The issue is NOT the database, but result processing in the ORM layer

**Hypotheses for Future Investigation**:
1. JSONB deserialization overhead
2. Row object creation overhead
3. Deferred/lazy loading
4. Network/data transfer

**Data collected**:
- JSONB field sizes are small: `content_data` avg 58 bytes, `item_metadata` avg 1.3KB
- Total row size: 16KB for 10 rows (1.6KB per row)
- Data transfer is NOT the issue (only 16KB total)

**Next steps** (for future work, not now):
- Profile Python code to isolate exact bottleneck
- Test deferred loading of JSONB fields
- Consider raw SQL for list endpoints


**Problem**: SQLAlchemy's `.all()` call takes 3.7 seconds while raw SQL takes 5ms - a 700x slowdown. This is the PRIMARY performance bottleneck (95% of query time).

**Background**:
- Database query execution: 5.4ms (excellent)
- SQLAlchemy `.all()` call: 3,761ms (BOTTLENECK!)
- JSONB fields are small (avg 58 bytes content_data, 1.3KB item_metadata)
- Total data transfer: only 16KB for 10 rows
- Data transfer is NOT the issue

**Investigation Phase**:

1. **Profile SQLAlchemy overhead** (REQUIRED FIRST):
   - [ ] Create profiling script to isolate exact bottleneck
   - [ ] Use cProfile or line_profiler on the query execution
   - [ ] Measure timing breakdown:
     - [ ] Query compilation time
     - [ ] Network round-trip time
     - [ ] Result fetching time
     - [ ] ORM object creation time
     - [ ] JSONB deserialization time
   - [ ] Identify the specific slow operation

2. **Test hypothesis: JSONB deserialization**:
   - [ ] Test query with `defer(ContentItemsAll.content_data, ContentItemsAll.item_metadata)`
   - [ ] Measure if excluding JSONB fields improves performance
   - [ ] If yes: Consider deferred loading for list endpoints
   - [ ] If no: Move to next hypothesis

3. **Test hypothesis: ORM object creation overhead**:
   - [ ] Compare performance of:
     - [ ] `.all()` - Creates ORM objects
     - [ ] `.scalars().all()` - Returns scalar values
     - [ ] Raw SQL with `.execute().fetchall()` - No ORM
   - [ ] Measure overhead of ORM object instantiation
   - [ ] If significant: Consider raw SQL for list endpoints

4. **Test hypothesis: Result streaming**:
   - [ ] Test `query.yield_per(10)` for streaming results
   - [ ] Measure if this reduces memory/processing overhead
   - [ ] Compare with `.all()` performance

5. **Test hypothesis: Connection/transaction overhead**:
   - [ ] Check database connection pool settings
   - [ ] Verify connection reuse is happening
   - [ ] Test with connection pooling adjustments
   - [ ] Measure impact

**Optimization Strategies** (based on profiling results):

**Strategy A: Deferred JSONB Loading**
- [ ] Implement: Add `defer()` for content_data and item_metadata on list queries
- [ ] Load these fields only on detail view endpoints
- [ ] Test performance improvement
- [ ] Update response models to handle optional fields
- [ ] Expected impact: TBD (if JSONB is the bottleneck)

**Strategy B: Raw SQL for List Endpoints**
It seemed like this was mostly what it did.

- [ ] Implement: Create raw SQL query version of `get_unified_content_paginated()`
- [ ] Use `session.execute(text(sql))` with proper parameterization
- [ ] Map results to response dictionaries (skip ORM objects)
- [ ] Keep ORM for detail views and writes
- [ ] Test performance improvement
- [ ] Expected impact: Up to 700x faster (5ms vs 3,761ms)

**Strategy C: Optimize ORM Configuration**
- [ ] Review SQLAlchemy model configuration for lazy loading
- [ ] Check for unintended relationship loading
- [ ] Verify `lazy='select'` vs `lazy='joined'` settings
- [ ] Test with different loading strategies
- [ ] Expected impact: 10-50% improvement

**Strategy D: Result Set Optimization**
- [ ] Implement pagination at database level (already done)
- [ ] Use `yield_per()` for streaming large result sets
- [ ] Consider server-side cursors for very large queries
- [ ] Expected impact: 20-40% improvement

**Strategy E: Column Subset Selection**
- [ ] Only SELECT columns needed for list view
- [ ] Exclude large JSONB fields by default
- [ ] Use `.with_entities()` or `.options(load_only())`
- [ ] Expected impact: 30-60% improvement

**Implementation Priority** (after profiling):
1. Profile and identify exact bottleneck
2. Test quick wins (deferred loading, column subset)
3. If insufficient, implement raw SQL for list endpoints
4. Verify with performance tests
5. Update E2E and integration tests

**Testing Requirements**:
- [ ] All existing tests must pass
- [ ] Add performance test for list endpoint (<500ms target)
- [ ] Add performance test comparing different strategies
- [ ] Verify data consistency (raw SQL matches ORM results)
- [ ] Test with different page sizes (10, 25, 50, 100)
- [ ] Test with different filters (tags, source types, etc.)

**Expected Performance Impact**: 50-90% improvement (1.5-3.3s savings), potentially bringing query time from 3.7s to 0.2-1.8s

**Files to Check/Modify**:
- `genonaut/api/services/content_service.py:690-1072` - Main query method
- `genonaut/db/schema.py` - SQLAlchemy models
- `genonaut/api/db/database.py` - Database session configuration
- Create new profiling script: `/tmp/profile_sqlalchemy_overhead.py`

**Success Criteria**:
- [ ] Identify exact source of 3.7s overhead
- [ ] Implement optimization reducing query time by >50%
- [ ] All tests passing
- [ ] No data consistency issues
- [ ] Performance improvement verified with measurements

**Results**:
(To be filled in after investigation and implementation)

## Reports
### Report 1 - SQL Query Analysis and Timing
(copy of 'report 3' in ./perf-updates-non-db.md)

This report analyzes ALL SQL queries executed for the canonical query and identifies where time is actually being spent.

#### Test Methodology

**Canonical Query URL:**
```
GET /api/v1/content/unified?page=1&page_size=10&content_source_types=user-regular&content_source_types=user-auto&content_source_types=community-regular&content_source_types=community-auto&user_id=121e194b-4caa-4b81-ad4f-86ca3919d5b9&sort_field=created_at&sort_order=desc&tag=dfbb88fc-3c31-468f-a2d7-99605206c985
```

Four different execution contexts were tested:
1. **Direct SQL via psql** - Raw PostgreSQL execution
2. **Raw SQLAlchemy query** - Python script with SQLAlchemy
3. **Service method call** - Direct Python call to `ContentService.get_unified_content_paginated()`
4. **HTTP API request** - Full end-to-end HTTP request via requests library

#### SQL Queries Executed

**Query 1: Main Content Query** (with tag filtering)

```sql
SELECT content_items_all.source_type, content_items_all.id, content_items_all.title,
       content_items_all.content_type, content_items_all.content_data, content_items_all.path_thumb,
       content_items_all.path_thumbs_alt_res, content_items_all.prompt, content_items_all.item_metadata,
       content_items_all.creator_id, content_items_all.created_at, content_items_all.updated_at,
       content_items_all.quality_score, content_items_all.is_private
FROM content_items_all
WHERE (content_items_all.source_type = 'items' AND content_items_all.creator_id = '121e194b-4caa-4b81-ad4f-86ca3919d5b9'
   OR content_items_all.source_type = 'auto' AND content_items_all.creator_id = '121e194b-4caa-4b81-ad4f-86ca3919d5b9'
   OR content_items_all.source_type = 'items' AND content_items_all.creator_id != '121e194b-4caa-4b81-ad4f-86ca3919d5b9'
   OR content_items_all.source_type = 'auto' AND content_items_all.creator_id != '121e194b-4caa-4b81-ad4f-86ca3919d5b9')
AND (EXISTS (SELECT 1 FROM content_tags
             WHERE content_tags.content_id = content_items_all.id
             AND content_tags.content_source = content_items_all.source_type
             AND content_tags.tag_id = 'dfbb88fc-3c31-468f-a2d7-99605206c985'))
ORDER BY content_items_all.created_at DESC, content_items_all.id DESC
LIMIT 10;
```

**Execution Plan:**
- Uses Merge Append for partition-wise scanning (content_items + content_items_auto)
- Index scans on `idx_content_items_created_id_desc` and `idx_content_items_auto_created_id_desc`
- Nested Loop with Index Only Scan on `content_tags_pkey` for tag filtering
- Scans 218 rows from content tables, finds 10 matching rows after tag filter

**No stats queries** (include_stats=false by default)

#### Timing Results

| Execution Context | Query Execution Time | Total Time | Overhead | Breakdown |
|-------------------|---------------------|------------|----------|-----------|
| **Direct SQL (psql)** | 5.4ms | 9.3ms | 3.9ms | Planning: 2.6ms, Execution: 5.4ms, psql overhead: 1.3ms |
| **Raw SQLAlchemy** | 18.2ms | 73.1ms | 54.9ms | Query build + fetch: 18ms, Python processing: 55ms |
| **Service Method** | **3,761.6ms** | 3,765ms | 3.4ms | **Query exec: 3,761ms**, Serialization: 1ms, Tag proc: 1ms, Query build: 1ms |
| **HTTP API** | ~3,761ms | ~3,000-3,800ms | ~239ms | Service: 3,765ms, FastAPI/network: ~239ms |

#### CRITICAL FINDING: 700x SQLAlchemy Slowdown

**The Problem:**
- Raw SQL executes in 5.4ms
- SQLAlchemy's `.all()` call takes 3,761.6ms
- **This is a 700x slowdown in the ORM layer**

**What this means:**
- Database is NOT the bottleneck (5ms is excellent)
- PostgreSQL query plan is optimal
- Partitioning, indexes, and tag filtering are all working correctly
- **The bottleneck is in SQLAlchemy's result fetching/processing**

**Why SQLAlchemy is slow (hypotheses):**
1. **JSONB deserialization** - Large `content_data` and `item_metadata` fields
2. **Row object creation** - Overhead of creating ORM objects for each row
3. **Lazy loading** - Potential additional queries for relationships (though none detected)
4. **Connection/transaction overhead** - Though this should be minimal
5. **Network round-trips** - Data transfer from PostgreSQL to Python

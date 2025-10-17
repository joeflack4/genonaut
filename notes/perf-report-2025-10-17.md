# Performance Test Failure Analysis - 2025-10-17

## Executive Summary

Gallery tag filtering queries are taking 7-13 seconds to complete, significantly exceeding the 3-second performance target. The root cause is an inefficient tag filtering implementation using EXISTS subqueries against a junction table with **88+ million rows** (content_tags).

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
- 4 separate UNION queries (one per content source type)
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

### Proposal 1: Materialized Views for Popular Tags

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

### Proposal 2: Query Result Caching (Redis)

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
- [ ] Design cache key structure (hash of query parameters)
- [ ] Implement cache layer in content_service.get_unified_content_paginated
- [ ] Set appropriate TTL (5-10 minutes recommended)
- [ ] Implement cache warming for popular queries
- [ ] Add cache invalidation on content creation/update/delete
- [ ] Monitor Redis memory usage
- [ ] Add cache hit/miss metrics to logging
- [ ] Implement cache bypass flag for real-time requirements
- [ ] Add Redis connection pool optimization
- [ ] Add tests for cache invalidation logic
- [ ] Document cache warming strategy

---

### Proposal 3: Denormalized Tag Array Column

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

### Proposal 4: Optimized Index Strategy

Create composite indexes optimized for the exact query patterns.

**Benefits:**
- No schema changes required
- Can improve performance immediately
- Works with existing query structure
- Low risk

**Drawbacks:**
- Limited gains with 88M row table
- Index size overhead
- May not reach 3s target alone

**Implementation Checklist:**
- [ ] Analyze query execution plans (EXPLAIN ANALYZE)
- [ ] Create composite index: (tag_id, content_source, content_id)
- [ ] Create partial indexes for specific content_source values
- [ ] Run VACUUM ANALYZE on content_tags table
- [ ] Measure index size vs performance gains
- [ ] Consider index-only scans optimization
- [ ] Test query performance with new indexes
- [ ] Monitor index bloat over time
- [ ] Add index maintenance to database docs
- [ ] Remove redundant indexes if new ones are better

---

### Proposal 5: Pre-JOIN Tag Filtering

Restructure query to filter in junction table first, then JOIN to content tables.

**Benefits:**
- Reduces intermediate result set size
- More efficient use of indexes
- Better query planner optimization potential
- No schema changes required

**Drawbacks:**
- Complex query rewrite
- May not scale to "all" tag matching
- Still needs to handle UNION complexity

**Implementation Checklist:**
- [ ] Rewrite get_unified_content_paginated to filter in junction first
- [ ] Change from EXISTS to explicit JOIN with content_tags
- [ ] Apply tag filter before UNION (filter in junction table)
- [ ] Use JOIN to bring in content_items/content_items_auto after filtering
- [ ] Optimize for "any" matching (IN clause on tag_id)
- [ ] Optimize for "all" matching (GROUP BY with HAVING COUNT)
- [ ] Run EXPLAIN ANALYZE to verify query plan improvement
- [ ] Test with single tag and multiple tags
- [ ] Benchmark against current implementation
- [ ] Update tests to verify correctness
- [ ] Add query performance logging
- [ ] Document new query structure

---

### Proposal 6: Pagination Cursor Optimization

Implement cursor-based pagination specifically for tag-filtered queries.

**Benefits:**
- Eliminates OFFSET overhead
- Faster subsequent page loads
- More consistent performance across pages
- Works well with large result sets

**Drawbacks:**
- Can't jump to arbitrary pages
- Complex cursor encoding for multi-table UNION
- Requires UI changes for cursor-based navigation

**Implementation Checklist:**
- [ ] Design cursor format for unified queries (encode: created_at, id, source_type)
- [ ] Add cursor parameter to get_unified_content endpoint
- [ ] Implement cursor decoding and WHERE clause generation
- [ ] Replace OFFSET with WHERE > cursor for each subquery
- [ ] Test cursor stability across tag filter changes
- [ ] Handle edge cases (deleted items, updated timestamps)
- [ ] Update frontend to use cursor pagination
- [ ] Add cursor validation and error handling
- [ ] Document cursor format and encoding
- [ ] Add tests for cursor edge cases

---

### Proposal 7: Read Replicas for Tag Queries

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

---

### Proposal 8: Tag Facet Aggregation Table

Create a separate aggregation table: tag_content_counts (tag_id, content_source, count).

**Benefits:**
- Fast tag popularity queries
- Can pre-filter unpopular tags
- Helps with faceted search UI
- Reduces load for count queries

**Drawbacks:**
- Requires periodic updates
- Doesn't solve core filtering performance
- Additional storage overhead

**Implementation Checklist:**
- [ ] Create tag_content_counts table schema
- [ ] Add indexes on (tag_id, content_source)
- [ ] Write aggregation query to populate counts
- [ ] Create Celery task to refresh counts (hourly)
- [ ] Update tag filtering to use counts for validation
- [ ] Add "popular tags" endpoint using counts
- [ ] Optimize frontend tag selector with count data
- [ ] Add tests for count accuracy
- [ ] Monitor aggregation job performance
- [ ] Document refresh strategy

---

### Proposal 9: Database Partitioning for content_tags

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

### Proposal 10: ElasticSearch for Tag-Based Search

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

---

## Recommended Approach

**Immediate (< 1 week):**
1. **Proposal 2: Query Result Caching (Redis)** - Fastest implementation, immediate impact
2. **Proposal 5: Pre-JOIN Tag Filtering** - Optimize existing query structure

**Short-term (1-2 weeks):**
3. **Proposal 3: Denormalized Tag Array Column** - Fundamental performance improvement
4. **Proposal 6: Pagination Cursor Optimization** - Better pagination performance

**Long-term (1+ months):**
5. **Proposal 9: Database Partitioning** - Scalability for continued growth
6. **Proposal 10: ElasticSearch** - If complex search requirements expand

**Skip for now:**
- Proposal 1 (Materialized Views) - Caching is more flexible
- Proposal 4 (Index Optimization) - Unlikely to reach target alone
- Proposal 7 (Read Replicas) - Premature for current scale
- Proposal 8 (Aggregation Table) - Doesn't solve core issue

## Expected Improvements

| Proposal | Expected Time | Confidence | Complexity |
|----------|---------------|------------|------------|
| Redis Caching | < 100ms (cached) | Very High | Low |
| Pre-JOIN Filtering | 2-4s | Medium | Medium |
| Denormalized Arrays | 0.5-1.5s | High | High |
| Cursor Pagination | 1-2s (page 2+) | High | Medium |
| Partitioning | 3-5s | Medium | Very High |
| ElasticSearch | < 200ms | Very High | Very High |

## Implementation Priority

**Priority 1 (Critical - Do First):**
- Proposal 2: Redis Caching (quick win, low risk)
- Proposal 5: Pre-JOIN Tag Filtering (optimize existing)

**Priority 2 (High - Do Next):**
- Proposal 3: Denormalized Tag Arrays (major improvement)

**Priority 3 (Medium - Consider Later):**
- Proposal 6: Cursor Pagination
- Proposal 9: Database Partitioning

**Priority 4 (Low - Future Consideration):**
- Proposal 10: ElasticSearch (if search needs grow)

## Additional Notes

### Why Non-Tag Queries Are Fast

The passing test `test_canonical_query_without_tag_is_fast` (< 2s) confirms that the problem is specifically the tag filtering EXISTS clause, not the UNION or pagination logic.

### Data Distribution

With 870K+ matches for a single tag (anime) out of 88M total junction records, the tag is popular but queries should still be optimized. Popular tags will benefit most from caching.

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

The 7-13 second query times are caused by inefficient EXISTS subqueries against an 88 million row junction table. The most practical path to < 3s performance is:

1. **Redis caching** for immediate relief (80-90% of queries cached)
2. **Query restructuring** (Pre-JOIN) for uncached queries
3. **Denormalized tag arrays** for long-term scalability

This combination should bring typical queries to < 500ms (cached) and < 2s (uncached).

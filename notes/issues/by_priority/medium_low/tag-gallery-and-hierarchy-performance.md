# Performance

## Phases
### 0. Tag Hierarchy Cache
- [ ] Design caching mechanism for full hierarchy JSON: @skipped-until-optimization
  - Option A: Materialized view storing complete JSON
  - Option B: Table with single row storing complete hierarchy JSON
  - Option C: Application-level caching with DB triggers to invalidate
- [ ] Choose best approach balancing performance vs complexity @skipped-until-optimization
- [ ] Implement auto-refresh mechanism when tags table changes @skipped-until-optimization

**Note**: Hierarchy will be loaded on-demand initially. We can add caching later if needed based on performance metrics.

### 1. Performance Testing
- [ ] Create `test/performance/test_tag_queries.py`:
  - Benchmark hierarchy query performance
  - Benchmark tag filtering on large datasets
  - Benchmark rating queries
  - Test recursive CTE performance for ancestors/descendants

### 2. Deferred Optimization Tasks (from Phase 1)
- [ ] Phase 1.3 Revisit: Create `TagStatistics` model/materialized view if needed:
  - Implement if on-demand computation is too slow
  - Create materialized view or trigger-updated table
  - Add mechanism to auto-update when tags or ratings change
  - Compare performance before/after
- [ ] Phase 1.5 Revisit: Implement tag hierarchy cache if needed:
  - Implement if hierarchy loading is too slow
  - Choose caching approach (materialized view, Redis, app-level cache)
  - Implement auto-refresh mechanism when tags table changes
  - Measure cache hit rates and performance improvement

### 3. Query Optimization
- [ ] Review and optimize database queries:
  - Analyze query plans with EXPLAIN
  - Ensure proper index usage
  - Add indexes if needed based on query plans
  - Optimize recursive CTEs if needed
- [ ] Optimize caching strategy:
  - Review cache hit rates
  - Tune cache invalidation
  - Test cache performance

### 4. Load Testing
- [ ] Test API endpoints under load:
  - Concurrent tag queries
  - Concurrent rating submissions
  - Gallery filtering with tags
  - Hierarchy queries under load
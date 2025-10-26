# Proposal Reids caache
## Preamble
We want to implement Redis caching to improve perforamnce of popular endpoints (hit without query params) and queries.

## Instructions
We'd like to implement this Redis caching. We'd like to cache the common endpoints (hit with no query params), as well 
as the most popular queries, partiuclarly queries coming from the gallery page. Additinally, every user should get its 
general content_items and content_items_auto queries hit...
- think about this. if i cache user stuff in this way, then i should cache the community stuff separately, and merge 
them after. For 4 gen types, that should be 4 diff results that i should recombine. is this difficult? should save a lot
of memory because that way we don't have to have every content + auto cached in 1, which is useless if user just wants 
1, and i dont want want to cache all community data with every single user query every time
- mention that anything else in app that makes sense to cahce should
 
- say?: But I've never done such caching before. makefile I'd like you to make commmands...
- say something about: Cache query results for common filter combinations in Redis.

Break this off into own issue and inform redis caching
- we should improve analytics. what's the best way to store all previous backend routes hit? 1 pg table? redis? external
piece of software? 3rd party service? basically i want to know what was hit, at what time, by what user, and what time 
it happened, and how long it took for the backend to handle the request

Context: We'll use this to determine what Redis will cache, as a function of frequency and time taken to serve.
**NOTE to self**: is there a general algorithm like this well accepted for choosing what to cache based on these or more 
params?
- See: route-analytics.md

## Additional notes
### Pros/cons
Benefits:
- Fastest possible response for cached queries (< 100ms)
- Works for any tag, not just popular ones (for tagged content queries)
- Reduces database load significantly
- Easy to implement with existing Redis infrastructure

Drawbacks:
- Cache invalidation complexity
- Memory overhead in Redis
- Potential stale data if invalidation strategy is wrong

## Impleemntation checklist

### Phase 1: Cache Key Design
- [ ] Design cache key structure (sorted tags + user + filters + sort)
- [ ] Implement canonicalization function (consistent key generation)
- [ ] Add versioning to cache keys (for schema changes)
- [ ] Handle edge cases (empty tags, null filters)

### Phase 2: Cache Layer Implementation
- [ ] Add cache check at start of `get_unified_content_paginated`
- [ ] Serialize/deserialize response objects (JSON or MessagePack)
- [ ] Set TTL (5-10 minutes recommended, configurable)
- [ ] Add cache write on successful query
- [ ] Handle Redis connection errors gracefully (fall through to DB)

### Phase 3: Cache Invalidation
- [ ] Add cache invalidation on content creation
- [ ] Add cache invalidation on content update (tags changed)
- [ ] Add cache invalidation on content deletion
- [ ] Implement pattern-based invalidation (e.g., all queries with tag X)
- [ ] Add manual cache clear endpoint (admin only)

### Phase 4: Cache Bypass & Warming
- [ ] Add `cache_bypass` flag to API endpoint (for real-time needs)
- [ ] Implement cache warming for popular tag combinations
- [ ] Create Celery task to prewarm cache (optional)
- [ ] Add cache refresh strategy (update stale entries in background)

### Phase 5: Monitoring & Metrics
- [ ] Add cache hit/miss logging
- [ ] Track cache hit rate percentage
- [ ] Monitor Redis memory usage
- [ ] Add metrics for cache invalidation frequency
- [ ] Create dashboard or logging for cache performance

### Phase 6: Backend Testing
- [ ] Unit test: cache key generation and canonicalization
- [ ] Unit test: serialization/deserialization
- [ ] Integration test: cache hit returns correct data
- [ ] Integration test: cache miss queries database
- [ ] Integration test: cache invalidation on content changes
- [ ] Integration test: cache bypass flag works
- [ ] Verify `make test` passes

### Phase 7: Performance Verification
- [ ] Measure cached query response time (target: < 100ms)
- [ ] Measure uncached query response time (should match non-cached improvements)
- [ ] Test cache hit rate with realistic traffic patterns
- [ ] Verify cache doesn't impact write performance
- [ ] Document performance improvements (cached vs uncached)

### Phase 8: Documentation
- [ ] Document caching strategy in `docs/api.md` or `docs/performance.md`
- [ ] Document cache key format and invalidation rules
- [ ] Add configuration examples (TTL, cache size limits)
- [ ] Document cache warming strategy
- [ ] Update `README.md` with caching features
- [ ] Run full test suite: `make test-all`
# Gallery Tag Query Performance - Future Enhancements

This document covers additional performance optimization strategies that are deferred until after the core tag normalization work (documented in `notes/fix-gallery-tag-query.md`) is complete.

## When to Consider These Options

Implement these enhancements if:
- Core normalization (Option 3) + query optimization (Option 5) don't achieve performance targets
- Query times still exceed p95 < 3 seconds or p99 < 5 seconds
- High load causes database bottlenecks
- Users experience latency during peak traffic

## Option 2: Materialized View with Pre-Joined Data

### Overview

Create a materialized view that pre-joins content with users and includes denormalized tag data. This eliminates UNION overhead and JOIN costs at query time.

### Implementation

```sql
CREATE MATERIALIZED VIEW unified_content_with_tags AS
SELECT
  'regular' as source_type,
  ci.id, ci.title, ci.content_type, ci.content_data,
  ci.path_thumb, ci.path_thumbs_alt_res, ci.prompt,
  ci.creator_id, u.username as creator_username,
  ci.item_metadata, ci.tags, ci.is_private, ci.quality_score,
  ci.created_at, ci.updated_at
FROM content_items ci
JOIN users u ON u.id = ci.creator_id
UNION ALL
SELECT
  'auto' as source_type,
  cia.id, cia.title, cia.content_type, cia.content_data,
  cia.path_thumb, cia.path_thumbs_alt_res, cia.prompt,
  cia.creator_id, u.username as creator_username,
  cia.item_metadata, cia.tags, cia.is_private, cia.quality_score,
  cia.created_at, cia.updated_at
FROM content_items_auto cia
JOIN users u ON u.id = cia.creator_id;

-- Create indexes on the materialized view
CREATE INDEX idx_unified_tags_gin
ON unified_content_with_tags USING gin(tags);

CREATE INDEX idx_unified_creator_created
ON unified_content_with_tags(creator_id, created_at DESC);

CREATE INDEX idx_unified_created
ON unified_content_with_tags(created_at DESC);

-- For concurrent refresh, need a UNIQUE index
CREATE UNIQUE INDEX idx_unified_pk
ON unified_content_with_tags(source_type, id);
```

### Query Example

```sql
-- Simplified query against view
SELECT *
FROM unified_content_with_tags
WHERE creator_id = :user_id
  AND tags @> :tag_array  -- or use junction table if normalized
ORDER BY created_at DESC
LIMIT 25;
```

### Refresh Strategies

#### Option A: Periodic Refresh (Acceptable Staleness)

```sql
-- Refresh every 5-10 minutes via cron job or scheduled task
REFRESH MATERIALIZED VIEW CONCURRENTLY unified_content_with_tags;
```

With CONCURRENTLY, the view remains available during refresh, but requires UNIQUE index.

**Pros**:
- Simple to implement
- Predictable resource usage
- Acceptable staleness: 5-10 minutes per requirements

**Cons**:
- Data can be up to 10 minutes stale
- Refresh time increases with data volume (1M+ rows)

#### Option B: Event-Triggered Refresh

```python
# In content service, after create/update/delete
def _trigger_view_refresh():
    # Queue background job to refresh view
    celery_app.send_task('refresh_materialized_view', countdown=30)
```

Use debouncing to avoid excessive refreshes during bursts.

**Pros**:
- Fresher data
- Refresh only when needed

**Cons**:
- More complex to implement
- Can cause resource spikes during high write activity

#### Option C: Incremental Maintenance (Advanced)

Use triggers or change data capture to maintain view incrementally. Complex but keeps data fresh.

### Pros

- **Massive query simplification**: Single table instead of UNION
- **Pre-joined data**: Eliminates JOIN overhead at query time
- **Better query planner optimization**: Simpler query plans
- **Reduced lock contention**: Reads from view don't compete with writes to base tables
- **Consistent snapshot**: All queries see same data version during refresh interval

### Cons

- **Stale data**: Up to 5-10 minutes old (acceptable per requirements)
- **Storage overhead**: Duplicate data stored in view
- **Refresh time**: With 50M+ projected rows, refresh could take minutes
- **Refresh blocking**: Non-concurrent refresh locks the view
- **Requires UNIQUE index**: For concurrent refresh, needs unique constraint
- **Write amplification**: Every base table write eventually causes view refresh

### When to Use

- Read:write ratio is very high (100:1 or more)
- Query performance still insufficient after normalization
- Staleness acceptable (gallery browsing use case)
- Database has spare storage capacity
- Can schedule refreshes during low-traffic periods

### Performance Estimates

- **Query time reduction**: 70-85% vs current UNION approach
- **Refresh time**: ~30-60 seconds for 1M rows, could be 5-10 minutes for 50M rows
- **Storage overhead**: ~100% (duplicate of base tables)

### Implementation Checklist

- [ ] Create materialized view with UNION of both content tables
- [ ] Add GIN index on tags column
- [ ] Add btree indexes on creator_id and created_at
- [ ] Add UNIQUE index on (source_type, id) for concurrent refresh
- [ ] Test refresh time with current data volume
- [ ] Project refresh time for target scale (50M rows)
- [ ] Set up scheduled refresh job (every 5-10 minutes)
- [ ] Update service layer to query view instead of base tables
- [ ] Monitor view staleness and refresh performance
- [ ] Document view maintenance in docs/db.md

## Option 4: Redis Caching Layer

### Overview

Cache query results in Redis with LRU eviction. Provides dramatic speedup for repeated queries without changing database schema.

### Implementation

#### Cache Key Generation

```python
import redis
import hashlib
import json
from typing import Dict, Any, Optional

class ContentCacheManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cache_prefix = "unified_content"
        self.default_ttl = 600  # 10 minutes

    def generate_cache_key(self, params: Dict[str, Any]) -> str:
        """Generate deterministic cache key from query parameters."""
        # Sort keys for deterministic hashing
        normalized = {
            'page': params.get('page', 1),
            'page_size': params.get('page_size', 25),
            'user_id': str(params.get('user_id', '')),
            'tags': sorted(params.get('tags', [])),
            'content_source_types': sorted(params.get('content_source_types', [])),
            'sort_field': params.get('sort_field', 'created_at'),
            'sort_order': params.get('sort_order', 'desc'),
            'search_term': params.get('search_term', ''),
        }

        # Create hash of parameters
        params_json = json.dumps(normalized, sort_keys=True)
        params_hash = hashlib.md5(params_json.encode()).hexdigest()

        return f"{self.cache_prefix}:{params_hash}"

    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached query result."""
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        return None

    def cache_result(self, cache_key: str, result: Dict[str, Any], ttl: Optional[int] = None):
        """Cache query result with TTL."""
        if ttl is None:
            ttl = self.default_ttl

        self.redis.setex(
            cache_key,
            ttl,
            json.dumps(result)
        )

    def invalidate_pattern(self, pattern: str):
        """Invalidate all cache keys matching pattern."""
        keys = self.redis.keys(f"{self.cache_prefix}:{pattern}*")
        if keys:
            self.redis.delete(*keys)
```

#### Service Layer Integration

```python
class ContentService:
    def __init__(self, db: Session, cache_manager: ContentCacheManager):
        self.db = db
        self.cache = cache_manager
        # ...

    def get_unified_content_paginated(
        self,
        pagination: PaginationRequest,
        content_types: Optional[List[str]] = None,
        creator_filter: str = "all",
        content_source_types: Optional[List[str]] = None,
        user_id: Optional[UUID] = None,
        search_term: Optional[str] = None,
        sort_field: str = "created_at",
        sort_order: str = "desc",
        tags: Optional[List[str]] = None,
        tag_match: str = "any",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Get paginated content with optional caching."""

        # Generate cache key
        cache_key = self.cache.generate_cache_key({
            'page': pagination.page,
            'page_size': pagination.page_size,
            'user_id': user_id,
            'tags': tags,
            'content_source_types': content_source_types,
            'sort_field': sort_field,
            'sort_order': sort_order,
            'search_term': search_term,
        })

        # Try cache first
        if use_cache:
            cached_result = self.cache.get_cached_result(cache_key)
            if cached_result:
                # Add cache metadata
                cached_result['_from_cache'] = True
                return cached_result

        # Execute database query (existing logic)
        result = self._execute_unified_query(
            pagination, content_types, creator_filter,
            content_source_types, user_id, search_term,
            sort_field, sort_order, tags, tag_match
        )

        # Cache result
        if use_cache:
            # Use longer TTL for tag-filtered queries (less volatile)
            ttl = 600 if tags else 300  # 10 min for tag queries, 5 min otherwise
            self.cache.cache_result(cache_key, result, ttl=ttl)
            result['_from_cache'] = False

        return result
```

#### Cache Invalidation

```python
class ContentService:
    def create_content(self, content_data: Dict[str, Any]) -> Any:
        """Create content and invalidate relevant caches."""
        content_item = self.repository.create(content_data)

        # Invalidate caches that might include this new content
        creator_id = content_data.get('creator_id')
        if creator_id:
            # Invalidate all caches for this user
            self.cache.invalidate_pattern(f"*user_id:{creator_id}*")

        # Invalidate "all content" caches
        self.cache.invalidate_pattern("*creator_filter:all*")

        return content_item

    def update_content(self, content_id: int, update_data: Dict[str, Any]) -> Any:
        """Update content and invalidate relevant caches."""
        content = self.repository.update(content_id, update_data)

        # Invalidate all caches (conservative approach)
        # Could be more targeted based on what changed
        self.cache.invalidate_pattern("*")

        return content

    def delete_content(self, content_id: int) -> bool:
        """Delete content and invalidate relevant caches."""
        result = self.repository.delete(content_id)

        # Invalidate all caches
        self.cache.invalidate_pattern("*")

        return result
```

### Cache Invalidation Strategies

#### Strategy 1: Time-Based (Simplest)

- TTL of 5-10 minutes for all queries
- No explicit invalidation on writes
- Acceptable staleness for gallery browsing

**Pros**: Simple, no coordination needed
**Cons**: Stale data for full TTL duration

#### Strategy 2: Event-Based (Recommended)

- Invalidate on content create/update/delete
- Targeted invalidation by user_id or tags
- Still use TTL as safety net

**Pros**: Fresher data, efficient
**Cons**: More complex, requires careful invalidation logic

#### Strategy 3: Hybrid (Best)

- Use event-based invalidation for user-specific caches
- Use time-based expiration for community/aggregate queries
- Different TTLs based on query type:
  - User-only queries: 5 minutes
  - Tag-filtered queries: 10 minutes
  - Community queries: 10 minutes

### Checking Cache Age

Per requirements, document how to check cache age in docs/db.md:

```python
# Add timestamp to cached data
def cache_result(self, cache_key: str, result: Dict[str, Any], ttl: Optional[int] = None):
    """Cache query result with TTL and timestamp."""
    result['_cached_at'] = datetime.utcnow().isoformat()
    result['_cache_ttl'] = ttl or self.default_ttl

    self.redis.setex(
        cache_key,
        ttl or self.default_ttl,
        json.dumps(result)
    )

# Client can check age
def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached query result with age information."""
    cached = self.redis.get(cache_key)
    if cached:
        result = json.loads(cached)

        # Calculate age if timestamp present
        if '_cached_at' in result:
            cached_at = datetime.fromisoformat(result['_cached_at'])
            age_seconds = (datetime.utcnow() - cached_at).total_seconds()
            result['_cache_age_seconds'] = age_seconds

        return result
    return None
```

### Monitoring and Metrics

```python
class ContentCacheManager:
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache hit/miss statistics."""
        keys = self.redis.keys(f"{self.cache_prefix}:*")

        stats = {
            'total_keys': len(keys),
            'memory_usage_bytes': sum(
                self.redis.memory_usage(key) or 0
                for key in keys
            ),
        }

        # If using Redis INFO stats
        info = self.redis.info('stats')
        stats.update({
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'hit_rate': info.get('keyspace_hits', 0) /
                       (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)),
        })

        return stats
```

### Pros

- **Dramatic speedup**: 95%+ reduction for cache hits
- **Reduces database load**: Fewer queries hitting PostgreSQL
- **No schema changes**: Works with existing database structure
- **Flexible TTLs**: Different expiration times per query type
- **Easy to implement**: Minimal code changes
- **Easy to disable**: Can turn off caching if issues arise

### Cons

- **Stale data**: Up to 5-10 minutes old (acceptable per requirements)
- **Memory overhead**: Redis memory for cached results
- **Cache miss penalty**: First request still slow
- **Invalidation complexity**: Need careful logic to invalidate correctly
- **Cold start issues**: Empty cache after restart
- **Doesn't fix root cause**: Underlying query still slow

### When to Use

- High query repetition (same filters used frequently)
- Gallery browsing patterns predictable
- Acceptable staleness (5-10 minutes confirmed acceptable)
- Want quick wins without schema changes
- Complement to normalization, not replacement

### Performance Estimates

- **Cache hit**: < 10ms response time (95%+ reduction)
- **Cache miss**: Same as uncached query (no improvement)
- **Expected hit rate**: 60-80% for typical gallery usage
- **Memory usage**: ~1-2KB per cached result, ~10MB for 5000 cached queries

### Redis Configuration

```python
# config/base.json
{
  "redis-host": "localhost",
  "redis-port": 6379,
  "redis-db": 1,  # Use different DB than Celery (DB 0)
  "redis-max-memory": "256mb",
  "redis-eviction-policy": "allkeys-lru"
}
```

### Implementation Checklist

- [ ] Create ContentCacheManager class
- [ ] Implement cache key generation
- [ ] Add timestamp and age tracking to cached results
- [ ] Integrate into ContentService.get_unified_content_paginated
- [ ] Implement cache invalidation in create/update/delete methods
- [ ] Add cache statistics endpoint
- [ ] Configure Redis connection (separate DB from Celery)
- [ ] Set up LRU eviction policy in Redis
- [ ] Monitor cache hit rates
- [ ] Document cache age checking in docs/db.md
- [ ] Add tests for caching logic
- [ ] Load test with cache enabled/disabled

## Combining Both Options

For maximum performance, both options can be used together:

1. **Materialized view** provides fast base queries (70-85% improvement)
2. **Redis caching** eliminates even that overhead for repeated queries (95%+ improvement on hits)

This two-tier approach:
- Materialized view: Refreshed every 5-10 minutes
- Redis cache: 5-10 minute TTL, invalidated on writes
- Net result: Most queries hit Redis cache (<10ms), cache misses hit fast materialized view (still fast), only view refresh hits base tables

**Trade-offs**:
- Maximum performance
- Maximum complexity
- Most stale data (but acceptable per requirements)
- Highest resource usage (storage + memory)

**When to use both**:
- After normalization still insufficient
- Extremely high read load (1000+ req/sec)
- Scale reaches upper projections (50M+ rows)
- Performance critical and staleness acceptable

## Recommendations

### Phase 1 (Current)
- Implement tag normalization (Option 3)
- Implement query optimization (Option 5)
- Benchmark results

### Phase 2 (If Needed)
- If performance targets met: DONE
- If p99 > 5s but p95 OK: Implement Redis caching (Option 4)
- If p95 > 3s: Consider materialized view (Option 2)

### Phase 3 (Future Scale)
- When approaching 10M+ rows: Re-evaluate need for materialized view
- When approaching 50M+ rows: Likely need both caching and materialized view

## Documentation Requirements

When implementing these options, update the following:

- **docs/db.md**:
  - Document materialized view refresh schedule
  - Document cache age checking procedures
  - Document cache invalidation strategy

- **docs/api.md**:
  - Document cache behavior in API responses
  - Document `_from_cache` and `_cache_age_seconds` fields
  - Document when caching can be bypassed

- **docs/configuration.md**:
  - Document Redis configuration options
  - Document cache TTL settings
  - Document materialized view refresh settings

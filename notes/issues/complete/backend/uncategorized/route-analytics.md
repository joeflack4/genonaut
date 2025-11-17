## Route analytics
We should improve analytics. what's the best way to store all previous backend routes hit? 1 pg table? redis? external
piece of software? 3rd party service? basically i want to know what was hit, at what time, by what user, and what time 
it happened, and how long it took for the backend to handle the request. 

Perhaps there are also more fields that we should be collecting. Context: We'll use this to determine what Redis will 
cache, as a function of frequency and time taken to serve. But maybe there a general algorithm / heuristic like for 
choosing what to cache? Maybe we should consider that, if so.

First, just think about this, and make a report of your recommendations here in the "Reports" section. Let us know what 
your number one recommendation is, if you have one.

When you actually go about working on this, follow the SOP in `.claude/commands/new-big-task.md`.

## Phase 5 Implementation Notes

If implementing Phase 5 API endpoints, follow this pattern from existing routes:

**Create `genonaut/api/routes/analytics.py`:**
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from genonaut.api.dependencies import get_database_session

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/routes/cache-priorities")
async def get_cache_priorities(
    n: int = Query(10, description="Number of routes to return"),
    days: int = Query(7, description="Days of history to analyze"),
    db: Session = Depends(get_database_session)
):
    """Get top N routes recommended for caching (wraps CLI logic)."""
    # Import and call get_top_routes_for_caching() from CLI
    # Return JSON response
```

**Register router in `genonaut/api/main.py`:**
```python
from genonaut.api.routes import analytics
app.include_router(analytics.router)
```

**Reuse CLI logic:** The CLI tools already have all the business logic. API endpoints can simply import and call the CLI functions, then return the results as JSON.

## Reports

### Analysis and Recommendations

#### Current State
The project currently has:
1. **MetricsService** (genonaut/api/services/metrics_service.py:22) - In-memory metrics tracking for ComfyUI operations and some performance data, limited to 1000 entries, data lost on restart
2. **PerformanceTimingMiddleware** (genonaut/api/middleware/performance_timing.py:12) - Logs timing for specific endpoints to console, no persistence
3. **Infrastructure**: PostgreSQL (demo/dev/test), Redis (for Celery), Celery workers, FastAPI

#### Storage Options Evaluated

**Option 1: PostgreSQL Table**
- Pros: Persistent, excellent for analytics, ACID guarantees, already have infrastructure, powerful query capabilities
- Cons: Write overhead per request, need careful implementation to avoid performance impact, table growth management

**Option 2: Redis Only**
- Pros: Very fast writes, already have Redis, low latency, good for real-time metrics
- Cons: Memory-based (limited capacity), difficult complex analytics, long-term storage issues, data persistence risks

**Option 3: Hybrid (PostgreSQL + Redis)**
- Pros: Fast writes to Redis, long-term storage in PostgreSQL, best of both worlds, background processing via Celery
- Cons: Added complexity, maintaining two systems

**Option 4: External Software (ELK, Prometheus, etc.)**
- Pros: Purpose-built, rich features, battle-tested
- Cons: Additional infrastructure, learning curve, may be overkill

**Option 5: 3rd Party SaaS (DataDog, New Relic, etc.)**
- Pros: No maintenance, professional tooling
- Cons: Ongoing costs, data leaves infrastructure, less control

#### Primary Recommendation: Hybrid Approach (PostgreSQL + Redis)

**Why this is the best choice:**
1. **Performance**: Fast, non-blocking writes to Redis (< 1ms overhead)
2. **Analytics Power**: PostgreSQL enables complex queries for cache planning algorithms
3. **Infrastructure Ready**: Both systems already running in the project
4. **Cost Effective**: No additional services or infrastructure needed
5. **Scalable**: Can handle high request volumes with minimal impact
6. **Background Processing**: Leverage existing Celery workers for data transfer

#### Implementation Design

**1. Data Model**
```python
{
    "route": "/api/v1/content/unified",        # API endpoint path (base route)
    "method": "GET",                           # HTTP method
    "user_id": "uuid-string",                  # User making request
    "timestamp": "2025-01-15T10:30:45.123Z",  # When request occurred
    "duration_ms": 142,                        # Response time in milliseconds
    "status_code": 200,                        # HTTP status code
    "query_params": {                          # Full query parameters
        "page": "1",
        "page_size": "10",
        "sort": "created_at"
    },
    "query_params_normalized": {               # Normalized params (for grouping)
        "page_size": "10",                     # Pagination values excluded
        "sort": "created_at"
    },
    "request_size_bytes": 1234,               # Request payload size
    "response_size_bytes": 5678,              # Response payload size
    "error_type": null,                        # Error type if failed
    "db_query_count": 3,                       # Number of DB queries made
    "cache_status": "miss"                     # Cache hit/miss (future use)
}
```

**2. PostgreSQL Schema**

**Raw Events Table** (individual requests):
```sql
CREATE TABLE route_analytics (
    id BIGSERIAL PRIMARY KEY,
    route TEXT NOT NULL,                           -- Base route (e.g., /api/v1/content/unified)
    method VARCHAR(10) NOT NULL,
    user_id UUID REFERENCES users(id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_ms INTEGER NOT NULL,
    status_code SMALLINT NOT NULL,
    query_params JSONB,                            -- Full query params
    query_params_normalized JSONB,                 -- Normalized params (for grouping)
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    error_type TEXT,
    db_query_count INTEGER,
    cache_status VARCHAR(10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX idx_route_analytics_timestamp ON route_analytics(timestamp DESC);
CREATE INDEX idx_route_analytics_route_time ON route_analytics(route, timestamp DESC);
CREATE INDEX idx_route_analytics_user_time ON route_analytics(user_id, timestamp DESC);
CREATE INDEX idx_route_analytics_duration ON route_analytics(duration_ms DESC);

-- Consider partitioning by timestamp for large-scale deployments
-- CREATE TABLE route_analytics_2025_01 PARTITION OF route_analytics
--     FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

**Aggregated Hourly Table** (time-series statistics for cache planning):
```sql
-- Pre-aggregated hourly metrics for fast cache planning queries
-- Each row represents one hour's statistics for a specific route
CREATE TABLE route_analytics_hourly (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,           -- Hour bucket (e.g., 2025-01-15 10:00:00)
    route TEXT NOT NULL,
    method VARCHAR(10) NOT NULL,
    query_params_normalized JSONB,            -- Normalized params for this pattern
    total_requests INTEGER NOT NULL,          -- Total requests in this hour
    successful_requests INTEGER NOT NULL,     -- 2xx status codes
    client_errors INTEGER NOT NULL,           -- 4xx status codes
    server_errors INTEGER NOT NULL,           -- 5xx status codes
    avg_duration_ms INTEGER,                  -- Average response time
    p50_duration_ms INTEGER,                  -- Median response time
    p95_duration_ms INTEGER,                  -- 95th percentile
    p99_duration_ms INTEGER,                  -- 99th percentile
    unique_users INTEGER,                     -- Distinct users this hour
    avg_request_size_bytes INTEGER,
    avg_response_size_bytes INTEGER,
    avg_db_query_count FLOAT,                 -- Average DB queries per request
    cache_hits INTEGER DEFAULT 0,             -- For future caching
    cache_misses INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(timestamp, route, method, query_params_normalized)
);

CREATE INDEX idx_route_metrics_timestamp ON route_analytics_hourly(timestamp DESC);
CREATE INDEX idx_route_metrics_route_time ON route_analytics_hourly(route, timestamp DESC);
CREATE INDEX idx_route_metrics_total_requests ON route_analytics_hourly(total_requests DESC);
CREATE INDEX idx_route_metrics_duration ON route_analytics_hourly(avg_duration_ms DESC);

-- This table enables fast queries like:
-- "Show me the top 10 slowest routes over the last 7 days"
-- "Which routes have the highest traffic during peak hours?"
-- "What's the cache priority score for each endpoint?"
```

**3. FastAPI Middleware Implementation**
- Create `RouteAnalyticsMiddleware` in `genonaut/api/middleware/route_analytics.py`
- Capture request start time before processing
- Write to Redis asynchronously after response sent
- Use Redis Streams for ordered, persistent storage
- Minimal performance impact (< 1ms per request)

**4. Redis Storage Strategy**
- Use Redis Streams: `XADD route_analytics:stream * field1 value1 field2 value2 ...`
- Keep last 2 hours of data in Redis for real-time queries
- Stream entries automatically timestamped
- Consumer group pattern for reliable transfer to PostgreSQL

**5. Celery Background Tasks**

**Task 1: Transfer Raw Events (every 10 minutes)**
- Transfer raw events from Redis -> route_analytics table
- Use `XREAD` to consume from Redis Stream
- Batch insert to PostgreSQL (1000 records at a time)
- Trim old Redis data with `XTRIM` after successful transfer
- Handle failures gracefully (retry logic, dead letter queue)

**Task 2: Aggregate Hourly Metrics (hourly)**
- Calculate statistics from route_analytics for the previous hour
- Insert into route_analytics_hourly table
- Calculate: avg, p50, p95, p99 durations, unique users, error rates
- Use `ON CONFLICT (timestamp, route, method) DO UPDATE` for idempotency
- Example aggregation query:
```sql
INSERT INTO route_analytics_hourly (
    timestamp, route, method, query_params_normalized, total_requests, successful_requests,
    client_errors, server_errors, avg_duration_ms, p50_duration_ms,
    p95_duration_ms, p99_duration_ms, unique_users
)
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    route,
    method,
    query_params_normalized,
    COUNT(*) as total_requests,
    SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as successful_requests,
    SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END) as client_errors,
    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as server_errors,
    AVG(duration_ms)::INTEGER as avg_duration_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p50_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p95_duration_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p99_duration_ms,
    COUNT(DISTINCT user_id) as unique_users
FROM route_analytics
WHERE timestamp >= DATE_TRUNC('hour', NOW() - INTERVAL '1 hour')
    AND timestamp < DATE_TRUNC('hour', NOW())
GROUP BY hour, route, method, query_params_normalized
ON CONFLICT (timestamp, route, method, query_params_normalized) DO UPDATE SET
    total_requests = EXCLUDED.total_requests,
    avg_duration_ms = EXCLUDED.avg_duration_ms,
    p95_duration_ms = EXCLUDED.p95_duration_ms;
```

**6. Cache Planning Algorithm**
Based on collected data, implement analysis that considers:
- **Frequency**: requests per minute/hour for each endpoint
- **Response Time**: avg, p50, p95, p99 latency per endpoint
- **User Distribution**: unique users hitting each endpoint
- **Time Patterns**: hourly/daily access patterns
- **Cache Effectiveness**: estimate cache hit rate and savings

**Cache Priority Query** (uses hourly aggregated data):
```sql
-- Find routes that should be cached based on frequency + latency
-- Query last 7 days of hourly data for patterns
SELECT
    route,
    method,
    AVG(total_requests) as avg_hourly_requests,
    AVG(p95_duration_ms) as avg_p95_latency,
    AVG(unique_users) as avg_unique_users,
    -- Cache priority score: high frequency * high latency
    (AVG(total_requests) * AVG(p95_duration_ms))::BIGINT as cache_priority_score
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY route, method
HAVING AVG(total_requests) > 100      -- Frequent enough to cache
    AND AVG(p95_duration_ms) > 200    -- Slow enough to benefit
ORDER BY cache_priority_score DESC
LIMIT 20;
```

**Peak Hours Analysis** (identify when to cache more aggressively):
```sql
-- Identify peak traffic hours per route
SELECT
    route,
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    AVG(total_requests) as avg_requests,
    AVG(p95_duration_ms) as avg_latency
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY route, hour_of_day
HAVING AVG(total_requests) > 50
ORDER BY route, avg_requests DESC;
```

**Example cache priority calculation in Python:**
```python
def calculate_cache_priority(route_stats):
    # Higher frequency = higher priority
    frequency_score = route_stats.avg_hourly_requests * 10

    # Slower endpoints benefit more from caching
    latency_score = route_stats.avg_p95_duration_ms / 100

    # Wide user distribution = better cache reuse
    user_diversity_score = min(route_stats.avg_unique_users / 10, 10)

    # Combine scores
    return frequency_score + latency_score + user_diversity_score

# Automatic cache decision
def should_cache_route(route_stats):
    priority = calculate_cache_priority(route_stats)
    return priority > 50  # Threshold for caching
```

**7. Query Parameter Handling Strategy**

**The Challenge:**
Routes like `/api/v1/content/unified` can have many query parameter combinations:
- `?page=1&page_size=10&sort=created_at`
- `?page=2&page_size=10&sort=created_at`
- `?page=1&page_size=50&sort=title`
- Potentially thousands of unique combinations

**Decision Required: How to handle query parameters?**

**Recommended Approach: Smart Normalization**

Store both normalized route and full route with params:
```python
{
    "route": "/api/v1/content/unified",          # Base route (normalized)
    "route_full": "/api/v1/content/unified?page=1&page_size=10&sort=created_at",
    "query_params": {
        "page": "1",
        "page_size": "10",
        "sort": "created_at"
    },
    "query_params_normalized": {                  # For grouping similar requests
        "page_size": "10",
        "sort": "created_at"
        # Omit 'page' - it varies but pattern is same
    }
}
```

**Normalization rules:**
1. **Pagination params** (page, offset) - Omit from normalized version (they vary but pattern is same)
2. **Filtering params** (sort, filter, content_types) - Include in normalized version (these define distinct query patterns)
3. **User-specific params** (user_id in URL) - Keep in base route

**Benefits:**
- Can identify "page_size=10 with sort=created_at gets 80% of traffic"
- Can decide to cache first N pages of popular combinations
- Can group similar requests for better cache hit rates

**Implementation in middleware:**
```python
def normalize_query_params(route: str, query_params: dict) -> tuple:
    """Normalize query params for cache analysis.

    Returns:
        (base_route, normalized_params, full_route)
    """
    # Params to exclude from normalization (vary within same pattern)
    variable_params = {'page', 'offset', 'limit', 'cursor'}

    # Create normalized version without variable params
    normalized = {
        k: v for k, v in query_params.items()
        if k not in variable_params
    }

    base_route = route.split('?')[0]
    full_route = f"{base_route}?{urlencode(query_params)}" if query_params else base_route

    return base_route, normalized, full_route
```

**Cache decision example:**
```sql
-- Find popular query patterns for a route
SELECT
    route,
    query_params_normalized,
    SUM(total_requests) as total_requests,
    AVG(avg_duration_ms) as avg_duration
FROM route_analytics_hourly
WHERE route = '/api/v1/content/unified'
    AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY route, query_params_normalized
ORDER BY total_requests DESC
LIMIT 5;

-- Result might show:
-- {'page_size': '10', 'sort': 'created_at'} - 50K requests
-- {'page_size': '50', 'sort': 'created_at'} - 15K requests
-- Cache decision: Cache first 3 pages of top 2 combinations
```

**8. CLI Tool for Cache Analysis**

**Purpose:** Analyze route analytics data and identify top N routes to cache.

**Location:** `genonaut/cli/cache_analysis.py`

**Usage:**
```bash
# Get top 10 routes to cache
make cache-analysis n=10

# Get top 20 routes, looking at last 7 days
make cache-analysis n=20 days=7

# Output as JSON for programmatic consumption
make cache-analysis n=10 format=json
```

**Implementation:**
```python
#!/usr/bin/env python3
"""CLI tool for analyzing route analytics and recommending cache targets."""

import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tabulate import tabulate
from sqlalchemy import text

from genonaut.db import get_db_session
from genonaut.api.config import get_settings


def calculate_cache_priority_score(row: Dict[str, Any]) -> float:
    """Calculate cache priority score for a route.

    Higher score = higher priority for caching.

    Args:
        row: Route statistics from route_analytics_hourly

    Returns:
        Priority score (0-10000+)
    """
    # Extract metrics
    avg_requests = row['avg_hourly_requests']
    avg_p95_latency = row['avg_p95_latency']
    unique_users = row['avg_unique_users']

    # Component scores
    frequency_score = avg_requests * 10          # High traffic = higher priority
    latency_score = avg_p95_latency / 100        # Slow queries = higher benefit
    user_diversity_score = min(unique_users / 10, 10)  # More users = better cache reuse

    # Combined priority score
    return frequency_score + latency_score + user_diversity_score


def get_top_routes_for_caching(
    n: int = 10,
    lookback_days: int = 7,
    min_requests_per_hour: int = 10,
    min_latency_ms: int = 100
) -> List[Dict[str, Any]]:
    """Get top N routes that should be cached.

    Args:
        n: Number of top routes to return
        lookback_days: Days of historical data to analyze
        min_requests_per_hour: Minimum average requests/hour to consider
        min_latency_ms: Minimum p95 latency to benefit from caching

    Returns:
        List of route statistics with cache priority scores
    """
    settings = get_settings()

    query = text("""
        SELECT
            route,
            method,
            query_params_normalized,
            AVG(total_requests) as avg_hourly_requests,
            AVG(p95_duration_ms) as avg_p95_latency,
            AVG(p99_duration_ms) as avg_p99_latency,
            AVG(unique_users) as avg_unique_users,
            SUM(total_requests) as total_requests,
            AVG(successful_requests::FLOAT / NULLIF(total_requests, 0)) as success_rate
        FROM route_analytics_hourly
        WHERE timestamp > NOW() - INTERVAL :lookback_days DAY
        GROUP BY route, method, query_params_normalized
        HAVING AVG(total_requests) >= :min_requests_per_hour
            AND AVG(p95_duration_ms) >= :min_latency_ms
        ORDER BY AVG(total_requests) * AVG(p95_duration_ms) DESC
        LIMIT :limit
    """)

    with get_db_session() as session:
        result = session.execute(query, {
            'lookback_days': lookback_days,
            'min_requests_per_hour': min_requests_per_hour,
            'min_latency_ms': min_latency_ms,
            'limit': n * 2  # Get more, then filter by priority
        })

        routes = []
        for row in result:
            row_dict = dict(row._mapping)
            row_dict['cache_priority_score'] = calculate_cache_priority_score(row_dict)
            routes.append(row_dict)

    # Sort by priority score and return top N
    routes.sort(key=lambda x: x['cache_priority_score'], reverse=True)
    return routes[:n]


def format_output_table(routes: List[Dict[str, Any]]) -> str:
    """Format routes as human-readable table."""
    table_data = []
    for i, route in enumerate(routes, 1):
        params_str = json.dumps(route.get('query_params_normalized') or {})
        if len(params_str) > 40:
            params_str = params_str[:37] + "..."

        table_data.append([
            i,
            route['method'],
            route['route'],
            params_str,
            f"{route['avg_hourly_requests']:.0f}",
            f"{route['avg_p95_latency']:.0f}ms",
            f"{route['avg_unique_users']:.0f}",
            f"{route['cache_priority_score']:.1f}",
            f"{route['success_rate']*100:.1f}%"
        ])

    headers = [
        "Rank", "Method", "Route", "Normalized Params",
        "Avg Req/Hr", "P95 Latency", "Unique Users", "Priority Score", "Success Rate"
    ]

    return tabulate(table_data, headers=headers, tablefmt="grid")


def format_output_json(routes: List[Dict[str, Any]]) -> str:
    """Format routes as JSON for programmatic consumption."""
    # Convert to JSON-serializable format
    output = []
    for route in routes:
        output.append({
            'route': route['route'],
            'method': route['method'],
            'query_params_normalized': route.get('query_params_normalized'),
            'avg_hourly_requests': float(route['avg_hourly_requests']),
            'avg_p95_latency_ms': float(route['avg_p95_latency']),
            'avg_unique_users': float(route['avg_unique_users']),
            'cache_priority_score': float(route['cache_priority_score']),
            'success_rate': float(route['success_rate']),
            'total_requests': int(route['total_requests'])
        })

    return json.dumps(output, indent=2)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze route analytics and identify top routes to cache"
    )
    parser.add_argument(
        '-n', '--count',
        type=int,
        default=10,
        help="Number of top routes to return (default: 10)"
    )
    parser.add_argument(
        '-d', '--days',
        type=int,
        default=7,
        help="Days of historical data to analyze (default: 7)"
    )
    parser.add_argument(
        '-f', '--format',
        choices=['table', 'json'],
        default='table',
        help="Output format (default: table)"
    )
    parser.add_argument(
        '--min-requests',
        type=int,
        default=10,
        help="Minimum avg requests/hour to consider (default: 10)"
    )
    parser.add_argument(
        '--min-latency',
        type=int,
        default=100,
        help="Minimum p95 latency in ms to benefit from caching (default: 100)"
    )

    args = parser.parse_args()

    print(f"Analyzing route analytics (last {args.days} days)...")
    print(f"Filters: min {args.min_requests} req/hr, min {args.min_latency}ms latency\n")

    routes = get_top_routes_for_caching(
        n=args.count,
        lookback_days=args.days,
        min_requests_per_hour=args.min_requests,
        min_latency_ms=args.min_latency
    )

    if not routes:
        print("No routes found matching criteria.")
        return

    print(f"Top {len(routes)} routes recommended for caching:\n")

    if args.format == 'json':
        print(format_output_json(routes))
    else:
        print(format_output_table(routes))
        print(f"\nTotal routes analyzed: {len(routes)}")
        print(f"Use --format=json for machine-readable output")


if __name__ == '__main__':
    main()
```

**Makefile command:**
```makefile
# Cache analysis
.PHONY: cache-analysis
cache-analysis:
	@ENV_TARGET=local-demo python -m genonaut.cli.cache_analysis \
		--count=$(or $(n),10) \
		--days=$(or $(days),7) \
		--format=$(or $(format),table)
```

**Example output (table format):**
```
Top 10 routes recommended for caching:

+------+--------+------------------------------+-------------------------+-----------+-------------+--------------+----------------+--------------+
| Rank | Method | Route                        | Normalized Params       | Avg Req/Hr| P95 Latency | Unique Users | Priority Score | Success Rate |
+======+========+==============================+=========================+===========+=============+==============+================+==============+
|    1 | GET    | /api/v1/content/unified      | {"page_size": "10", ... | 2,450     | 189ms       | 45           | 24,559.4       | 98.5%        |
|    2 | GET    | /api/v1/tags/hierarchy       | {}                      | 890       | 156ms       | 32           | 9,076.2        | 99.1%        |
|    3 | GET    | /api/v1/content/{id}         | {}                      | 1,200     | 95ms        | 67           | 12,156.7       | 97.8%        |
+------+--------+------------------------------+-------------------------+-----------+-------------+--------------+----------------+--------------+
```

**Example output (JSON format):**
```json
[
  {
    "route": "/api/v1/content/unified",
    "method": "GET",
    "query_params_normalized": {"page_size": "10", "sort": "created_at"},
    "avg_hourly_requests": 2450.0,
    "avg_p95_latency_ms": 189.0,
    "avg_unique_users": 45.0,
    "cache_priority_score": 24559.4,
    "success_rate": 0.985,
    "total_requests": 411600
  }
]
```

**9. CLI Tool for Relative Cache Analysis (System 2)**

**Purpose:** Rank routes by RELATIVE popularity and latency, ideal for development environments with low/sporadic traffic.

**Location:** `genonaut/cli/cache_analysis_relative.py`

**Usage:**
```bash
# Get top 10 routes using relative ranking
make cache-analysis-relative n=10

# Get top 20 routes, looking at last 7 days
make cache-analysis-relative n=20 days=7

# Output as JSON
make cache-analysis-relative n=10 format=json
```

**How it differs from System 1:**
- **No absolute thresholds** - considers all routes with any traffic
- **Percentile-based ranking** - compares each route to the distribution of all routes
- **Better for dev** - works even with 1-2 requests per day

**Implementation:**
```python
#!/usr/bin/env python3
"""CLI tool for relative cache priority analysis (development-friendly)."""

import argparse
import json
from typing import List, Dict, Any
import numpy as np
from tabulate import tabulate
from sqlalchemy import text

from genonaut.db import get_db_session
from genonaut.api.config import get_settings


def calculate_relative_priority_score(
    row: Dict[str, Any],
    stats: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate relative cache priority based on percentiles.

    Args:
        row: Route statistics from route_analytics_hourly
        stats: Distribution statistics for all routes

    Returns:
        Dict with priority score and component scores
    """
    # Extract route metrics
    avg_requests = row['avg_hourly_requests']
    avg_p95_latency = row['avg_p95_latency']
    unique_users = row['avg_unique_users']

    # Calculate percentiles (0-100)
    # Higher percentile = more important
    popularity_percentile = _calculate_percentile(
        avg_requests,
        stats['request_distribution']
    )

    latency_percentile = _calculate_percentile(
        avg_p95_latency,
        stats['latency_distribution']
    )

    user_percentile = _calculate_percentile(
        unique_users,
        stats['user_distribution']
    )

    # Combined score: weighted average of percentiles
    # Latency gets 40%, popularity 40%, user diversity 20%
    priority_score = (
        (latency_percentile * 0.4) +
        (popularity_percentile * 0.4) +
        (user_percentile * 0.2)
    )

    return {
        'priority_score': priority_score,
        'popularity_percentile': popularity_percentile,
        'latency_percentile': latency_percentile,
        'user_percentile': user_percentile
    }


def _calculate_percentile(value: float, distribution: List[float]) -> float:
    """Calculate what percentile this value is in the distribution."""
    if not distribution:
        return 50.0  # Default to median if no distribution

    # Use numpy for percentile calculation
    percentile = (np.searchsorted(sorted(distribution), value, side='right') /
                  len(distribution)) * 100

    return min(100.0, max(0.0, percentile))


def get_top_routes_relative(
    n: int = 10,
    lookback_days: int = 7
) -> List[Dict[str, Any]]:
    """Get top N routes using relative ranking.

    No absolute thresholds - ranks ALL routes by relative importance.

    Args:
        n: Number of top routes to return
        lookback_days: Days of historical data to analyze

    Returns:
        List of route statistics with relative priority scores
    """
    query = text("""
        SELECT
            route,
            method,
            query_params_normalized,
            AVG(total_requests) as avg_hourly_requests,
            AVG(p95_duration_ms) as avg_p95_latency,
            AVG(p99_duration_ms) as avg_p99_latency,
            AVG(unique_users) as avg_unique_users,
            SUM(total_requests) as total_requests,
            AVG(successful_requests::FLOAT / NULLIF(total_requests, 0)) as success_rate
        FROM route_analytics_hourly
        WHERE timestamp > NOW() - INTERVAL :lookback_days DAY
        GROUP BY route, method, query_params_normalized
        HAVING AVG(total_requests) > 0  -- At least some traffic
    """)

    with get_db_session() as session:
        result = session.execute(query, {'lookback_days': lookback_days})

        routes = []
        request_dist = []
        latency_dist = []
        user_dist = []

        # First pass: collect all routes and build distributions
        for row in result:
            row_dict = dict(row._mapping)
            routes.append(row_dict)
            request_dist.append(row_dict['avg_hourly_requests'])
            latency_dist.append(row_dict['avg_p95_latency'])
            user_dist.append(row_dict['avg_unique_users'])

        # Build distribution stats
        stats = {
            'request_distribution': request_dist,
            'latency_distribution': latency_dist,
            'user_distribution': user_dist
        }

        # Second pass: calculate relative scores
        for route in routes:
            scores = calculate_relative_priority_score(route, stats)
            route.update(scores)

    # Sort by priority score and return top N
    routes.sort(key=lambda x: x['priority_score'], reverse=True)
    return routes[:n]


def format_output_table_relative(routes: List[Dict[str, Any]]) -> str:
    """Format routes as human-readable table with percentiles."""
    table_data = []
    for i, route in enumerate(routes, 1):
        params_str = json.dumps(route.get('query_params_normalized') or {})
        if len(params_str) > 35:
            params_str = params_str[:32] + "..."

        table_data.append([
            i,
            route['method'],
            route['route'][:40],  # Truncate long routes
            params_str,
            f"{route['avg_hourly_requests']:.1f}",
            f"{route['avg_p95_latency']:.0f}ms",
            f"{route['priority_score']:.1f}",
            f"P{route['popularity_percentile']:.0f}",
            f"L{route['latency_percentile']:.0f}",
            f"U{route['user_percentile']:.0f}"
        ])

    headers = [
        "Rank", "Method", "Route", "Params",
        "Req/Hr", "P95", "Score", "Pop%", "Lat%", "User%"
    ]

    return tabulate(table_data, headers=headers, tablefmt="grid")


def format_output_json_relative(routes: List[Dict[str, Any]]) -> str:
    """Format routes as JSON with relative scores."""
    output = []
    for route in routes:
        output.append({
            'route': route['route'],
            'method': route['method'],
            'query_params_normalized': route.get('query_params_normalized'),
            'avg_hourly_requests': float(route['avg_hourly_requests']),
            'avg_p95_latency_ms': float(route['avg_p95_latency']),
            'priority_score': float(route['priority_score']),
            'popularity_percentile': float(route['popularity_percentile']),
            'latency_percentile': float(route['latency_percentile']),
            'user_percentile': float(route['user_percentile']),
            'success_rate': float(route['success_rate']),
            'total_requests': int(route['total_requests'])
        })

    return json.dumps(output, indent=2)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze routes using RELATIVE ranking (dev-friendly)"
    )
    parser.add_argument(
        '-n', '--count',
        type=int,
        default=10,
        help="Number of top routes to return (default: 10)"
    )
    parser.add_argument(
        '-d', '--days',
        type=int,
        default=7,
        help="Days of historical data to analyze (default: 7)"
    )
    parser.add_argument(
        '-f', '--format',
        choices=['table', 'json'],
        default='table',
        help="Output format (default: table)"
    )

    args = parser.parse_args()

    print(f"Analyzing routes with RELATIVE ranking (last {args.days} days)...")
    print("No absolute thresholds - comparing all routes to each other\n")

    routes = get_top_routes_relative(
        n=args.count,
        lookback_days=args.days
    )

    if not routes:
        print("No routes found with traffic.")
        return

    print(f"Top {len(routes)} routes by relative importance:\n")

    if args.format == 'json':
        print(format_output_json_relative(routes))
    else:
        print(format_output_table_relative(routes))
        print(f"\nColumns: Pop% (popularity), Lat% (latency), User% (user diversity)")
        print(f"Higher percentile = more important relative to other routes")
        print(f"Use --format=json for machine-readable output")


if __name__ == '__main__':
    main()
```

**Makefile command:**
```makefile
# Relative cache analysis (development-friendly)
.PHONY: cache-analysis-relative
cache-analysis-relative:
	@ENV_TARGET=local-demo python -m genonaut.cli.cache_analysis_relative \
		--count=$(or $(n),10) \
		--days=$(or $(days),7) \
		--format=$(or $(format),table)
```

**Example output:**
```
Top 10 routes by relative importance:

+------+--------+-----------------------------+---------------+--------+--------+-------+------+------+-------+
| Rank | Method | Route                       | Params        | Req/Hr | P95    | Score | Pop% | Lat% | User% |
+======+========+=============================+===============+========+========+=======+======+======+=======+
|    1 | GET    | /api/v1/content/unified     | {"page_si..." | 12.5   | 1850ms | 95.2  | P92  | L98  | U95   |
|    2 | GET    | /api/v1/tags/hierarchy      | {}            | 8.2    | 1560ms | 89.4  | P85  | L94  | U89   |
|    3 | POST   | /api/v1/generation/jobs     | {}            | 3.1    | 5230ms | 87.1  | P65  | L99  | U78   |
+------+--------+-----------------------------+---------------+--------+--------+-------+------+------+-------+

Columns: Pop% (popularity), Lat% (latency), User% (user diversity)
Higher percentile = more important relative to other routes
```

**Key differences:**
- **Pop%**: This route is at 92nd percentile for traffic (busier than 92% of routes)
- **Lat%**: This route is at 98th percentile for latency (slower than 98% of routes)
- **Score**: Weighted combination (latency 40%, popularity 40%, users 20%)

This system will surface slow routes even with low traffic, which is perfect for development!

#### Additional Fields to Consider

**Already Included:**
- route, method, user_id, timestamp, duration_ms, status_code

**Recommended Additions:**
- request_size_bytes - Track payload sizes
- response_size_bytes - Track response sizes
- error_type - Categorize errors for pattern detection
- db_query_count - Identify N+1 queries
- cache_status - Track cache effectiveness (once implemented)

**Future Considerations:**
- ip_address - Geo-distribution analysis
- user_agent - Client type analysis
- referrer - Traffic source tracking
- session_id - Session-based analytics
- trace_id - Distributed tracing integration

#### Migration Path

1. **Phase 1**: Implement middleware and Redis storage
   - Create RouteAnalyticsMiddleware
   - Add Redis Stream writes for raw events
   - Test performance impact (< 1ms overhead)

2. **Phase 2**: Create PostgreSQL schema
   - Add route_analytics table (raw events)
   - Add route_analytics_hourly table (aggregated metrics)
   - Add indexes for query optimization

3. **Phase 3**: Add Celery tasks
   - Task 1: Transfer raw events (every 10 minutes)
   - Task 2: Aggregate hourly metrics (hourly)
   - Add to Celery Beat schedule in config/base.json

4. **Phase 4**: Build analytics queries and dashboards
   - Cache priority queries
   - Peak hours analysis
   - Route performance trends
   - Error rate monitoring

5. **Phase 5**: Implement cache planning algorithm
   - Automated cache decision logic
   - Cache priority scoring
   - Dynamic cache configuration

6. **Phase 6**: Deploy intelligent Redis caching based on analytics
   - Cache high-priority routes
   - Implement cache warming during off-peak hours
   - Monitor cache hit rates and effectiveness

#### Performance Considerations

- Middleware adds < 1ms overhead per request
- Redis writes are async, don't block response
- PostgreSQL writes batched in background
- Indexes optimized for common query patterns
- Consider table partitioning for > 100M rows
- Monitor Redis memory usage, adjust retention as needed

#### Benefits of Hourly Aggregation Table

**Why route_analytics_hourly is critical for cache planning:**

1. **Query Performance**: Scanning millions of raw events is slow. Aggregated hourly data reduces query time from seconds to milliseconds.

2. **Time-Series Analysis**: Each row = one hour of data for a specific route. Easy to see patterns:
   ```
   /api/v1/content/unified on 2025-01-15:
   - 09:00: 450 req/hr, 120ms avg
   - 12:00: 2100 req/hr, 189ms avg  <- Lunch rush, cache needed!
   - 15:00: 890 req/hr, 135ms avg
   ```

3. **Data Reduction**: 100K requests/hour = 1 aggregated row per endpoint. Makes long-term trend analysis feasible.

4. **Cache Decision Support**: Pre-calculated percentiles (p95, p99) essential for cache priority scoring.

5. **Dashboard Ready**: Real-time dashboards can query aggregated data without expensive calculations.

**Example: Without hourly table**
```sql
-- Slow query scanning 10M+ rows
SELECT route, AVG(duration_ms), COUNT(*)
FROM route_analytics
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY route;  -- Takes 5-10 seconds
```

**With hourly table:**
```sql
-- Fast query on 20K aggregated rows
SELECT route, AVG(avg_duration_ms), SUM(total_requests)
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY route;  -- Takes 50-100ms
```

#### Alternative Recommendation

If simplicity is preferred over optimal performance, use **PostgreSQL only** with:
- Async database writes in middleware
- Connection pooling to handle write load
- Separate read replica for analytics queries
- Table partitioning by timestamp from day one

This is simpler but may add 5-10ms overhead per request vs. < 1ms for Redis approach.

## Summary: Is This End-to-End Sufficient?

**Yes!** The document now provides everything needed for your end-to-end workflow:

### What You Asked For:
✅ **Identify top N routes to cache** - CLI tool with `make cache-analysis n=10`
✅ **Heuristic algorithm** - Combines frequency + latency + user diversity
✅ **Both popular AND frequent** - Built into cache priority scoring
✅ **Query param handling** - Smart normalization groups similar requests
✅ **JSON output** - For feeding to future caching system
✅ **Human-readable output** - Table format for manual review

### End-to-End Flow:
1. **Middleware** captures every request → writes to Redis (< 1ms overhead)
2. **Celery task** (every 10 min) transfers Redis → PostgreSQL raw events table
3. **Celery task** (hourly) aggregates raw events → hourly time-series table
4. **CLI command** queries hourly table → applies heuristic → returns top N routes
5. **Future system** consumes JSON output → implements Redis caching

### Decisions You Need to Make:

**Decision 1: Query Parameter Normalization Rules**
- **Recommended**: Use smart normalization (exclude pagination params like `page`, `offset`)
- **Why**: Groups similar requests (all pages of same query pattern)
- **Customization needed**: Which params to exclude for YOUR routes?

Example normalization rules:
```python
# Params to exclude from normalization (vary within same pattern)
variable_params = {'page', 'offset', 'limit', 'cursor'}

# If you have other variable params specific to your app, add them:
# variable_params = {'page', 'offset', 'limit', 'cursor', 'timestamp', 'random_seed'}
```

A: For now, just your recommended ones.

**Decision 2: Cache Priority Approaches - TWO SYSTEMS**

We will implement TWO different cache priority analysis systems:

**System 1: Absolute Thresholds (Production-Ready)**
- Based on best practices for production environments
- Uses absolute thresholds (min requests/hour, min latency)
- Good when you have established traffic patterns
- CLI: `make cache-analysis n=10`
- Defaults:
  - Minimum 10 requests/hour (optional filter)
  - Minimum 100ms p95 latency (optional filter)
  - Adjustable: `make cache-analysis n=10 --min-requests=50 --min-latency=200`

**System 2: Relative Ranking (Development-Friendly)**
- Based on RELATIVE popularity and latency
- No absolute thresholds - ranks all routes by importance
- Perfect for development with sporadic/low traffic
- CLI: `make cache-analysis-relative n=10`
- Logic:
  - Popularity: How popular compared to OTHER routes (percentile-based)
  - Latency: How slow compared to OTHER routes (percentile-based)
  - Example: Routes taking 5-15 seconds get high priority even if infrequent, as long as they're slower than most other routes

Both systems output the same format (table/JSON) for consistency.

**Decision 3: Heuristic Weights (System 1 only)**
- **Current formula**: `(frequency * 10) + (latency / 100) + (user_diversity)`
- **Decision**: Use these defaults for System 1
- System 2 uses percentile-based ranking instead of weighted scores

**Decision 4: How Many Routes to Cache?**
- **Decision**: Configurable in `config/base.json`
- **Default**: Top 20 routes
- **Configuration**:
```json
"cache-planning": {
  "top-n-routes": 20,
  "pages-to-cache-per-route": 1
}
```

**Decision 5: Cache What Exactly?**
When CLI says "cache /api/v1/content/unified with page_size=10, sort=created_at":
- **Decision**: Cache first page only (page=1)
- Other pages can be cached on-demand or if they become popular
- Configurable via `pages-to-cache-per-route` in config/base.json 

### What You DON'T Need to Decide Now:
- ❌ Actual Redis caching implementation (future work)
- ❌ Cache expiration policies (future work)
- ❌ Cache warming strategies (future work)

### No New Scope Creep Issues!
The additions (CLI tool, query param handling) are **necessary** for your stated goal of identifying which routes to cache. They're not scope creep - they're making the plan **actionable**.

### What's NOT in This Document:
This document does NOT cover:
- Implementing the actual Redis caching layer (Phase 6 mentioned, but not detailed)
- Cache invalidation strategies
- Cache warming during deployment
- Cache hit/miss tracking (mentioned in schema, but implementation is future work)

Those are separate tasks that will use the output from this analytics system.

### Testing the CLI Before Full Implementation:
You could implement JUST the CLI tool (Phase 4) first to validate the heuristic with dummy data, then implement the full pipeline (Phases 1-3) once you're confident in the algorithm.

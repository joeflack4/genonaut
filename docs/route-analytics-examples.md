# Route Analytics - Example Queries and Usage

This document provides practical examples for working with the route analytics system, including SQL queries for monitoring, debugging, and analysis.

## Table of Contents
- [Quick Start Examples](#quick-start-examples)
- [Monitoring Queries](#monitoring-queries)
- [Cache Analysis Queries](#cache-analysis-queries)
- [Performance Analysis](#performance-analysis)
- [Debugging and Troubleshooting](#debugging-and-troubleshooting)
- [API Usage Examples](#api-usage-examples)
- [CLI Usage Examples](#cli-usage-examples)

## Quick Start Examples

### Check if Data is Flowing

```sql
-- Check recent raw events (should see data from last 10 minutes)
SELECT COUNT(*), MAX(timestamp) as latest_event
FROM route_analytics
WHERE timestamp > NOW() - INTERVAL '15 minutes';

-- Check hourly aggregations (should see data from last few hours)
SELECT COUNT(*), MAX(timestamp) as latest_hour
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '24 hours';
```

### View Recent Requests

```sql
-- Last 100 requests with their performance
SELECT
    timestamp,
    route,
    method,
    duration_ms,
    status_code,
    user_id
FROM route_analytics
ORDER BY timestamp DESC
LIMIT 100;
```

### Top 10 Slowest Routes (Last 24 Hours)

```sql
SELECT
    route,
    method,
    AVG(avg_duration_ms)::INTEGER as avg_latency,
    AVG(p95_duration_ms)::INTEGER as p95_latency,
    AVG(p99_duration_ms)::INTEGER as p99_latency,
    SUM(total_requests) as total_requests
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY route, method
ORDER BY avg_latency DESC
LIMIT 10;
```

## Monitoring Queries

### Data Freshness Check

```sql
-- Check how fresh the data is in both tables
SELECT
    'route_analytics' as table_name,
    COUNT(*) as total_rows,
    MAX(timestamp) as latest_timestamp,
    NOW() - MAX(timestamp) as data_age
FROM route_analytics
UNION ALL
SELECT
    'route_analytics_hourly' as table_name,
    COUNT(*) as total_rows,
    MAX(timestamp) as latest_timestamp,
    NOW() - MAX(timestamp) as data_age
FROM route_analytics_hourly;
```

### Request Volume by Hour

```sql
-- See request volume over the last 24 hours
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    SUM(total_requests) as requests,
    AVG(avg_duration_ms)::INTEGER as avg_latency_ms
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;
```

### Error Rate Monitoring

```sql
-- Check error rates across all routes
SELECT
    route,
    method,
    SUM(total_requests) as total_requests,
    SUM(successful_requests) as successful,
    SUM(client_errors) as client_errors,
    SUM(server_errors) as server_errors,
    (SUM(server_errors)::FLOAT / NULLIF(SUM(total_requests), 0) * 100)::NUMERIC(5,2) as server_error_rate_pct
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY route, method
HAVING SUM(server_errors) > 0
ORDER BY server_error_rate_pct DESC;
```

### Traffic by Endpoint

```sql
-- See which endpoints are getting the most traffic
SELECT
    route,
    method,
    SUM(total_requests) as total_requests,
    AVG(avg_duration_ms)::INTEGER as avg_latency,
    AVG(unique_users)::INTEGER as avg_unique_users
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY route, method
ORDER BY total_requests DESC
LIMIT 20;
```

## Cache Analysis Queries

### Find Routes for Caching (Manual)

```sql
-- Identify top routes for caching based on frequency and latency
SELECT
    route,
    method,
    query_params_normalized,
    AVG(total_requests) as avg_hourly_requests,
    AVG(p95_duration_ms)::INTEGER as avg_p95_latency,
    AVG(unique_users)::INTEGER as avg_unique_users,
    SUM(total_requests) as total_requests,
    -- Cache priority score: (frequency * 10) + (latency / 100) + (user_diversity)
    (AVG(total_requests) * 10 + AVG(p95_duration_ms) / 100 + LEAST(AVG(unique_users) / 10, 10))::INTEGER as cache_priority_score
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY route, method, query_params_normalized
HAVING AVG(total_requests) >= 10  -- Min 10 requests/hour
    AND AVG(p95_duration_ms) >= 100  -- Min 100ms latency
ORDER BY cache_priority_score DESC
LIMIT 20;
```

### Popular Query Patterns for a Route

```sql
-- Find the most popular query parameter patterns for a specific route
SELECT
    route,
    query_params_normalized,
    SUM(total_requests) as total_requests,
    AVG(avg_duration_ms)::INTEGER as avg_duration,
    AVG(p95_duration_ms)::INTEGER as p95_duration
FROM route_analytics_hourly
WHERE route = '/api/v1/content/unified'
    AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY route, query_params_normalized
ORDER BY total_requests DESC
LIMIT 10;
```

### Peak Hours by Route

```sql
-- Identify peak traffic hours for cache warming
SELECT
    route,
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    AVG(total_requests)::INTEGER as avg_requests,
    AVG(p95_duration_ms)::INTEGER as avg_p95_latency,
    AVG(unique_users)::INTEGER as avg_unique_users
FROM route_analytics_hourly
WHERE route = '/api/v1/content/unified'
    AND timestamp > NOW() - INTERVAL '30 days'
GROUP BY route, EXTRACT(HOUR FROM timestamp)
ORDER BY avg_requests DESC;
```

## Performance Analysis

### Latency Percentiles Over Time

```sql
-- Track latency trends for a specific route
SELECT
    DATE_TRUNC('day', timestamp) as day,
    route,
    AVG(avg_duration_ms)::INTEGER as avg_latency,
    AVG(p50_duration_ms)::INTEGER as p50,
    AVG(p95_duration_ms)::INTEGER as p95,
    AVG(p99_duration_ms)::INTEGER as p99,
    SUM(total_requests) as total_requests
FROM route_analytics_hourly
WHERE route = '/api/v1/content/unified'
    AND timestamp > NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', timestamp), route
ORDER BY day DESC;
```

### Compare Route Performance

```sql
-- Compare performance across different routes
SELECT
    route,
    method,
    COUNT(*) as hours_with_data,
    AVG(avg_duration_ms)::INTEGER as avg_latency,
    AVG(p95_duration_ms)::INTEGER as p95_latency,
    SUM(total_requests) as total_requests,
    AVG(unique_users)::INTEGER as avg_unique_users
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY route, method
HAVING SUM(total_requests) > 100
ORDER BY p95_latency DESC
LIMIT 20;
```

### User Engagement by Route

```sql
-- See which routes have the most user diversity
SELECT
    route,
    method,
    AVG(unique_users)::INTEGER as avg_unique_users,
    SUM(total_requests) as total_requests,
    (SUM(total_requests)::FLOAT / NULLIF(AVG(unique_users), 0))::NUMERIC(10,2) as requests_per_user
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY route, method
ORDER BY avg_unique_users DESC
LIMIT 20;
```

### Success Rate Trends

```sql
-- Track success rates over time
SELECT
    DATE_TRUNC('day', timestamp) as day,
    route,
    SUM(total_requests) as total_requests,
    SUM(successful_requests) as successful,
    (SUM(successful_requests)::FLOAT / NULLIF(SUM(total_requests), 0) * 100)::NUMERIC(5,2) as success_rate_pct
FROM route_analytics_hourly
WHERE route = '/api/v1/content/unified'
    AND timestamp > NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', timestamp), route
ORDER BY day DESC;
```

## Debugging and Troubleshooting

### Check Data Transfer from Redis

```sql
-- Verify Redis to PostgreSQL transfer is working
-- Should see new data every 10 minutes
SELECT
    DATE_TRUNC('minute', timestamp) as minute,
    COUNT(*) as event_count
FROM route_analytics
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY DATE_TRUNC('minute', timestamp)
ORDER BY minute DESC;
```

### Check Hourly Aggregation

```sql
-- Verify hourly aggregation task is running
-- Should see one entry per hour per route pattern
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(DISTINCT route) as unique_routes,
    SUM(total_requests) as total_requests_aggregated
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;
```

### Find Missing Hours

```sql
-- Identify any gaps in hourly aggregations
WITH expected_hours AS (
    SELECT generate_series(
        DATE_TRUNC('hour', NOW() - INTERVAL '24 hours'),
        DATE_TRUNC('hour', NOW()),
        INTERVAL '1 hour'
    ) as hour
)
SELECT
    eh.hour,
    COALESCE(COUNT(DISTINCT rah.route), 0) as routes_tracked
FROM expected_hours eh
LEFT JOIN route_analytics_hourly rah ON DATE_TRUNC('hour', rah.timestamp) = eh.hour
GROUP BY eh.hour
ORDER BY eh.hour DESC;
```

### Query Parameter Normalization Check

```sql
-- Verify query parameter normalization is working correctly
SELECT
    route,
    query_params,
    query_params_normalized,
    COUNT(*) as request_count
FROM route_analytics
WHERE route = '/api/v1/content/unified'
    AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY route, query_params, query_params_normalized
ORDER BY request_count DESC
LIMIT 20;
```

### Raw Events vs Aggregated Comparison

```sql
-- Compare counts between raw and aggregated tables
-- Should roughly match (accounting for timing differences)
SELECT
    'Raw Events (last hour)' as source,
    COUNT(*) as count,
    COUNT(DISTINCT route) as unique_routes
FROM route_analytics
WHERE timestamp >= DATE_TRUNC('hour', NOW() - INTERVAL '1 hour')
    AND timestamp < DATE_TRUNC('hour', NOW())
UNION ALL
SELECT
    'Aggregated (last completed hour)' as source,
    SUM(total_requests) as count,
    COUNT(DISTINCT route) as unique_routes
FROM route_analytics_hourly
WHERE timestamp = DATE_TRUNC('hour', NOW() - INTERVAL '1 hour');
```

## API Usage Examples

### Get Top 5 Routes for Caching (Absolute System)

```bash
curl "http://localhost:8001/api/v1/analytics/routes/cache-priorities?n=5&system=absolute" | jq .
```

### Get Top 10 Routes for Caching (Relative System)

```bash
curl "http://localhost:8001/api/v1/analytics/routes/cache-priorities?n=10&system=relative&days=7" | jq .
```

### Get Performance Trends (Hourly)

```bash
curl "http://localhost:8001/api/v1/analytics/routes/performance-trends?route=/api/v1/content/unified&days=7&granularity=hourly" | jq .
```

### Get Performance Trends (Daily)

```bash
curl "http://localhost:8001/api/v1/analytics/routes/performance-trends?route=/api/v1/tags/hierarchy&days=30&granularity=daily" | jq .
```

### Get Peak Hours for All Routes

```bash
curl "http://localhost:8001/api/v1/analytics/routes/peak-hours?days=30&min_requests=10" | jq .
```

### Get Peak Hours for Specific Route

```bash
curl "http://localhost:8001/api/v1/analytics/routes/peak-hours?route=/api/v1/content/unified&days=30" | jq .
```

### Python Example - Automated Cache Decision

```python
import requests
import json

# Get top 20 routes for caching
response = requests.get(
    "http://localhost:8001/api/v1/analytics/routes/cache-priorities",
    params={
        "n": 20,
        "system": "absolute",
        "days": 7,
        "min_requests": 50,
        "min_latency": 200
    }
)

data = response.json()

# Process results for cache configuration
cache_config = []
for route_info in data["routes"]:
    # Only cache first page of high-priority routes
    if route_info["cache_priority_score"] > 1000:
        cache_entry = {
            "pattern": f"{route_info['route']}?{json.dumps(route_info['query_params_normalized'])}",
            "ttl": 300,  # 5 minutes
            "priority": route_info["cache_priority_score"]
        }
        cache_config.append(cache_entry)

print(json.dumps(cache_config, indent=2))
```

## CLI Usage Examples

### System 1: Absolute Thresholds (Production)

```bash
# Basic usage - top 10 routes
make cache-analysis n=10

# Custom parameters
make cache-analysis n=20 days=30 min-requests=50 min-latency=200

# JSON output for automation
make cache-analysis n=15 format=json > cache_recommendations.json

# Direct Python invocation
source env/python_venv/bin/activate
ENV_TARGET=local-demo python -m genonaut.cli.cache_analysis \
    --count=10 \
    --days=7 \
    --format=table \
    --min-requests=10 \
    --min-latency=100
```

### System 2: Relative Ranking (Development)

```bash
# Basic usage - top 10 routes
make cache-analysis-relative n=10

# More routes, longer history
make cache-analysis-relative n=20 days=30

# JSON output
make cache-analysis-relative n=15 format=json > cache_recommendations_relative.json

# Direct Python invocation
source env/python_venv/bin/activate
ENV_TARGET=local-demo python -m genonaut.cli.cache_analysis_relative \
    --count=10 \
    --days=7 \
    --format=json
```

### Comparing Both Systems

```bash
# Get recommendations from both systems
make cache-analysis n=10 format=json > cache_absolute.json
make cache-analysis-relative n=10 format=json > cache_relative.json

# Compare results
diff <(jq -r '.[].route' cache_absolute.json | sort) \
     <(jq -r '.[].route' cache_relative.json | sort)
```

## Advanced Usage

### Custom Aggregation - By Day of Week

```sql
-- Analyze traffic patterns by day of week
SELECT
    EXTRACT(DOW FROM timestamp) as day_of_week,
    CASE EXTRACT(DOW FROM timestamp)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END as day_name,
    route,
    AVG(total_requests)::INTEGER as avg_requests_per_hour,
    AVG(p95_duration_ms)::INTEGER as avg_p95_latency
FROM route_analytics_hourly
WHERE timestamp > NOW() - INTERVAL '30 days'
    AND route = '/api/v1/content/unified'
GROUP BY EXTRACT(DOW FROM timestamp), route
ORDER BY day_of_week;
```

### Identify Anomalies

```sql
-- Find hours with unusually high latency (> 2 standard deviations above mean)
WITH stats AS (
    SELECT
        route,
        AVG(avg_duration_ms) as mean_latency,
        STDDEV(avg_duration_ms) as stddev_latency
    FROM route_analytics_hourly
    WHERE timestamp > NOW() - INTERVAL '7 days'
    GROUP BY route
)
SELECT
    rah.timestamp,
    rah.route,
    rah.avg_duration_ms,
    s.mean_latency::INTEGER,
    (rah.avg_duration_ms - s.mean_latency)::INTEGER as deviation,
    rah.total_requests
FROM route_analytics_hourly rah
JOIN stats s ON rah.route = s.route
WHERE rah.timestamp > NOW() - INTERVAL '7 days'
    AND rah.avg_duration_ms > s.mean_latency + (2 * s.stddev_latency)
ORDER BY rah.timestamp DESC;
```

### Export Data for External Analysis

```bash
# Export to CSV for spreadsheet analysis
psql -h localhost -U genonaut_admin -d genonaut -c "\COPY (
    SELECT
        timestamp,
        route,
        method,
        total_requests,
        avg_duration_ms,
        p95_duration_ms,
        unique_users
    FROM route_analytics_hourly
    WHERE timestamp > NOW() - INTERVAL '30 days'
    ORDER BY timestamp DESC
) TO '/tmp/route_analytics_export.csv' WITH CSV HEADER"
```

## Tips and Best Practices

1. **Use Hourly Table for Analysis**: Always query `route_analytics_hourly` for analysis - it's orders of magnitude faster than the raw table.

2. **Monitor Data Freshness**: Check `MAX(timestamp)` regularly to ensure Celery tasks are running properly.

3. **Watch for Query Parameter Explosion**: If you see too many unique `query_params_normalized` values, review normalization rules.

4. **Set Appropriate Lookback Windows**:
   - Cache decisions: 7-14 days
   - Performance monitoring: 24 hours - 7 days
   - Trend analysis: 30-90 days

5. **Use JSON Output for Automation**: Both CLI tools support `--format=json` for feeding into automated systems.

6. **Compare Both Cache Systems**: Use absolute for production, relative for development - they may recommend different routes.

7. **Monitor Error Rates**: High cache priority routes with high error rates may need fixing before caching.

# Generation Analytics Examples

This document provides practical examples for querying generation analytics data, including direct SQL queries and API usage examples.

## Table of Contents

1. [API Examples](#api-examples)
2. [Direct SQL Queries](#direct-sql-queries)
3. [Common Analysis Patterns](#common-analysis-patterns)
4. [Data Pipeline](#data-pipeline)

## API Examples

### Basic Dashboard Overview

Get a quick summary of generation activity for the last 7 days:

```bash
curl "http://localhost:8001/api/v1/analytics/generation/overview?days=7"
```

```python
import requests

response = requests.get(
    "http://localhost:8001/api/v1/analytics/generation/overview",
    params={"days": 7}
)
data = response.json()

print(f"Success rate: {data['success_rate_pct']:.1f}%")
print(f"Total requests: {data['total_requests']}")
print(f"P95 latency: {data['p95_duration_ms']}ms")
```

### Time-Series Analysis

Get hourly trends to visualize generation patterns:

```bash
curl "http://localhost:8001/api/v1/analytics/generation/trends?days=7&interval=hourly"
```

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Fetch trends data
response = requests.get(
    "http://localhost:8001/api/v1/analytics/generation/trends",
    params={"days": 7, "interval": "hourly"}
)
data = response.json()

# Convert to DataFrame for analysis
df = pd.DataFrame(data['data_points'])
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Plot success rate over time
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['success_rate'], marker='o')
plt.xlabel('Time')
plt.ylabel('Success Rate')
plt.title('Generation Success Rate - Last 7 Days')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

### User-Specific Analytics

Analyze generation history for a specific user:

```bash
USER_ID="550e8400-e29b-41d4-a716-446655440000"
curl "http://localhost:8001/api/v1/analytics/generation/users/${USER_ID}?days=30"
```

```python
import requests

user_id = "550e8400-e29b-41d4-a716-446655440000"
response = requests.get(
    f"http://localhost:8001/api/v1/analytics/generation/users/{user_id}",
    params={"days": 30}
)
data = response.json()

print(f"User {user_id} Analytics:")
print(f"  Total requests: {data['total_requests']}")
print(f"  Success rate: {data['success_rate_pct']:.1f}%")
print(f"  Avg duration: {data['avg_duration_ms']}ms")

# Show failure breakdown
if data['failure_breakdown']:
    print("\nFailure breakdown:")
    for failure in data['failure_breakdown']:
        print(f"  {failure['error_type']}: {failure['count']} failures")
```

### Model Performance Comparison

Compare different model checkpoints:

```bash
curl "http://localhost:8001/api/v1/analytics/generation/models?days=30"
```

```python
import requests
import pandas as pd

response = requests.get(
    "http://localhost:8001/api/v1/analytics/generation/models",
    params={"days": 30}
)
data = response.json()

# Convert to DataFrame for easy comparison
df = pd.DataFrame(data['models'])
df = df.sort_values('success_rate_pct', ascending=False)

print("Model Performance Comparison:")
print(df[['model_checkpoint', 'total_generations', 'success_rate_pct', 'p95_duration_ms']])
```

### Failure Analysis

Investigate recurring errors:

```bash
curl "http://localhost:8001/api/v1/analytics/generation/failures?days=7"
```

```python
import requests

response = requests.get(
    "http://localhost:8001/api/v1/analytics/generation/failures",
    params={"days": 7}
)
data = response.json()

# Analyze error types
print("Top Error Types:")
for error in data['error_types']:
    print(f"\n{error['error_type']}: {error['count']} occurrences")
    print(f"  Avg duration: {error['avg_duration_ms']}ms")
    print("  Sample messages:")
    for msg in error['sample_messages'][:2]:
        print(f"    - {msg}")

# Plot failure trends
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame(data['failure_trends'])
df['date'] = pd.to_datetime(df['date'])

plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['failure_rate'], marker='o', color='red')
plt.xlabel('Date')
plt.ylabel('Failure Rate')
plt.title('Generation Failure Rate Trend')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

### Peak Hours Analysis

Identify capacity planning needs:

```bash
curl "http://localhost:8001/api/v1/analytics/generation/peak-hours?days=30"
```

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt

response = requests.get(
    "http://localhost:8001/api/v1/analytics/generation/peak-hours",
    params={"days": 30}
)
data = response.json()

df = pd.DataFrame(data['peak_hours'])

# Create bar chart of requests by hour
plt.figure(figsize=(14, 6))
plt.bar(df['hour_of_day'], df['avg_requests'])
plt.xlabel('Hour of Day (UTC)')
plt.ylabel('Average Requests')
plt.title('Generation Load by Hour of Day')
plt.xticks(range(24))
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()

# Print peak hours
print("Peak generation hours:")
top_hours = df.nlargest(5, 'avg_requests')
for _, row in top_hours.iterrows():
    print(f"  Hour {int(row['hour_of_day']):02d}:00 - {row['avg_requests']:.1f} requests/hour")
```

## Direct SQL Queries

These queries access the underlying PostgreSQL tables directly. Useful for custom analysis or debugging.

### Query Raw Generation Events

Get recent generation events:

```sql
-- Last 100 generation events
SELECT
    id,
    event_type,
    generation_id,
    user_id,
    timestamp,
    duration_ms,
    success,
    error_type,
    model_checkpoint
FROM generation_events
ORDER BY timestamp DESC
LIMIT 100;
```

### Find Slow Generations

Identify generations taking longer than 10 seconds:

```sql
-- Slow generations (> 10 seconds)
SELECT
    generation_id,
    user_id,
    timestamp,
    duration_ms,
    model_checkpoint,
    success,
    error_type
FROM generation_events
WHERE event_type = 'completion'
    AND duration_ms > 10000
ORDER BY duration_ms DESC
LIMIT 50;
```

### User Activity Summary

Aggregate user generation statistics:

```sql
-- User generation summary (last 30 days)
SELECT
    user_id,
    COUNT(*) FILTER (WHERE event_type = 'request') as total_requests,
    COUNT(*) FILTER (WHERE event_type = 'completion' AND success = true) as successful,
    COUNT(*) FILTER (WHERE event_type = 'completion' AND success = false) as failed,
    AVG(duration_ms) FILTER (WHERE event_type = 'completion')::INTEGER as avg_duration_ms,
    MAX(timestamp) as last_generation_at
FROM generation_events
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY user_id
ORDER BY total_requests DESC
LIMIT 20;
```

### Hourly Metrics

Query pre-aggregated hourly data:

```sql
-- Hourly metrics for last 7 days
SELECT
    timestamp,
    total_requests,
    successful_generations,
    failed_generations,
    cancelled_generations,
    p95_duration_ms,
    unique_users,
    avg_queue_length,
    total_images_generated
FROM generation_metrics_hourly
WHERE timestamp >= NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

### Model Performance Analysis

Compare models over time:

```sql
-- Model performance comparison (last 30 days)
SELECT
    model_checkpoint,
    COUNT(*) FILTER (WHERE event_type = 'completion') as total_generations,
    COUNT(*) FILTER (WHERE event_type = 'completion' AND success = true) as successful,
    COUNT(*) FILTER (WHERE event_type = 'completion' AND success = false) as failed,
    (COUNT(*) FILTER (WHERE event_type = 'completion' AND success = true)::FLOAT /
     NULLIF(COUNT(*) FILTER (WHERE event_type = 'completion'), 0) * 100)::NUMERIC(5,2) as success_rate_pct,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p50_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p95_duration_ms,
    AVG(duration_ms)::INTEGER as avg_duration_ms
FROM generation_events
WHERE timestamp >= NOW() - INTERVAL '30 days'
    AND model_checkpoint IS NOT NULL
GROUP BY model_checkpoint
ORDER BY total_generations DESC;
```

### Error Analysis

Breakdown errors by type and time:

```sql
-- Daily error breakdown (last 14 days)
SELECT
    DATE(timestamp) as day,
    error_type,
    COUNT(*) as error_count,
    AVG(duration_ms)::INTEGER as avg_duration_ms,
    array_agg(DISTINCT error_message) as sample_messages
FROM generation_events
WHERE timestamp >= NOW() - INTERVAL '14 days'
    AND event_type = 'completion'
    AND success = false
GROUP BY DATE(timestamp), error_type
ORDER BY day DESC, error_count DESC;
```

### Peak Hour Analysis

Identify busiest hours by day of week:

```sql
-- Peak hours by day of week (last 30 days)
SELECT
    EXTRACT(DOW FROM timestamp)::INTEGER as day_of_week,
    EXTRACT(HOUR FROM timestamp)::INTEGER as hour_of_day,
    AVG(total_requests) as avg_requests,
    AVG(p95_duration_ms) as avg_p95_duration,
    COUNT(*) as data_points
FROM generation_metrics_hourly
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY EXTRACT(DOW FROM timestamp), EXTRACT(HOUR FROM timestamp)
ORDER BY avg_requests DESC
LIMIT 20;
```

## Common Analysis Patterns

### Pattern 1: Identify Performance Degradation

Monitor if generation times are increasing over time:

```python
import requests
import pandas as pd
import numpy as np

# Fetch daily trends for last 30 days
response = requests.get(
    "http://localhost:8001/api/v1/analytics/generation/trends",
    params={"days": 30, "interval": "daily"}
)
data = response.json()

df = pd.DataFrame(data['data_points'])
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Calculate moving average for p95 duration
df['p95_ma_7d'] = df['p95_duration_ms'].rolling(window=7).mean()

# Check if recent performance is degrading
recent_avg = df.tail(7)['p95_duration_ms'].mean()
baseline_avg = df.head(7)['p95_duration_ms'].mean()

if recent_avg > baseline_avg * 1.2:  # 20% slower
    print(f"WARNING: Performance degradation detected!")
    print(f"  Recent avg: {recent_avg:.0f}ms")
    print(f"  Baseline: {baseline_avg:.0f}ms")
    print(f"  Degradation: {((recent_avg/baseline_avg - 1) * 100):.1f}%")
```

### Pattern 2: User Cohort Analysis

Compare generation behavior across user groups:

```sql
-- New users vs experienced users (last 30 days)
WITH user_first_gen AS (
    SELECT
        user_id,
        MIN(timestamp) as first_generation_at
    FROM generation_events
    WHERE event_type = 'request'
    GROUP BY user_id
),
recent_activity AS (
    SELECT
        e.user_id,
        CASE
            WHEN u.first_generation_at >= NOW() - INTERVAL '7 days' THEN 'new'
            ELSE 'experienced'
        END as user_type,
        COUNT(*) FILTER (WHERE e.event_type = 'completion') as generations,
        AVG(e.duration_ms) FILTER (WHERE e.event_type = 'completion')::INTEGER as avg_duration,
        COUNT(*) FILTER (WHERE e.event_type = 'completion' AND e.success = true)::FLOAT /
            NULLIF(COUNT(*) FILTER (WHERE e.event_type = 'completion'), 0) as success_rate
    FROM generation_events e
    JOIN user_first_gen u ON e.user_id = u.user_id
    WHERE e.timestamp >= NOW() - INTERVAL '30 days'
    GROUP BY e.user_id, user_type
)
SELECT
    user_type,
    COUNT(DISTINCT user_id) as user_count,
    AVG(generations)::INTEGER as avg_generations_per_user,
    AVG(avg_duration)::INTEGER as avg_duration_ms,
    AVG(success_rate)::NUMERIC(4,3) as avg_success_rate
FROM recent_activity
GROUP BY user_type;
```

### Pattern 3: Alert on High Failure Rates

Detect when failure rates exceed threshold:

```python
import requests

response = requests.get(
    "http://localhost:8001/api/v1/analytics/generation/overview",
    params={"days": 1}  # Last 24 hours
)
data = response.json()

FAILURE_THRESHOLD = 10.0  # 10% failure rate

failure_rate = 100 - data['success_rate_pct']

if failure_rate > FAILURE_THRESHOLD:
    print(f"ALERT: High failure rate detected: {failure_rate:.1f}%")

    # Get failure details
    failures_response = requests.get(
        "http://localhost:8001/api/v1/analytics/generation/failures",
        params={"days": 1}
    )
    failures = failures_response.json()

    print("\nTop errors:")
    for error in failures['error_types'][:3]:
        print(f"  {error['error_type']}: {error['count']} occurrences")
```

## Data Pipeline

### Overview

The generation analytics data flows through several stages:

1. **Event Capture** (< 1ms overhead)
   - MetricsService records events to Redis Streams
   - Non-blocking writes to avoid impacting generation performance
   - Stream key: `{redis_ns}:generation_events:stream`

2. **Event Transfer** (Every 10 minutes)
   - Celery task: `transfer_generation_events_to_postgres`
   - Reads up to 1000 events from Redis Stream
   - Batch inserts to `generation_events` table
   - Trims processed events from Redis

3. **Hourly Aggregation** (Every hour)
   - Celery task: `aggregate_generation_metrics_hourly`
   - Aggregates events into `generation_metrics_hourly` table
   - Calculates percentiles, averages, and counts
   - Uses `ON CONFLICT DO UPDATE` for idempotency

4. **Query Layer**
   - GenerationAnalyticsService queries aggregated tables
   - API endpoints expose data via REST interface
   - Fast queries (< 100ms) due to pre-aggregation

### Monitoring the Pipeline

Check if data is flowing correctly:

```sql
-- Check if Redis transfer is working (events should be recent)
SELECT
    MAX(created_at) as latest_event,
    COUNT(*) as total_events,
    NOW() - MAX(created_at) as time_since_last_event
FROM generation_events;

-- Check if hourly aggregation is working
SELECT
    MAX(timestamp) as latest_hourly_metric,
    COUNT(*) as total_hours,
    NOW() - MAX(timestamp) as time_since_last_aggregation
FROM generation_metrics_hourly;

-- Verify data completeness (should have hourly rows for recent period)
SELECT
    DATE(timestamp) as day,
    COUNT(*) as hours_with_data
FROM generation_metrics_hourly
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY day DESC;
```

### Troubleshooting

If data is missing or stale:

1. **Check Celery workers are running:**
   ```bash
   make celery-dev
   ```

2. **Check Celery Beat schedule:**
   ```bash
   make beat-status
   ```

3. **Manually trigger tasks:**
   ```bash
   python -c "from genonaut.worker.tasks import transfer_generation_events_to_postgres; transfer_generation_events_to_postgres.delay()"
   python -c "from genonaut.worker.tasks import aggregate_generation_metrics_hourly; aggregate_generation_metrics_hourly.delay()"
   ```

4. **Check Redis Stream:**
   ```bash
   make redis-keys-dev  # Should show generation_events:stream
   ```

5. **Check task logs:**
   ```bash
   # Check Celery worker logs for errors
   tail -f logs/celery.log
   ```

## Generation Analytics
We should refactor the existing in-memory MetricsService to use persistent storage. Currently, all generation
metrics are stored in memory and lost on restart. We need to move to storing this information in Redis (for fast
writes) and PostgreSQL (for long-term analytics and reporting).

Context: This will enable long-term generation monitoring, user behavior analysis, performance tracking, and capacity
planning for image generation infrastructure.

When you actually go about working on this, follow the SOP in `notes/routines/new-big-task.md`.

## Implementation tasks

## Reports

### Analysis and Recommendations

#### Current State
The project currently has:
1. **MetricsService** (genonaut/api/services/metrics_service.py:22) - In-memory metrics service tracking:
   - Generation requests, completions, failures, cancellations
   - User activity (active users, generation counts per user, last activity times)
   - Performance metrics (response times, error rates, resource usage)
   - Queue statistics (queue length, active generations)
   - Success rates and average generation times
   - Alert thresholds for monitoring
2. **Storage**: All data in memory with deque (max 1000 entries), lost on restart
3. **Current usage**: Called from generation service, ComfyUI integration, monitoring endpoints

#### Problem Statement
- **Data Loss**: All metrics lost on server restart
- **Limited History**: Only last 1000 entries kept in memory
- **No Analytics**: Cannot analyze trends over time
- **Missing Insights**: Cannot identify patterns in user behavior, peak usage times, or failure patterns
- **Capacity Planning**: No historical data for infrastructure scaling decisions

#### Primary Recommendation: Hybrid Approach (PostgreSQL + Redis)

**Why this is the best choice:**
1. **Performance**: Fast, non-blocking writes to Redis
2. **Analytics Power**: PostgreSQL enables complex queries for trend analysis
3. **Infrastructure Ready**: Both systems already running
4. **Consistent Pattern**: Same approach as route analytics
5. **Background Processing**: Leverage existing Celery workers

#### Implementation Design

**1. Data Models**

**Generation Events Table** (for individual events):
```python
{
    "event_type": "request|completion|cancellation",  # Type of event
    "generation_id": "uuid-string",                   # Unique generation job ID
    "user_id": "uuid-string",                        # User who initiated
    "timestamp": "2025-01-15T10:30:45.123Z",        # When event occurred
    "generation_type": "standard|batch|priority",    # Generation type
    "duration_ms": 45230,                            # Total duration (completion only)
    "success": true,                                 # Success/failure (completion only)
    "error_type": null,                              # Error category if failed
    "error_message": null,                           # Error details if failed
    "queue_wait_time_ms": 1200,                     # Time spent in queue
    "generation_time_ms": 44030,                    # Actual generation time
    "model_checkpoint": "illustriousXL_v01",        # Model used
    "image_dimensions": {"width": 832, "height": 1216},  # Output dimensions
    "batch_size": 1,                                # Number of images
    "prompt_tokens": 45,                            # Prompt complexity metric
}
```

**Aggregated Metrics Table** (for time-series data):
```python
{
    "timestamp": "2025-01-15T10:00:00Z",           # Hour bucket
    "total_requests": 145,                          # Requests in this hour
    "successful_generations": 132,                  # Successes
    "failed_generations": 10,                       # Failures
    "cancelled_generations": 3,                     # Cancellations
    "avg_duration_ms": 42500,                      # Average duration
    "p50_duration_ms": 40000,                      # Median
    "p95_duration_ms": 55000,                      # 95th percentile
    "p99_duration_ms": 62000,                      # 99th percentile
    "unique_users": 23,                            # Unique users this hour
    "avg_queue_length": 4.5,                       # Average queue depth
    "max_queue_length": 12,                        # Peak queue
    "total_images_generated": 145,                 # Total output images
}
```

**2. PostgreSQL Schema**

```sql
-- Individual generation events for detailed analytics
CREATE TABLE generation_events (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(20) NOT NULL,
    generation_id UUID NOT NULL,
    user_id UUID REFERENCES users(id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generation_type VARCHAR(20),
    duration_ms INTEGER,
    success BOOLEAN,
    error_type TEXT,
    error_message TEXT,
    queue_wait_time_ms INTEGER,
    generation_time_ms INTEGER,
    model_checkpoint TEXT,
    image_dimensions JSONB,
    batch_size INTEGER,
    prompt_tokens INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX idx_gen_events_timestamp ON generation_events(timestamp DESC);
CREATE INDEX idx_gen_events_user_time ON generation_events(user_id, timestamp DESC);
CREATE INDEX idx_gen_events_generation_id ON generation_events(generation_id);
CREATE INDEX idx_gen_events_event_type ON generation_events(event_type);
CREATE INDEX idx_gen_events_success ON generation_events(success) WHERE event_type = 'completion';
CREATE INDEX idx_gen_events_error_type ON generation_events(error_type) WHERE error_type IS NOT NULL;
CREATE INDEX idx_gen_events_model ON generation_events(model_checkpoint, timestamp DESC);

-- Aggregated hourly metrics for fast dashboard queries
CREATE TABLE generation_metrics_hourly (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    total_requests INTEGER NOT NULL,
    successful_generations INTEGER NOT NULL,
    failed_generations INTEGER NOT NULL,
    cancelled_generations INTEGER NOT NULL,
    avg_duration_ms INTEGER,
    p50_duration_ms INTEGER,
    p95_duration_ms INTEGER,
    p99_duration_ms INTEGER,
    unique_users INTEGER,
    avg_queue_length FLOAT,
    max_queue_length INTEGER,
    total_images_generated INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(timestamp)
);

CREATE INDEX idx_gen_metrics_timestamp ON generation_metrics_hourly(timestamp DESC);

-- Partitioning for large-scale deployments
-- CREATE TABLE generation_events_2025_01 PARTITION OF generation_events
--     FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

**3. Refactored MetricsService Architecture**

**Current flow:**
```
Generation event -> MetricsService (in-memory) -> Lost on restart
```

**New flow:**
```
Generation event -> MetricsService (in-memory + Redis write) -> Celery task -> PostgreSQL
```

**Key changes to MetricsService:**
- Keep in-memory tracking for real-time monitoring (recent 1 hour)
- Add Redis write for each significant event
- Use Redis Streams for reliable event storage
- Keep existing API methods for backward compatibility
- Add async writes that don't block generation flow

**4. Redis Storage Strategy**

Use separate Redis Streams for different event types:

```python
# Generation events stream
XADD generation_events:stream * \
    event_type "request" \
    generation_id "uuid" \
    user_id "uuid" \
    timestamp "2025-01-15T10:30:45.123Z" \
    generation_type "standard"

# Real-time metrics (for monitoring)
HSET generation_metrics:current \
    active_generations 5 \
    queue_length 12 \
    success_rate_1h 0.92
```

**Retention policy:**
- Keep last 2 hours of raw events in Redis
- Keep current metrics indefinitely (overwritten)
- Trim after successful PostgreSQL transfer

**5. Celery Background Tasks**

**Task 1: Transfer Events (every 10 minutes)**
```python
@celery_app.task
def transfer_generation_events_to_postgres():
    """Transfer generation events from Redis to PostgreSQL."""
    # Read from Redis Stream
    # Batch insert to generation_events table (1000 at a time)
    # Trim processed events from Redis
    # Handle failures gracefully
```

**Task 2: Aggregate Metrics (hourly)**
```python
@celery_app.task
def aggregate_generation_metrics():
    """Calculate hourly aggregates from generation_events."""
    # Query last hour of generation_events
    # Calculate statistics (avg, p50, p95, p99)
    # Insert into generation_metrics_hourly
    # Handle duplicate timestamps (ON CONFLICT DO UPDATE)
```

**6. Backward Compatibility**

Keep MetricsService interface unchanged:
```python
class MetricsService:
    def record_generation_request(self, user_id, generation_type):
        # Keep in-memory tracking
        self._update_memory_stats()

        # NEW: Write to Redis asynchronously
        self._write_to_redis_async({
            "event_type": "request",
            "user_id": user_id,
            "generation_type": generation_type,
            "timestamp": datetime.utcnow().isoformat()
        })

    def record_generation_completion(self, user_id, success, duration, error_type):
        # Keep in-memory tracking
        self._update_memory_stats()

        # NEW: Write to Redis asynchronously
        self._write_to_redis_async({
            "event_type": "completion",
            "user_id": user_id,
            "success": success,
            "duration_ms": int(duration * 1000),
            "error_type": error_type,
            "timestamp": datetime.utcnow().isoformat()
        })

    # Keep all existing get_* methods for real-time queries
    # Add new get_historical_* methods for PostgreSQL queries
```

**7. Analytics Queries**

Based on stored data, enable analytics like:

```sql
-- User generation patterns
SELECT
    user_id,
    COUNT(*) as total_generations,
    AVG(duration_ms) as avg_duration,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate
FROM generation_events
WHERE event_type = 'completion'
    AND timestamp > NOW() - INTERVAL '30 days'
GROUP BY user_id
ORDER BY total_generations DESC;

-- Peak usage times
SELECT
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    EXTRACT(DOW FROM timestamp) as day_of_week,
    AVG(total_requests) as avg_requests
FROM generation_metrics_hourly
WHERE timestamp > NOW() - INTERVAL '90 days'
GROUP BY hour_of_day, day_of_week
ORDER BY avg_requests DESC;

-- Failure pattern analysis
SELECT
    error_type,
    COUNT(*) as occurrences,
    AVG(duration_ms) as avg_duration_before_failure,
    COUNT(DISTINCT user_id) as affected_users
FROM generation_events
WHERE event_type = 'completion'
    AND success = false
    AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY error_type
ORDER BY occurrences DESC;

-- Model performance comparison
SELECT
    model_checkpoint,
    COUNT(*) as uses,
    AVG(generation_time_ms) as avg_generation_time,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate
FROM generation_events
WHERE event_type = 'completion'
    AND timestamp > NOW() - INTERVAL '30 days'
GROUP BY model_checkpoint
ORDER BY uses DESC;
```

#### Additional Metrics to Track

**Already in MetricsService:**
- Generation requests, completions, failures, cancellations
- Duration tracking
- User activity
- Queue statistics

**Recommended Additions:**
- **Queue wait time** - Time from request to generation start
- **Generation time** - Actual generation duration (excluding queue)
- **Model used** - Which checkpoint/model was used
- **Image dimensions** - Output size
- **Prompt tokens** - Prompt complexity metric
- **Batch size** - Number of images generated
- **Resource usage** - GPU memory, compute time
- **Retry count** - Number of retry attempts

**Future Considerations:**
- **Cost tracking** - Compute costs per generation
- **Quality scores** - User ratings, automated quality metrics
- **A/B test tracking** - Model/parameter experiments
- **Geographic distribution** - User location patterns
- **Referrer tracking** - Where generation requests originate

#### Migration Path

1. **Phase 1**: Add Redis writes to existing MetricsService methods
2. **Phase 2**: Create PostgreSQL schema and migrations
3. **Phase 3**: Implement Celery transfer task (events)
4. **Phase 4**: Implement Celery aggregation task (hourly metrics)
5. **Phase 5**: Build analytics queries and monitoring dashboards
6. **Phase 6**: Add new metrics (queue wait time, model tracking, etc.)
7. **Phase 7**: Optional - retire in-memory storage for historical data

#### Performance Considerations

- Redis writes are async, don't block generation
- In-memory cache kept for real-time monitoring (1 hour window)
- PostgreSQL writes batched every 10 minutes
- Aggregation reduces query load (pre-calculated hourly stats)
- Indexes optimized for common query patterns
- Consider partitioning for > 10M events
- Monitor Redis memory usage, adjust retention as needed

#### Integration Points

**Files to modify:**
- `genonaut/api/services/metrics_service.py` - Add Redis writes
- `genonaut/db/schema.py` - Add new tables
- `genonaut/worker/tasks.py` - Add Celery tasks
- `config/base.json` - Add Celery Beat schedule entries

**New files to create:**
- `genonaut/api/services/generation_analytics_service.py` - Historical analytics queries
- `genonaut/db/migrations/versions/[timestamp]_add_generation_analytics_tables.py` - Schema migration

**API endpoints to add:**
- `GET /api/v1/analytics/generation/overview` - Dashboard overview
- `GET /api/v1/analytics/generation/trends` - Time-series trends
- `GET /api/v1/analytics/generation/users/{user_id}` - User-specific analytics
- `GET /api/v1/analytics/generation/models` - Model performance comparison
- `GET /api/v1/analytics/generation/failures` - Failure analysis

#### Benefits

1. **Persistent History**: Never lose generation metrics again
2. **Trend Analysis**: Identify patterns over weeks/months
3. **User Insights**: Understand user behavior and preferences
4. **Capacity Planning**: Data-driven infrastructure scaling
5. **Failure Analysis**: Root cause analysis for errors
6. **Model Optimization**: Compare model performance objectively
7. **Cost Optimization**: Track compute usage and costs
8. **Real-time + Historical**: Fast in-memory for live, PostgreSQL for analysis

#### Alternative Recommendation

If simplicity is preferred, use **PostgreSQL only** with:
- Direct async writes from MetricsService to PostgreSQL
- Connection pooling to handle write load
- Keep in-memory cache for real-time queries (1 hour)
- Use materialized views for aggregated metrics
- Refresh materialized views hourly

This is simpler but may add 2-5ms overhead per generation event vs. < 1ms for Redis approach.

# Performance: Request Timing Middleware

**Status:** Planned
**Priority:** Medium
**Estimated Effort:** 1-2 hours
**Expected Benefit:** Better diagnostics for performance issues

## Overview

Add middleware to capture and log detailed timing information for each API request. This will help diagnose performance issues faster by showing exactly where time is being spent in the request lifecycle.

## Problem Statement

Currently when we see slow requests (like the recent 5.82s issue), we have to:
- Manually profile endpoints
- Guess which component is slow
- Add temporary timing code
- Restart servers to test

This is time-consuming and doesn't help us catch regressions early.

## Solution

Add a middleware that automatically tracks and logs timing for:
- Total request duration
- Database query time (aggregate)
- Redis operations time
- Serialization time
- Business logic time
- Middleware overhead

## Benefits

1. **Faster Debugging:** Immediately see which component is slow
2. **Regression Detection:** Log timing to file/metrics system to catch regressions
3. **Production Monitoring:** Use in production to identify real-world bottlenecks
4. **No Code Changes:** Works automatically for all endpoints

## Implementation Phases

### Phase 1: Basic Timing Middleware
- [ ] Create `genonaut/api/middleware/timing.py`
- [ ] Implement `RequestTimingMiddleware` class
- [ ] Capture total request duration
- [ ] Log timing for requests >1s (slow request threshold)
- [ ] Add to middleware stack in `genonaut/api/main.py`
- [ ] Test with sample requests

### Phase 2: Database Query Timing
- [ ] Add SQLAlchemy event listener for query timing
- [ ] Track individual query times
- [ ] Aggregate total DB time per request
- [ ] Log slow queries (>100ms threshold)
- [ ] Include query count per request

### Phase 3: Component-Level Timing
- [ ] Add context var for timing tracker
- [ ] Instrument Redis operations (wrap `get_redis_client()`)
- [ ] Instrument serialization (custom JSON encoder)
- [ ] Track middleware overhead
- [ ] Calculate business logic time (total - components)

### Phase 4: Structured Logging
- [ ] Use structured logging format (JSON)
- [ ] Include request metadata (method, path, user_id, status_code)
- [ ] Add timing breakdown in response headers (optional, dev only)
- [ ] Configure logging output (file, stdout, metrics system)

### Phase 5: Metrics Integration (Optional)
- [ ] Integrate with Prometheus/StatsD for metrics
- [ ] Create Grafana dashboard for request timing
- [ ] Set up alerts for slow requests
- [ ] Add percentile tracking (p50, p95, p99)

## Example Output

```json
{
  "timestamp": "2025-10-25T12:34:56.789Z",
  "method": "GET",
  "path": "/api/v1/content/unified",
  "status_code": 200,
  "user_id": "121e194b-4caa-4b81-ad4f-86ca3919d5b9",
  "timing": {
    "total_ms": 652,
    "database_ms": 6,
    "database_queries": 3,
    "redis_ms": 10,
    "serialization_ms": 580,
    "middleware_ms": 5,
    "business_logic_ms": 51
  },
  "slow_queries": [
    {
      "query": "SELECT * FROM content_items_all WHERE...",
      "duration_ms": 125,
      "timestamp": "2025-10-25T12:34:56.800Z"
    }
  ]
}
```

## Configuration

Add to `config/base.json`:

```json
{
  "performance": {
    "timing_enabled": true,
    "slow_request_threshold_ms": 1000,
    "slow_query_threshold_ms": 100,
    "log_all_requests": false,
    "include_timing_headers": false
  }
}
```

## Testing

- [ ] Unit tests for timing middleware
- [ ] Integration tests with mock endpoints
- [ ] Verify timing accuracy (within 5% of actual)
- [ ] Test with concurrent requests
- [ ] Verify no performance overhead (<1ms)

## Rollout Plan

1. **Development:** Enable with `log_all_requests: true`
2. **Staging:** Enable with slow request logging only
3. **Production:** Enable with metrics integration
4. **Monitor:** Watch for any performance impact from middleware itself

## Related Work

- See `notes/route-analytics-fix-perf-tag-qry.md` for previous performance investigation
- Redis connection pooling fix in commit 5b0b108
- Performance tests in `test/api/performance/`

## Future Enhancements

- Request tracing with OpenTelemetry
- Distributed tracing for microservices
- Performance budgets per endpoint
- Automatic regression detection in CI

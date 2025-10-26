# Performance: JSON Serialization Optimization

**Status:** Planned (Optional)
**Priority:** Low
**Estimated Effort:** 30 minutes - 2 hours
**Expected Benefit:** 100-200ms (15-30% improvement)

## Overview

Optimize JSON serialization performance by replacing Python's standard `json` module with faster alternatives and implementing response compression.

## Problem Statement

Current performance breakdown shows:
- **Serialization/Network:** 584ms (90% of request time)
- Database queries: 6ms (1%)
- Business logic: 50ms (8%)
- Redis: 10ms (2%)

The largest single bottleneck is JSON serialization and HTTP response handling.

## Current State

- Using Python's built-in `json` module
- No response compression
- Returning full objects (not optimized payloads)

## Solution Options

### Option 1: Use orjson (Recommended)
`orjson` is 2-3x faster than standard `json` and handles edge cases better.

**Pros:**
- Drop-in replacement for most use cases
- Significantly faster (2-3x)
- Better datetime handling
- Better UUID handling

**Cons:**
- Additional dependency
- Slightly different API (returns bytes, not str)

### Option 2: Use ujson
Alternative fast JSON library.

**Pros:**
- Pure Python fallback available
- Faster than standard json

**Cons:**
- Not as fast as orjson
- Less actively maintained

### Option 3: Response Compression
Enable gzip/brotli compression for HTTP responses.

**Pros:**
- Reduces bandwidth
- Faster for large responses
- Works with existing serialization

**Cons:**
- CPU overhead for compression
- Client must support decompression

## Implementation Phases

### Phase 1: Benchmark Current Performance
- [ ] Create benchmarking script for serialization
- [ ] Test with realistic payloads (25 content items)
- [ ] Measure baseline performance
- [ ] Document current timings

### Phase 2: Implement orjson
- [ ] Add `orjson` to `requirements-unlocked.txt`
- [ ] Update `requirements.txt` with locked version
- [ ] Create custom JSON response class using orjson
- [ ] Update FastAPI JSON encoder configuration
- [ ] Handle datetime/UUID serialization
- [ ] Test with all endpoints

### Phase 3: Optimize Payload Size
- [ ] Audit response schemas for unnecessary fields
- [ ] Create minimal response schemas for list endpoints
- [ ] Implement field selection (e.g., `?fields=id,title,created_at`)
- [ ] Add response schema documentation
- [ ] Update API tests

### Phase 4: Enable Response Compression
- [ ] Add `GZipMiddleware` to FastAPI app
- [ ] Configure compression threshold (e.g., responses >500 bytes)
- [ ] Test compression with various payload sizes
- [ ] Measure bandwidth savings
- [ ] Document in API docs

### Phase 5: Benchmark & Validate
- [ ] Re-run performance benchmarks
- [ ] Compare before/after timings
- [ ] Run full test suite (ensure no regressions)
- [ ] Update performance tests with new targets
- [ ] Document performance improvements

## Expected Results

### Before (Standard json)
```
Average response time: 652ms
- Serialization: 580ms
- Other: 72ms
```

### After (orjson + compression)
```
Average response time: 450-550ms
- Serialization: 300-400ms (30-50% faster)
- Compression: 20-30ms
- Other: 72ms
```

**Net improvement: 100-200ms (15-30% faster)**

## Implementation Example

### Custom JSON Response

```python
# genonaut/api/utils/json_response.py
import orjson
from fastapi.responses import JSONResponse

class OrjsonResponse(JSONResponse):
    """FastAPI response using orjson for faster serialization."""

    media_type = "application/json"

    def render(self, content) -> bytes:
        return orjson.dumps(
            content,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
        )
```

### Update FastAPI App

```python
# genonaut/api/main.py
from genonaut.api.utils.json_response import OrjsonResponse

app = FastAPI(
    default_response_class=OrjsonResponse,
    # ... other config
)

# Add compression middleware
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)
```

### Field Selection (Optional)

```python
# genonaut/api/routes/content.py
@router.get("/unified")
def get_unified_content(
    fields: Optional[str] = Query(None, description="Comma-separated fields to return"),
    # ... other params
):
    items = service.get_unified_content(...)

    if fields:
        # Only include specified fields
        field_list = fields.split(",")
        items = [{k: v for k, v in item.items() if k in field_list} for item in items]

    return items
```

## Testing Checklist

- [ ] All existing tests pass
- [ ] Performance tests show improvement
- [ ] Edge cases handled (None, datetime, UUID, special chars)
- [ ] Response compression works for all endpoints
- [ ] Frontend still parses responses correctly
- [ ] Error responses still serialize correctly

## Rollout Plan

1. **Development:**
   - Install orjson
   - Test with subset of endpoints
   - Verify no breaking changes

2. **Testing:**
   - Run full test suite
   - Performance benchmarks
   - Frontend integration tests

3. **Staging:**
   - Deploy to staging
   - Monitor for issues
   - Compare performance metrics

4. **Production:**
   - Deploy during low-traffic period
   - Monitor error rates
   - Monitor performance improvements

## Risks & Mitigation

**Risk:** orjson serialization differences break existing code
- **Mitigation:** Comprehensive testing, gradual rollout

**Risk:** Compression increases CPU usage
- **Mitigation:** Monitor CPU metrics, adjust threshold if needed

**Risk:** Frontend can't decompress responses
- **Mitigation:** Modern browsers support gzip automatically

## Benchmarking Script

```python
# scripts/benchmark_serialization.py
import json
import orjson
import time
from typing import List, Dict, Any

def benchmark_serialization(data: List[Dict[str, Any]], iterations: int = 1000):
    """Benchmark json vs orjson serialization."""

    # Standard json
    start = time.time()
    for _ in range(iterations):
        json.dumps(data)
    json_time = time.time() - start

    # orjson
    start = time.time()
    for _ in range(iterations):
        orjson.dumps(data)
    orjson_time = time.time() - start

    print(f"Standard json: {json_time:.3f}s ({iterations} iterations)")
    print(f"orjson:        {orjson_time:.3f}s ({iterations} iterations)")
    print(f"Speedup:       {json_time / orjson_time:.2f}x faster")

# Test with realistic data
sample_content_items = [...]  # Load from DB
benchmark_serialization(sample_content_items)
```

## References

- [orjson GitHub](https://github.com/ijl/orjson)
- [FastAPI Custom Response Classes](https://fastapi.tiangolo.com/advanced/custom-response/)
- [FastAPI GZip Middleware](https://fastapi.tiangolo.com/advanced/middleware/#gzipmiddleware)
- Previous performance analysis: `notes/route-analytics-fix-perf-tag-qry.md`

## Decision

- [ ] Review benchmarking results
- [ ] Decide if 100-200ms improvement is worth the effort
- [ ] Consider if other optimizations have higher ROI
- [ ] Document decision in this file

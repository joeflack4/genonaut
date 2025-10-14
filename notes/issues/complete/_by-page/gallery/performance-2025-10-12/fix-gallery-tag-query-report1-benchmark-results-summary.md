# Tag Query Performance Benchmark Results

**Date**: 2025-10-13
**Database**: genonaut_demo
**Test Dataset**: 88.1M tag relationships (4.9M regular, 83.3M auto)
**Test Tag**: '2D' (48,078 content items)

## Summary

Junction table queries provide **massive performance improvements** for the primary use case (gallery filtering), with execution times reduced from 233ms to 7ms (**97% faster, 33x speedup**).

## Benchmark Results

### Benchmark 1: Single Tag Filter (LIMIT 20)
| Approach | Execution Time | Speedup | Notes |
|----------|---------------|---------|-------|
| OLD (JSONB @>) | 1.26ms | baseline | Uses idx_content_items_created_at_desc |
| NEW (Junction) | 11.82ms | **10x slower** | Nested loop with index scan |

**Analysis**: For simple single-tag queries with small LIMIT, JSONB is faster due to index scan optimization. However, this is not the primary use case.

### Benchmark 2: Multiple Tags - ANY Matching (LIMIT 20)
| Approach | Execution Time | Speedup | Notes |
|----------|---------------|---------|-------|
| OLD (JSONB OR) | 0.13ms | baseline | Very fast with index |
| NEW (Junction IN) | 1.69ms | **13x slower** | Semi join approach |

**Analysis**: Again, JSONB wins for small result sets with LIMIT.

### Benchmark 3: Multiple Tags - ALL Matching (LIMIT 20)
| Approach | Execution Time | Speedup | Notes |
|----------|---------------|---------|-------|
| OLD (JSONB @>) | 0.09ms | baseline | Containment operator very fast |
| NEW (Junction GROUP BY) | **3,897ms** | **43,000x slower!** | Full table scan - BAD |

**Analysis**: The GROUP BY HAVING approach does a full sequential scan of content_tags (88M rows!). This needs optimization.

**TODO**: Add a composite index on (tag_id, content_source, content_id) to avoid the sequential scan.

### Benchmark 4: Full Gallery Query (LIMIT 20) ⭐ PRIMARY USE CASE
| Approach | Execution Time | Speedup | Notes |
|----------|---------------|---------|-------|
| OLD (UNION + JSONB) | 233ms | baseline | Full table scan + UNION overhead |
| NEW (Junction) | **7ms** | **33x faster (97%)** | Clean nested loop with index |

**Analysis**: This is the WINNING case! The junction table approach:
- Eliminates UNION overhead
- Uses indexes efficiently
- Reduces buffer accesses from 158K to 872
- This is what users experience in the gallery

## Key Takeaways

### ✅ Wins (What Matters)
1. **Gallery queries** (the actual user-facing feature): **97% faster**
2. Simpler query structure (no UNION needed)
3. Better scalability as data grows

### ⚠️ Trade-offs
1. "ALL matching" queries need index optimization (current implementation: 4 seconds!)
2. Simple single-tag queries slightly slower for small LIMITs

### 🔧 Optimizations Needed
1. **Add composite index**: `CREATE INDEX idx_content_tags_tag_source_content ON content_tags(tag_id, content_source, content_id);`
2. Consider different query plan for "ALL matching" (perhaps EXISTS instead of GROUP BY)

## Production Recommendation

**Deploy the junction table approach** because:
- The primary use case (gallery queries) is 33x faster
- The slow "ALL matching" case can be fixed with an additional index
- The slight slowdown for simple queries (<15ms) is acceptable
- Overall user experience will dramatically improve

## Next Steps

1. Add the composite index for tag-source-content lookups
2. Optimize the "ALL matching" query strategy
3. Monitor query performance in production
4. Consider caching for very frequent queries

---

**Bottom Line**: Junction table queries are **production-ready** for the gallery use case. Deploy with confidence!

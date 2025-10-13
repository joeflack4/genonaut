# Gallery Tag Query Optimization - Implementation Plan

**Date**: 2025-10-13
**Status**: In Progress
**Goal**: Implement Phase 2 query optimizations using content_tags junction table

## Current State

- Phase 0: Complete - Tags migrated to UUID arrays
- Phase 1: Partially Complete
  - content_tags junction table created and migrated
  - Backfill: content_items 100% (4.87M relationships), content_items_auto 28%+ (ongoing)
  - ContentTag model added to schema.py

## Implementation Strategy

### Priority 1: Core Query Optimization (DO FIRST)

1. **Add junction table support to get_unified_content_paginated**
   - Keep existing JSONB array fallback for backward compatibility
   - Add new code path that uses content_tags JOIN when tags are filtered
   - Test both paths work correctly

2. **Fix creator_id filter inefficiency**
   - When both user + community selected for same table: remove creator_id filter
   - When neither selected: skip table entirely
   - Significant performance win for common use case

3. **Remove tag expansion logic**
   - Tags are now UUIDs only (no legacy slug support needed)
   - Remove expand_tag_identifiers() calls
   - Simplifies query logic

### Priority 2: Dual-Write Implementation

4. **Implement dual-write in content creation/update**
   - When tags are set on content, write to BOTH:
     - tags UUID[] array (for backward compatibility)
     - content_tags junction table rows
   - Update create_content and update_content methods

### Priority 3: Testing & Verification

5. **Add comprehensive tests**
   - Test creator filter combinations
   - Test single tag / multiple tags with 'any' / 'all' matching
   - Test tag-filtered queries return correct results
   - Test performance (should be under 1 second)

6. **Benchmark with EXPLAIN ANALYZE**
   - Run before/after comparison
   - Document query plans and execution times
   - Verify indexes are being used

### Priority 4: Documentation

7. **Update documentation**
   - Document new query approach in docs/db.md
   - Update API documentation
   - Document dual-write strategy

## Implementation Details

### Junction Table Query Pattern

```python
# Instead of: WHERE tags @> ARRAY['tag-uuid']
# Use: INNER JOIN content_tags ON content_id = id AND content_source = 'regular'
#      WHERE content_tags.tag_id = 'tag-uuid'
```

### Creator Filter Optimization

```python
# Current (inefficient):
if include_user_regular:
    query1 = ...filter(creator_id == user_id)
if include_community_regular:
    query2 = ...filter(creator_id != user_id)
# Then UNION query1 and query2

# Optimized:
if include_user_regular and include_community_regular:
    # Both selected - query all content, no creator filter
    query = ...  # No creator_id filter at all
elif include_user_regular:
    query = ...filter(creator_id == user_id)
elif include_community_regular:
    query = ...filter(creator_id != user_id)
# No UNION needed
```

### Dual-Write Pattern

```python
def _sync_tags_to_junction_table(
    self, content_id: int, content_source: str, tag_ids: List[UUID]
):
    """Sync tags from UUID array to junction table."""
    # Delete old relationships
    self.db.query(ContentTag).filter(
        ContentTag.content_id == content_id,
        ContentTag.content_source == content_source
    ).delete()

    # Insert new relationships
    for tag_id in tag_ids:
        self.db.add(ContentTag(
            content_id=content_id,
            content_source=content_source,
            tag_id=tag_id
        ))
```

## Files to Modify

1. `genonaut/db/schema.py` - ContentTag model (DONE)
2. `genonaut/api/services/content_service.py` - Query optimization
3. `genonaut/api/services/content_service.py` - Dual-write implementation
4. Tests in `tests/` directory
5. `docs/db.md` - Documentation

## Testing Strategy

1. **Unit tests**: Test individual methods work correctly
2. **Integration tests**: Test full query flows
3. **Performance tests**: Measure query execution time
4. **Regression tests**: Ensure existing functionality still works

## Rollback Plan

If issues arise:
1. Junction table queries are opt-in (only when tags filtered)
2. JSONB array queries still work as fallback
3. Can disable dual-write if needed
4. Data in both places ensures safety

## Success Criteria

- [ ] Tag-filtered gallery queries complete in < 1 second (p50)
- [ ] Tag-filtered gallery queries complete in < 3 seconds (p95)
- [ ] All existing tests pass
- [ ] New tests cover junction table queries
- [ ] Documentation updated
- [ ] Code reviewed and approved

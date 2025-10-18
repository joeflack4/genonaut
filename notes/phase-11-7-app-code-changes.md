# Phase 11.7: Application Code Changes for Partitioned Parent Table

## Overview

Now that `content_items_all` partitioned parent table exists, we can simplify the application code by querying a single table instead of building UNION queries between `content_items` and `content_items_auto`.

## Benefits

1. **Simpler Queries**: Query one table instead of building complex UNIONs
2. **Better Performance**: PostgreSQL can use partition pruning when filtering by `source_type`
3. **Cleaner Code**: Eliminate duplicate query building logic
4. **Easier Cursor Pagination**: Single table simplifies cursor encoding/decoding

## Changes Needed

### 1. Add SQLAlchemy Model for Parent Table

**File**: `genonaut/db/schema.py`

Add after the `ContentItemAuto` class:

```python
class ContentItemAll(ContentItemColumns, Base):
    """Partitioned parent table for unified content queries.

    This table partitions content_items and content_items_auto by source_type.
    Querying this table allows PostgreSQL to use partition pruning and eliminates
    the need for manual UNION queries.

    Note: INSERT/UPDATE/DELETE operations can target this table and will be
    automatically routed to the correct partition based on source_type.
    """
    __tablename__ = 'content_items_all'

    # Partition key - will route to correct child table
    # Values: 'items' (regular content) or 'auto' (auto-generated content)
    source_type = Column(Text, nullable=False, default='items', server_default='items')

    # No relationships defined - use child table models for relationships
    # This is a query-only model for unified content access

    @property
    def creator_username(self) -> Optional[str]:
        """Get creator username (requires join with User table in query)."""
        return getattr(self, '_creator_username', None)

    # Indexes are defined per-partition, not on parent
    __table_args__ = (
        # Unique constraint on (id, source_type) enforced via index
        # content_items_all_uidx_id_src created in migration
    )
```

### 2. Update ContentService.get_unified_content_paginated

**File**: `genonaut/api/services/content_service.py`

**Current Approach**: Builds separate queries for ContentItem and ContentItemAuto, adds UNION

**New Approach**: Query ContentItemAll once, filter by source_type

**Key Changes**:

```python
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
) -> Dict[str, Any]:
    """Get paginated content from partitioned parent table."""
    session = self.repository.db

    # Build single query against content_items_all
    query = session.query(
        ContentItemAll.id.label('id'),
        ContentItemAll.title.label('title'),
        ContentItemAll.content_type.label('content_type'),
        ContentItemAll.content_data.label('content_data'),
        ContentItemAll.path_thumb.label('path_thumb'),
        ContentItemAll.path_thumbs_alt_res.label('path_thumbs_alt_res'),
        ContentItemAll.prompt.label('prompt'),
        ContentItemAll.creator_id.label('creator_id'),
        ContentItemAll.item_metadata.label('item_metadata'),
        ContentItemAll.is_private.label('is_private'),
        ContentItemAll.quality_score.label('quality_score'),
        ContentItemAll.created_at.label('created_at'),
        ContentItemAll.updated_at.label('updated_at'),
        ContentItemAll.source_type.label('source_type'),
        User.username.label('creator_username')
    ).join(User, ContentItemAll.creator)

    # Apply source_type filter (enables partition pruning!)
    source_types_to_include = []

    if content_source_types:
        # Map content_source_types to source_type values
        if 'user-regular' in content_source_types or 'community-regular' in content_source_types:
            source_types_to_include.append('items')
        if 'user-auto' in content_source_types or 'community-auto' in content_source_types:
            source_types_to_include.append('auto')

    if source_types_to_include:
        # IMPORTANT: This WHERE clause enables PostgreSQL partition pruning
        query = query.filter(ContentItemAll.source_type.in_(source_types_to_include))

    # Apply creator filter
    if content_source_types:
        creator_filters = []

        if 'user-regular' in content_source_types or 'user-auto' in content_source_types:
            if user_id:
                creator_filters.append(ContentItemAll.creator_id == user_id)

        if 'community-regular' in content_source_types or 'community-auto' in content_source_types:
            if user_id:
                creator_filters.append(ContentItemAll.creator_id != user_id)

        if creator_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*creator_filters))

    # Apply search filter
    if search_term:
        query = self._apply_enhanced_search_filter(query, ContentItemAll, search_term)

    # Apply tag filter
    if tag_uuids:
        query = self._apply_tag_filter_via_junction(
            query,
            ContentItemAll,
            None,  # source_type_str not needed - already filtered above
            tag_uuids,
            tag_match_normalized,
        )

    # Apply sorting and pagination
    # ... rest of method remains similar
```

### 3. Update _apply_tag_filter_via_junction

**File**: `genonaut/api/services/content_service.py`

This method needs to be updated to work with ContentItemAll. The key change is that `source_type_str` parameter becomes optional since we're querying a single table.

```python
def _apply_tag_filter_via_junction(
    self,
    query,
    content_model,
    source_type_str: Optional[str],  # Make optional
    tag_uuids: List[UUID],
    tag_match: str = "any",
):
    """Apply tag filter using content_tags junction table.

    Args:
        query: SQLAlchemy query to filter
        content_model: ContentItem, ContentItemAuto, or ContentItemAll
        source_type_str: 'regular', 'auto', or None (for ContentItemAll)
        tag_uuids: List of tag UUIDs to filter by
        tag_match: 'any' or 'all'
    """
    if not tag_uuids:
        return query

    # When using ContentItemAll, source_type is already in the query
    # Junction table uses content_id for both partitions
    if tag_match == "all":
        # ALL: Item must have all specified tags
        for tag_uuid in tag_uuids:
            subq = (
                self.repository.db.query(ContentTag.content_id)
                .filter(ContentTag.tag_id == tag_uuid)
            )

            # Only add source_type filter if specified (not needed for ContentItemAll)
            if source_type_str:
                subq = subq.filter(ContentTag.source_type == source_type_str)

            query = query.filter(content_model.id.in_(subq))
    else:
        # ANY: Item must have at least one of the specified tags
        subq = (
            self.repository.db.query(ContentTag.content_id)
            .filter(ContentTag.tag_id.in_(tag_uuids))
        )

        if source_type_str:
            subq = subq.filter(ContentTag.source_type == source_type_str)

        query = query.filter(content_model.id.in_(subq))

    return query
```

### 4. Update get_unified_content_stats

**File**: `genonaut/api/services/content_service.py`

Simplify stats counting using ContentItemAll:

```python
def get_unified_content_stats(self, user_id: Optional[UUID] = None) -> Dict[str, int]:
    """Get unified content statistics using partitioned parent table."""
    session = self.repository.db

    # Query partitioned table with source_type grouping
    if user_id:
        user_stats = session.query(
            ContentItemAll.source_type,
            func.count(ContentItemAll.id)
        ).filter(
            ContentItemAll.creator_id == user_id
        ).group_by(ContentItemAll.source_type).all()

        user_regular_count = next((count for st, count in user_stats if st == 'items'), 0)
        user_auto_count = next((count for st, count in user_stats if st == 'auto'), 0)
    else:
        user_regular_count = 0
        user_auto_count = 0

    # Community stats
    community_stats = session.query(
        ContentItemAll.source_type,
        func.count(ContentItemAll.id)
    ).group_by(ContentItemAll.source_type).all()

    community_regular_count = next((count for st, count in community_stats if st == 'items'), 0)
    community_auto_count = next((count for st, count in community_stats if st == 'auto'), 0)

    return {
        "user_regular_count": user_regular_count,
        "user_auto_count": user_auto_count,
        "community_regular_count": community_regular_count,
        "community_auto_count": community_auto_count,
    }
```

## Testing Checklist

After implementing changes:

- [ ] Unit tests pass for unified content queries
- [ ] Integration tests pass for pagination
- [ ] Tag filtering works correctly (both ANY and ALL modes)
- [ ] Creator filtering (user vs community) works
- [ ] Search filtering works
- [ ] Cursor pagination works across partitions
- [ ] Performance tests show improvement (run EXPLAIN ANALYZE)
- [ ] Verify partition pruning with `EXPLAIN` when filtering by source_type

## Performance Verification

Run these queries to verify partition pruning is working:

```sql
-- Should scan only content_items partition
EXPLAIN ANALYZE
SELECT * FROM content_items_all
WHERE source_type = 'items'
ORDER BY created_at DESC
LIMIT 10;

-- Should scan only content_items_auto partition
EXPLAIN ANALYZE
SELECT * FROM content_items_all
WHERE source_type = 'auto'
ORDER BY created_at DESC
LIMIT 10;

-- Should scan both partitions
EXPLAIN ANALYZE
SELECT * FROM content_items_all
WHERE source_type IN ('items', 'auto')
ORDER BY created_at DESC
LIMIT 10;
```

Look for "Append" with partition scans in the EXPLAIN output.

## Migration Notes

**IMPORTANT**: These code changes require the database migration to be complete:
- Migration `e7526785bd0d` (adds source_type columns)
- Migration `86456c44a065` (creates partitioned parent table)

The application will fail if these migrations haven't been applied yet.

## Rollback Plan

If issues arise, rollback is simple:
1. Revert application code changes
2. Optionally run migration downgrade to remove partitioning
3. Original UNION-based queries will continue to work

The partitioned table is backward compatible - both child tables remain fully functional.

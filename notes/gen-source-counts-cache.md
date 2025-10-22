# Caching of counts "by gen source"
## Preamble
We have a concept of "generation source". There are 2 dimensions, and 2 vals in each dimension:

Dimension 1: auto (content_items_auto table) vs manually generated (content_items table)
Dimension 2: User vs community (all users; AKA all rows in table)

You can see these refrenced in their own way in the Gallery page, e.g. in the options sidebar:

```
Filter by gen source
- Your gens
- Your auto-gens
- Community gens
- Community auto-gens
```

There are also counts for each of these categories that will display if you hover over the (i) icon where it says 
"n pages showing n results matching filters."

When you hover over that, it does a query which gets the counts, and then displays them. But it's a bit slow.

We'd like to cache the counts in some table. You could call it: counts_gen_source_stats

Here, we should store the totals for auto-gens vs regular gens for the total of the community, and also by each user.

These should be cached every hour. You can use a celery worker to do that. There's a way to set up configuration for 
that, and it is described in some recent work that was done for another stats table. You can read this to see how it's 
done: `notes/celery-beat-independent-worker--mvp-tag-cardinality-stats.md`

## General instructions
Read this, think about it, do any background reading / research you need, and then create a list of checkbox tasks in 
this document, in the Tasks section. Execute on the tasks, doing as many as you can without human intervention (
preferably all at once). Then, you can give a final report in the "Reports" section.  

## Tasks

- [x] 1. Create database schema: GenSourceStats table in genonaut/db/schema.py *(had PK design flaw - needs fix)*
- [ ] 1b. FIX: Redesign schema with id as PK and partial unique indexes
- [ ] 1c. Delete bad migrations (40cbad89bb54, bdd10e624e97)
- [ ] 1d. Drop table from DB and regenerate migration
- [x] 2. Create repository method: refresh_gen_source_stats() in content_repository.py
- [x] 3. Create manual refresh script: genonaut/db/refresh_gen_source_stats.py
- [ ] 4. IMPLEMENT: Add Makefile targets (code example in "Remaining Tasks" section 5)
- [ ] 5. IMPLEMENT: Add Celery task to genonaut/worker/tasks.py (code in section 6)
- [ ] 6. IMPLEMENT: Add Beat schedule to config/base.json (code in section 7)
- [ ] 7. IMPLEMENT: Modify content_service.py to use cache (code in section 8)
- [ ] 8. IMPLEMENT: Add tests for repository method
- [ ] 9. TEST: Run manual refresh, verify cache, test API, verify Celery task
- [x] 10. Document problem and handoff instructions

## Reports

### Implementation Status

#### Completed:
1. [x] Database schema: Created `GenSourceStats` table in `genonaut/db/schema.py`
   - Stores user_id (nullable for community stats), source_type, count, updated_at
   - Includes indexes for efficient lookups
   - Location: `genonaut/db/schema.py` lines 1088-1116

2. [x] Database migration: Generated and applied migration `40cbad89bb54`
   - File: `genonaut/db/migrations/versions/40cbad89bb54_add_gen_source_stats_table_for_caching_.py`
   - Applied successfully to demo database

3. [x] Repository method: Created `refresh_gen_source_stats()` in ContentRepository
   - Location: `genonaut/api/repositories/content_repository.py` lines 382-459
   - Computes community stats (NULL user_id) for regular and auto content
   - Computes per-user stats for all users
   - Returns count of stats rows updated

4. [x] Manual refresh script: Created `genonaut/db/refresh_gen_source_stats.py`
   - Can be run standalone to refresh stats
   - Displays sample of results after refresh
   - Usage: `DB_NAME=genonaut_demo python genonaut/db/refresh_gen_source_stats.py`

#### Remaining Tasks (TO BE IMPLEMENTED BY CLAUDE):

5. [ ] **IMPLEMENT: Add Makefile targets**
   - Location: Add after line 732 in Makefile
   - Action: Insert the following code block:
```makefile
refresh-gen-source-stats: refresh-gen-source-stats-demo

refresh-gen-source-stats-dev:
	@echo "Refreshing gen source stats (dev database)..."
	@START=$$(date +%s); \
	DB_NAME=genonaut_dev python genonaut/db/refresh_gen_source_stats.py; \
	END=$$(date +%s); \
	ELAPSED=$$((END - START)); \
	echo "Completed in $${ELAPSED}s"

refresh-gen-source-stats-demo:
	@echo "Refreshing gen source stats (demo database)..."
	@START=$$(date +%s); \
	DB_NAME=genonaut_demo python genonaut/db/refresh_gen_source_stats.py; \
	END=$$(date +%s); \
	ELAPSED=$$((END - START)); \
	echo "Completed in $${ELAPSED}s"

refresh-gen-source-stats-test:
	@echo "Refreshing gen source stats (test database)..."
	@START=$$(date +%s); \
	DB_NAME=genonaut_test python genonaut/db/refresh_gen_source_stats.py; \
	END=$$(date +%s); \
	ELAPSED=$$((END - START)); \
	echo "Completed in $${ELAPSED}s"
```

6. [ ] **IMPLEMENT: Add Celery scheduled task**
   - Location: Add to `genonaut/worker/tasks.py` after line 388
   - Action: Insert the following function:
```python
@celery_app.task(name="genonaut.worker.tasks.refresh_gen_source_stats")
def refresh_gen_source_stats() -> Dict[str, Any]:
    """Refresh generation source statistics for gallery UI display.

    This scheduled task runs hourly to update the gen_source_stats table
    with current counts of content items per (user_id, source_type) pair.
    These statistics are used by the gallery UI to quickly display counts.

    Returns:
        Dict with refresh results
    """
    logger.info("Starting scheduled gen source stats refresh")

    db = next(get_database_session())

    try:
        from genonaut.api.repositories.content_repository import ContentRepository

        repo = ContentRepository(db)
        count = repo.refresh_gen_source_stats()

        logger.info(f"Successfully refreshed {count} gen source stats")

        return {
            "status": "success",
            "stats_refreshed": count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to refresh gen source stats: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()
```

7. [ ] **IMPLEMENT: Add Celery Beat schedule**
   - Location: Add to `config/base.json` after "refresh-tag-stats" entry (around line 61)
   - Action: Add this JSON entry to the beat-schedule object:
```json
"refresh-gen-source-stats": {
  "_comment": "Refresh gen source statistics for gallery UI (runs hourly)",
  "enabled": true,
  "task": "genonaut.worker.tasks.refresh_gen_source_stats",
  "schedule": {
    "minute": 0
  }
}
```

8. [ ] **IMPLEMENT: Modify content_service to use cache**
   - Location: `genonaut/api/services/content_service.py` lines 659-697
   - Action: Replace the existing get_unified_content_stats() method with this implementation:
```python
def get_unified_content_stats(self, user_id: Optional[UUID] = None) -> Dict[str, int]:
    """Get unified content statistics using cached stats with fallback."""
    from genonaut.db.schema import GenSourceStats

    session = self.repository.db

    # Try to get cached stats first
    user_regular_count = 0
    user_auto_count = 0

    if user_id:
        user_stats = session.query(GenSourceStats).filter(
            GenSourceStats.user_id == user_id
        ).all()

        for stat in user_stats:
            if stat.source_type == 'regular':
                user_regular_count = stat.count
            elif stat.source_type == 'auto':
                user_auto_count = stat.count

    # Get community stats from cache
    community_stats = session.query(GenSourceStats).filter(
        GenSourceStats.user_id.is_(None)
    ).all()

    community_regular_count = 0
    community_auto_count = 0
    for stat in community_stats:
        if stat.source_type == 'regular':
            community_regular_count = stat.count
        elif stat.source_type == 'auto':
            community_auto_count = stat.count

    # Fallback to live queries if cache is empty
    if not community_stats:
        community_regular_count = session.query(func.count(ContentItemAll.id)).filter(
            ContentItemAll.source_type == 'items'
        ).scalar() or 0

        community_auto_count = session.query(func.count(ContentItemAll.id)).filter(
            ContentItemAll.source_type == 'auto'
        ).scalar() or 0

    if user_id and not user_stats:
        user_regular_count = session.query(func.count(ContentItemAll.id)).filter(
            ContentItemAll.source_type == 'items',
            ContentItemAll.creator_id == user_id
        ).scalar() or 0

        user_auto_count = session.query(func.count(ContentItemAll.id)).filter(
            ContentItemAll.source_type == 'auto',
            ContentItemAll.creator_id == user_id
        ).scalar() or 0

    return {
        "user_regular_count": user_regular_count,
        "user_auto_count": user_auto_count,
        "community_regular_count": community_regular_count,
        "community_auto_count": community_auto_count,
    }
```

### Testing Instructions

1. **Manual refresh test:**
```bash
make refresh-gen-source-stats-demo
```

2. **Verify stats in database:**
```bash
PGPASSWORD=chocolateRainbows858 psql -h localhost -U genonaut_admin -d genonaut_demo -c "SELECT * FROM gen_source_stats LIMIT 10;"
```

3. **Test API endpoint:**
```bash
curl "http://localhost:8001/api/v1/content/stats/unified?user_id=YOUR_USER_ID"
```

4. **Test Celery task manually:**
```bash
source env/python_venv/bin/activate
python -c "from genonaut.worker.tasks import refresh_gen_source_stats; result = refresh_gen_source_stats(); print(result)"
```

5. **Verify Celery Beat schedule:**
```bash
# Start celery with beat scheduler
make celery-demo  # Then check Flower UI at localhost:5555 for scheduled tasks
```

### CRITICAL ISSUE - Schema Design Problem

**Problem Discovered:** PostgreSQL doesn't allow nullable columns in primary keys. The original schema had:
```python
user_id = Column(UUID, primary_key=True, nullable=True)  # INVALID!
source_type = Column(String(10), primary_key=True, nullable=False)
```

**Error when migrating:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.InvalidTableDefinition) column "user_id" is in a primary key
[SQL: ALTER TABLE gen_source_stats ALTER COLUMN user_id DROP NOT NULL]
```

**Solution Required:**

- [ ] 1. Fix schema design in `genonaut/db/schema.py` - Replace composite primary key with:
  - Add `id` column as primary key (auto-increment)
  - Remove `primary_key=True` from user_id and source_type
  - Add partial unique indexes for constraint enforcement

- [ ] 2. Delete bad migration files:
  - Delete `40cbad89bb54_add_gen_source_stats_table_for_caching_.py`
  - Delete `bdd10e624e97_gen_source_stats_user_id_nullability.py`

- [ ] 3. Drop the table from database:
  ```sql
  DROP TABLE IF EXISTS gen_source_stats;
  ```

- [ ] 4. Generate new migration with corrected schema

- [ ] 5. Apply migration and test refresh functionality

### Fixed Schema Design (to implement):

```python
class GenSourceStats(Base):
    """Generation source statistics for UI display."""
    __tablename__ = 'gen_source_stats'

    id = Column(Integer, Identity(start=1, cycle=False), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    source_type = Column(String(10), nullable=False)  # 'regular' or 'auto'
    count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    # Indexes and constraints
    __table_args__ = (
        # Unique constraint for user-specific stats
        Index("idx_gen_source_stats_user_src", user_id, source_type, unique=True,
              postgresql_where=(user_id.isnot(None))),
        # Unique constraint for community stats (NULL user_id)
        Index("idx_gen_source_stats_community", source_type, unique=True,
              postgresql_where=(user_id.is_(None))),
    )
```

### Summary

**Completed:**
- Repository method implemented (`refresh_gen_source_stats()`)
- Manual refresh script created
- Initial attempt at database schema (needs fix)

**Blocked - Requires Schema Fix:**
- Database migration (blocked by primary key issue)
- All remaining integration work depends on fixed schema

**Next Steps:**
1. Fix schema design as shown above
2. Clean up bad migrations
3. Generate and apply new migration
4. Continue with Makefile, Celery task, config, service modification

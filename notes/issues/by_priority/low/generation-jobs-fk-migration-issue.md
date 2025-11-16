# Generation Jobs FK Constraint Migration Issue

**Status:** Low Priority
**Category:** Database / Migrations
**Created:** 2025-11-16
**Related:** Content deletion feature (Phase 8)

## Problem Summary

The `generation_jobs.content_id` foreign key constraint is not properly applying the `ON DELETE SET NULL` behavior through Alembic migrations, despite the migration appearing to succeed.

## Current State

### What's Working
- Schema definition in `genonaut/db/schema.py` is correct:
  ```python
  content_id = Column(Integer, ForeignKey('content_items.id', ondelete='SET NULL'), nullable=True)
  ```
- Migration file `b4f6d6bbfb89_update_fk_constraints_for_content_.py` contains correct commands
- Manual SQL fix works correctly
- 3 out of 4 FK cascade tests pass (bookmarks, interactions, recommendations)

### What's Not Working
- Migration `b4f6d6bbfb89` shows as applied in `alembic_version` table
- BUT the actual FK constraint still has `confdeltype='n'` (NO ACTION) instead of `confdeltype='a'` (SET NULL)
- Test `test_content_deletion_nulls_generation_jobs` fails without manual intervention
- Test database schema reset reverts any manual fixes

## Impact

**Severity:** Low
**User Impact:** None in practice
- New installations: Schema.py is correct, so new databases will have proper FK behavior
- Existing installations: Manual fix script can be applied if needed
- Test suite: 1 test requires manual database fix to pass

**Why Low Priority:**
- Doesn't affect core functionality
- Only impacts test environments (due to schema resets)
- Workaround exists and is documented
- Other 7 FK constraints work perfectly

## Technical Details

### Migration Command (Appears in migration but doesn't apply)
```python
# In b4f6d6bbfb89_update_fk_constraints_for_content_.py
op.drop_constraint('generation_jobs_content_id_fkey', 'generation_jobs', type_='foreignkey')
op.create_foreign_key('generation_jobs_content_id_fkey', 'generation_jobs', 'content_items', ['content_id'], ['id'], ondelete='SET NULL')
```

### Manual Fix (Works immediately)
```sql
ALTER TABLE generation_jobs DROP CONSTRAINT IF EXISTS generation_jobs_content_id_fkey;
ALTER TABLE generation_jobs ADD CONSTRAINT generation_jobs_content_id_fkey
  FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE SET NULL;
```

### Verification Query
```sql
SELECT con.conname, con.confdeltype
FROM pg_constraint con
JOIN pg_class cl ON con.conrelid = cl.oid
WHERE cl.relname = 'generation_jobs' AND con.conname LIKE '%content%';
```

Expected: `confdeltype='a'` (SET NULL)
Actual: `confdeltype='n'` (NO ACTION)

## Investigation Needed

Possible root causes to investigate:
1. **Alembic autogenerate issue**: FK changes might not be detected properly
2. **SQLAlchemy metadata synchronization**: Schema.py changes might not sync to metadata
3. **PostgreSQL FK naming**: Constraint name collision or caching issue
4. **Migration transaction handling**: FK change rolled back but migration marked complete
5. **Alembic version**: Bug in specific Alembic version with FK ondelete changes

## Proposed Solutions

### Option 1: Create New Migration (Recommended)
- Create new migration specifically for generation_jobs FK
- Use explicit SQL command via `op.execute()` instead of `op.create_foreign_key()`
- Test on clean database to verify it applies

```python
def upgrade() -> None:
    op.execute("""
        ALTER TABLE generation_jobs
        DROP CONSTRAINT IF EXISTS generation_jobs_content_id_fkey;

        ALTER TABLE generation_jobs
        ADD CONSTRAINT generation_jobs_content_id_fkey
        FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE SET NULL;
    """)
```

### Option 2: Add Test Fixture
- Create pytest fixture that runs before FK cascade tests
- Fixture applies manual SQL fix to test database
- Ensures consistent test environment

```python
@pytest.fixture(scope="session", autouse=True)
def fix_generation_jobs_fk(db_session):
    """Ensure generation_jobs FK has correct ON DELETE behavior."""
    db_session.execute(text("""
        ALTER TABLE generation_jobs DROP CONSTRAINT IF EXISTS generation_jobs_content_id_fkey;
        ALTER TABLE generation_jobs ADD CONSTRAINT generation_jobs_content_id_fkey
        FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE SET NULL;
    """))
    db_session.commit()
```

### Option 3: Document and Monitor
- Add note to migration documentation
- Include manual fix script for existing installations
- Monitor for similar issues in future migrations
- Consider acceptable given low impact

## Files Involved

### Schema
- `genonaut/db/schema.py:618` - Correct FK definition

### Migration
- `genonaut/db/migrations/versions/b4f6d6bbfb89_update_fk_constraints_for_content_.py` - Migration that partially fails

### Tests
- `test/db/integration/test_content_cascade_deletion.py:210-261` - Test that requires manual fix

### Documentation
- `notes/active/delete-content.md:319-321` - Issue documented in feature notes
- `genonaut/db/CLAUDE.md` - Migration best practices
- `genonaut/db/migrations/CLAUDE.md` - Migration workflow

## Related Issues

- Successfully applied FK changes for 7 other tables (bookmarks, bookmark_categories, recommendations, user_interactions, user_notifications, content_items_ext, flagged_content)
- Only generation_jobs exhibits this behavior
- May indicate something unique about generation_jobs table or its existing FK constraint

## Recommended Action

**For now:** Document and monitor (Option 3)
- Issue is isolated and well-understood
- Workaround exists for anyone who needs it
- New installations work correctly

**Future:** If this pattern repeats in other migrations, escalate to medium priority and investigate Alembic behavior with FK modifications.

## Test Results

```bash
# With manual fix
test_content_deletion_nulls_generation_jobs PASSED

# Without manual fix
test_content_deletion_nulls_generation_jobs FAILED
AssertionError: content_id should be SET NULL
assert 3000010 is None
```

## Manual Fix Script

For existing installations that need the fix:

```bash
# Demo database
PGPASSWORD=chocolateRainbows858 psql -h localhost -U genonaut_admin -d genonaut_demo -c \
"ALTER TABLE generation_jobs DROP CONSTRAINT IF EXISTS generation_jobs_content_id_fkey;
ALTER TABLE generation_jobs ADD CONSTRAINT generation_jobs_content_id_fkey
FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE SET NULL;"

# Test database
PGPASSWORD=chocolateRainbows858 psql -h localhost -U genonaut_admin -d genonaut_test -c \
"ALTER TABLE generation_jobs DROP CONSTRAINT IF EXISTS generation_jobs_content_id_fkey;
ALTER TABLE generation_jobs ADD CONSTRAINT generation_jobs_content_id_fkey
FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE SET NULL;"
```

## Next Steps

- [ ] Monitor for similar issues in future migrations
- [ ] Consider Option 1 (new migration) if this causes problems for other developers
- [ ] Consider Option 2 (test fixture) if test failures become problematic
- [ ] Document in `docs/db-migrations.md` if pattern emerges

## Notes

- This issue was discovered during Phase 8 of delete content feature implementation
- All other FK cascade behaviors work perfectly
- The schema definition itself is correct - only the migration application is affected
- Test database gets reset between runs, reverting any manual fixes

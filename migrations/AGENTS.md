# Database Migrations Guide

This file provides guidance to Claude Code when working with database migrations.

## Critical Migration Rules
**NEVER EDIT EXISTING MIGRATION FILES**: All files in `genonaut/db/migrations/versions/` are immutable history. Always create new migrations for changes.

## Environment Setup
**IMPORTANT**: Always activate virtual environment first:
```bash
source env/bin/activate
```

## Migration Workflow (SOP)
### Standard Operating Procedure for Schema Changes:
1. **Modify SQLAlchemy models** (never write raw SQL directly)
2. **Create revision using autogenerate**:
   ```bash
   make migrate-demo     # For demo database
   make migrate-all      # For all databases
   ```
3. **Review generated script** in `alembic/versions/*.py`
4. **Test migration**: `alembic upgrade head`

### Pre-Migration Checklist:
- [ ] Sync with main branch
- [ ] Run `PYTHONPATH=. alembic heads` to confirm exactly one head
- [ ] Check current database state with `alembic current`
- [ ] Ensure target database is on the same head

### Migration Commands:
```bash
# Check migration status
alembic heads                    # Should show exactly one head
alembic current                  # Show current migration state

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head             # Apply to current database
make migrate-all                 # Apply to all environments
```

## Safe Migration Patterns
### For Production:
- **Forward-only**: Prefer forward fixes in production, avoid downgrades
- **Two-step drops**: Stop writes → (optional) archive data → drop in next release
- **Non-null columns**: Add with `server_default`, backfill, then remove default
- **Archive strategy**: Copy to `archive_*` table before destructive operations

### Concurrent Index Creation:
```python
from alembic import op
# Outside transaction for PostgreSQL:
with op.get_context().autocommit_block():
    op.create_index("ix_users_email", "users", ["email"],
                   unique=True, postgresql_concurrently=True)
```

## Troubleshooting Common Issues
### Multiple Heads Error:
```bash
# If alembic heads shows >1 head:
alembic merge -m "merge heads" <head1> <head2>
alembic upgrade head
```

### Empty Autogenerate:
- Ensure `target_metadata = Base.metadata` in `env.py`
- Check `__init__.py` imports so models are loaded
- Use `compare_type=True` and `compare_server_default=True`

### Production Reverts:
- **Don't downgrade in prod**: Ship new forward migration instead
- Create shadow column → backfill → swap → drop old column

## Testing Migrations
Always test migrations thoroughly:
```bash
# Test on development database
make init-test              # Initialize test database
alembic upgrade head        # Apply migration
make test-db               # Run database tests
```

## File Management
### What to Commit:
- Model changes in SQLAlchemy files
- New migration files in `alembic/versions/`
- Updated `alembic.ini` if needed
- Updated `alembic/env.py` if needed

### What NOT to Commit:
- Actual database files
- Local `.env` files
- Database credentials

## Documentation Requirements
- Add clear migration message describing the change
- Document complex migrations with comments in the migration file
- Update schema documentation if making significant changes
- Consider updating `docs/db_migrations.md` for new patterns
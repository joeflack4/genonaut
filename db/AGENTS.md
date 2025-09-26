# Database Development Guide

This file provides guidance to Claude Code when working with database code in this repository.

## Environment Setup
**CRITICAL**: Always activate the virtual environment before any database work:
```bash
source env/bin/activate
```

## Database Schema Changes
**NEVER** edit existing Alembic migration files in `genonaut/db/migrations/versions/`! They are immutable history.

### Standard Operating Procedure for Schema Changes:
1. **Modify SQLAlchemy models** (not raw SQL)
2. **Create new migration**: Use `make migrate-*` commands (e.g., `make migrate-demo`, `make migrate-all`)
3. **Review generated migration** in `alembic/versions/*.py`
4. **Test migration** with `alembic upgrade head`

### Before Creating Migrations:
- Sync with main branch
- Run `PYTHONPATH=. alembic heads` to confirm exactly one head
- Check current database state with `alembic current`

## Database Testing
Follow the three-tier testing approach:
- **Unit tests**: `make test-unit` (no database required)
- **Database tests**: `make test-db` (requires database)
- **API integration**: `make test-api` (requires web server + database)

Always initialize test database: `make init-test`

## Key Commands
```bash
# Database initialization
make init              # Main database
make init-demo         # Demo database
make init-test         # Test database

# Migrations
make migrate-all       # All databases
make migrate-demo      # Demo database only

# Testing
make test-db           # Database tests
make test-db-unit      # DB unit tests (no DB required)
make test-db-integration # DB integration tests (DB required)
```

## Code Style
- Use types for all function/method parameters
- Write pure functions whenever possible
- Add comprehensive docstrings (module, class, function level)
- Include periodic code comments for complex blocks

## Documentation Requirements
- Update docstrings when modifying database functions
- Add test coverage for new database functionality
- Consider updating `docs/db.md` for significant changes
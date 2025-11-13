# Developer Documentation

This directory contains comprehensive documentation for Genonaut development.

## Table of Contents

### Core Documentation
- [Database Documentation](./db.md) - Database setup, schema, JSONB usage, and maintenance
- [API Documentation](./api.md) - FastAPI endpoints, configuration, and integration
- [Testing Documentation](./testing.md) - Testing strategy, commands, and best practices
- [Frontend Documentation](../notes/frontend.md) - Frontend development guide and recommendations
- [Queuing system](./queuing.md) - Queuing system for processing tasks

### Specialized Documentation
- [Database Migrations](db-migrations.md) - Alembic migration procedures and troubleshooting
- [Tag Ontology](./tag_ontology.md) - Hierarchical tag classification and semantic organization
- [Tag System Implementation](../notes/issues/complete/uncategorized/tags-db-and-gallery-and-view.md) - Database-backed tag system with ratings, hierarchy, and gallery filtering

## Quick Reference

### Essential Commands
- `make init` - Initialize main database
- `make api-dev` / `make api-demo` - Start API server (development / demo)
- `make test-all` - Run complete test suite

### Development Workflow
1. **Setup:** Follow database setup in [db.md](./db.md)
2. **API Development:** See endpoint documentation in [api.md](./api.md)
3. **Testing:** Use testing strategy from [testing.md](./testing.md)
4. **Frontend:** Plan frontend development with [frontend.md](../notes/frontend.md)

### Documentation Updates
When adding new features or making significant changes:
1. Update relevant documentation files
2. Keep README.md summary sections in sync
3. Add new specialized docs to this index
4. Update code examples and command references

### Statement Timeout Testing
- Lower `statement-timeout` in your local `config/local-dev.json` (e.g., `"1s"`) and restart the API.
- Execute a slow query (e.g., `SELECT pg_sleep(2)`) via psql or a temporary endpoint to confirm the backend raises a `StatementTimeoutError`.
- Watch the API logs for the structured timeout warning.
- Trigger the same operation from the frontend to verify the timeout snackbar appears and can be dismissed.
- Restore the timeout to its normal value after testing.

### Debugging Hangs with Faulthandler

Genonaut automatically registers Python's `faulthandler` module to help diagnose application hangs and deadlocks.

#### How to Use

1. **Find the API process ID:**
   ```bash
   ps aux | grep uvicorn
   # or
   lsof -i :8001
   ```

2. **Dump stack traces:**
   ```bash
   kill -USR1 <pid>
   ```

3. **View the stack traces** in the terminal where the API is running or in the API logs.

#### Configuration

Faulthandler is enabled by default. To disable it, add to your config:

```json
{
  "enable-faulthandler": false
}
```

#### Use Cases

- **Application appears hung:** Send SIGUSR1 to see what all threads are doing
- **Slow requests:** Identify which code path is taking time
- **Deadlock debugging:** See which threads are waiting on what
- **Development debugging:** Understand control flow during development

#### Example Output

```
Current thread 0x00007f9876543210 (most recent call first):
  File "/path/to/file.py", line 123, in function_name
  File "/path/to/other.py", line 456, in other_function
  ...
```

This shows the complete stack trace for all Python threads, helping identify bottlenecks and hangs.

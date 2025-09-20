# Developer Documentation

This directory contains comprehensive documentation for Genonaut development.

## Table of Contents

### Core Documentation
- [Database Documentation](./db.md) - Database setup, schema, JSONB usage, and maintenance
- [API Documentation](./api.md) - FastAPI endpoints, configuration, and integration
- [Testing Documentation](./testing.md) - Testing strategy, commands, and best practices
- [Frontend Documentation](./frontend.md) - Frontend development guide and recommendations

### Specialized Documentation
- [Database Migrations](./db_migrations.md) - Alembic migration procedures and troubleshooting

## Quick Reference

### Essential Commands
- `make init` - Initialize main database
- `make api-dev` - Start API server (development)
- `make test-all` - Run complete test suite
- `make test-unit` - Run unit tests only

### Development Workflow
1. **Setup:** Follow database setup in [db.md](./db.md)
2. **API Development:** See endpoint documentation in [api.md](./api.md)
3. **Testing:** Use testing strategy from [testing.md](./testing.md)
4. **Frontend:** Plan frontend development with [frontend.md](./frontend.md)

### Documentation Updates
When adding new features or making significant changes:
1. Update relevant documentation files
2. Keep README.md summary sections in sync
3. Add new specialized docs to this index
4. Update code examples and command references
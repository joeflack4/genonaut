# Test Database and Server Troubleshooting Guide

This guide covers common issues and solutions when working with Genonaut's test infrastructure, including database setup, server startup, and E2E test execution.

## Quick Diagnostic Commands

```bash
# Check if test database is accessible
python -c "from genonaut.db.init import get_database_url; print(get_database_url('test'))"

# Check if test server is running
curl -f http://localhost:8002/api/v1/health || echo "Test server not responding"

# Check test data seed status
python -m genonaut.db.init --check-playwright-fixtures

# Verify environment variables
python -c "import os; print('APP_ENV:', os.getenv('APP_ENV', 'Not set')); print('DATABASE_URL_TEST:', os.getenv('DATABASE_URL_TEST', 'Not set'))"
```

## Common Issues and Solutions

### Database Issues

#### Issue: "Database connection failed" or "relation does not exist"

**Symptoms:**
- Backend tests fail with connection errors
- API server won't start
- Migration errors

**Solutions:**

```bash
# 1. Check database connection
psql $DATABASE_URL_TEST -c "SELECT 1;" || echo "Connection failed"

# 2. Reinitialize test database
make init-test

# 3. For PostgreSQL test database
make init-test

# 4. Check environment variables
echo "DATABASE_URL_TEST: $DATABASE_URL_TEST"
echo "DATABASE_URL: $DATABASE_URL"
```

#### Issue: "Test data insufficient" or "Zero results" in Playwright tests

**Symptoms:**
- Playwright real API tests skip with "insufficient test data"
- Gallery tests show zero results
- Pagination tests can't run

**Solutions:**

```bash
# 1. Check current test data
python -m genonaut.db.init --check-playwright-fixtures

# 2. Re-export fresh test data from demo database
make export-demo-data

# 3. Reinitialize with new data
make init-test

# 4. Verify data was loaded
PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB_TEST -c "
SELECT
  (SELECT COUNT(*) FROM content_items) as content_items,
  (SELECT COUNT(*) FROM content_items_auto) as auto_content_items;
"
```

#### Issue: "Schema version mismatch" or migration errors

**Symptoms:**
- Database initialization fails
- API server startup fails with schema errors
- Migration commands fail

**Solutions:**

```bash
# 1. Check current schema version
alembic current

# 2. Reset database with clean slate
make reset-db-3-schema-and-history--test

# 3. Run migrations manually
make migrate-test

# 4. For development database
make reset-db-3-schema-and-history--dev
make migrate-dev
```

### Server Issues

#### Issue: "Test server not available on port 8002"

**Symptoms:**
- Playwright real API tests skip
- curl to localhost:8002 fails
- Health check endpoint unreachable

**Solutions:**

```bash
# 1. Check if port is in use
lsof -i :8002 || echo "Port 8002 is free"

# 2. Check if test server process is running
ps aux | grep "uvicorn.*8002" || echo "No test server running"

# 3. Start test server manually
make api-test

# 4. Start test server for Playwright (automatic)
npm --prefix frontend run test:e2e:real-api

# 5. Kill orphaned servers
pkill -f "uvicorn.*8002"

# 6. Check server logs
APP_ENV=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8002 --log-level debug
```

#### Issue: "API server starts but returns 500 errors"

**Symptoms:**
- Server starts successfully
- Health check fails
- All API endpoints return 500

**Solutions:**

```bash
# 1. Check server logs
APP_ENV=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8002 --log-level debug

# 2. Verify database connection
curl http://localhost:8002/api/v1/database-info

# 3. Check for missing dependencies
pip install -r requirements.txt

# 4. Verify environment setup
APP_ENV=test python -c "from genonaut.api.main import app; print('App created successfully')"
```

### Playwright Test Issues

#### Issue: "Real API server not available" skips

**Symptoms:**
- All real API tests are skipped
- Tests don't run against actual API
- Only mock tests execute

**Solutions:**

```bash
# 1. Use the real API test command (starts server automatically)
make frontend-test-e2e-real-api

# 2. Or start server manually first
make api-test
# Then in another terminal:
make frontend-test-e2e

# 3. Check Playwright configuration
cat frontend/playwright-real-api.config.ts | grep baseURL

# 4. Verify test server health
curl http://localhost:8002/api/v1/health
```

#### Issue: "Browser launch failed" or Playwright setup errors

**Symptoms:**
- Playwright tests fail to start
- Browser installation errors
- Timeout waiting for browser

**Solutions:**

```bash
# 1. Install/update Playwright browsers
cd frontend
npx playwright install

# 2. Clear Playwright cache
npx playwright install --force

# 3. Check system dependencies (Linux)
npx playwright install-deps

# 4. Run with headed mode for debugging
npm run test:e2e:headed
```

#### Issue: "Test timeout" or slow test execution

**Symptoms:**
- Tests timeout after 30 seconds
- Slow page loading
- Database queries taking too long

**Solutions:**

```bash
# 1. Increase timeout in test configuration
# Edit frontend/playwright.config.ts: timeout: 60000

# 2. Check database performance
time curl "http://localhost:8002/api/v1/content/unified?page=1&page_size=10"

# 3. Optimize test database
PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB_TEST -c "VACUUM ANALYZE;"

# 4. Run tests with longer timeout
PLAYWRIGHT_TIMEOUT=60000 npm run test:e2e:real-api
```

### Frontend Issues

#### Issue: "Module not found" or dependency errors

**Symptoms:**
- Frontend tests fail to start
- Import errors in test files
- TypeScript compilation errors

**Solutions:**

```bash
# 1. Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install

# 2. Clear TypeScript cache
npx tsc --build --clean

# 3. Update dependencies
npm update

# 4. Check for version conflicts
npm ls
```

#### Issue: "Test data mismatch" between frontend and API

**Symptoms:**
- Frontend expects different data format
- API returns unexpected structure
- Type mismatches in tests

**Solutions:**

```bash
# 1. Check API response format
curl "http://localhost:8002/api/v1/content/unified?page=1&page_size=1" | jq .

# 2. Update TypeScript types
cd frontend
npm run type-check

# 3. Regenerate API client if using code generation
# (Add your API client regeneration command here)

# 4. Compare expected vs actual data in tests
npm run test:e2e:ui  # Use Playwright UI for debugging
```

## Environment Setup Verification

### Complete Environment Check

```bash
#!/bin/bash
echo "=== Genonaut Test Environment Check ==="

# 1. Python environment
echo "Python version: $(python --version)"
echo "Virtual environment: ${VIRTUAL_ENV:-Not activated}"

# 2. Database connectivity
echo "Checking database connections..."
python -c "
import os
from genonaut.db.init import get_database_url
try:
    print('Test DB URL:', get_database_url('test'))
    print('Demo DB URL:', get_database_url('demo'))
except Exception as e:
    print('Database URL error:', e)
"

# 3. API server health
echo "Checking API servers..."
curl -s http://localhost:8001/api/v1/health && echo "Main API: ✓" || echo "Main API: ✗"
curl -s http://localhost:8002/api/v1/health && echo "Test API: ✓" || echo "Test API: ✗"

# 4. Frontend dependencies
echo "Frontend setup..."
cd frontend
npm ls --depth=0 | head -5
npx playwright --version || echo "Playwright not installed"

# 5. Test data status
echo "Test data status..."
python -m genonaut.db.init --check-playwright-fixtures || echo "Test data check failed"

echo "=== End Environment Check ==="
```

### Reset Everything

```bash
#!/bin/bash
echo "=== Complete Test Environment Reset ==="

# 1. Stop all servers
pkill -f "uvicorn.*800[12]" || echo "No servers to kill"

# 2. Clean databases
make reset-db-3-schema-and-history--test
make reset-db-3-schema-and-history--dev

# 3. Regenerate test data
make export-demo-data

# 4. Reinitialize everything
make init-test
make init-dev

# 5. Reinstall frontend dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npx playwright install

# 6. Run verification tests
cd ..
make test-quick
make frontend-test-unit
make frontend-test-e2e

echo "=== Reset Complete ==="
```

## Performance Troubleshooting

### Database Performance

```bash
# Check PostgreSQL database size
PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB_TEST -c "
SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB_TEST')) as database_size;
"

# Analyze query performance
time curl "http://localhost:8002/api/v1/content/unified?page=50&page_size=10"

# Optimize PostgreSQL database
PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB_TEST -c "VACUUM ANALYZE;"
```

### Memory Usage

```bash
# Monitor memory usage during tests
#!/bin/bash
echo "Monitoring memory usage..."
while true; do
    ps -o pid,rss,command -p $(pgrep -f "uvicorn.*8002" | head -1) 2>/dev/null || echo "No test server running"
    sleep 5
done
```

### Test Execution Performance

```bash
# Time individual test suites
time make test-unit
time make test-db
time make frontend-test-unit
time make frontend-test-e2e

# Profile specific test
time npx playwright test tests/e2e/gallery-real-api.spec.ts --reporter=line
```

## Getting Help

### Collect Diagnostic Information

```bash
#!/bin/bash
echo "=== Genonaut Test Diagnostics ==="
echo "Date: $(date)"
echo "OS: $(uname -a)"
echo "Python: $(python --version)"
echo "Node: $(node --version)"
echo "Environment variables:"
env | grep -E "(DATABASE_URL|APP_ENV|GENONAUT)" | sort
echo ""
echo "Test server processes:"
ps aux | grep -E "(uvicorn|genonaut)" | grep -v grep
echo ""
echo "Network connections:"
lsof -i :8001,8002 2>/dev/null || echo "No connections on ports 8001, 8002"
echo ""
echo "Recent test files:"
find . -name "test_*.db" -o -name "*.log" | head -10
echo "=== End Diagnostics ==="
```

### Debug Mode

For detailed debugging, run commands with verbose flags:

```bash
# Backend API with debug logging
APP_ENV=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8002 --log-level debug --reload

# Playwright with debug mode
DEBUG=pw:api npm run test:e2e:real-api

# Database operations with verbose output
python -m genonaut.db.init --verbose

# Frontend tests with debug info
npm run test:unit -- --reporter=verbose
```

## Automated Health Checks

Add this to your development workflow:

```bash
# .git/hooks/pre-commit (make executable)
#!/bin/bash
echo "Running health checks..."

# Quick environment verification
python -c "from genonaut.db.init import get_database_url; get_database_url('test')" || exit 1
make test-unit || exit 1
cd frontend && npm run test-unit || exit 1

echo "Health checks passed ✓"
```

This troubleshooting guide should help resolve the most common issues encountered when working with Genonaut's test infrastructure. Keep it updated as new issues and solutions are discovered.
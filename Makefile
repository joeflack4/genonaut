# Common development tasks and utilities
.PHONY: help init-all init-dev init-demo init-test reset-db-1-data--demo reset-db-1-data--test reset-db-2-schema--demo \
reset-db-2-schema--test reset-db-3-schema-and-history--demo reset-db-3-schema-and-history--test re-seed-demo \
re-seed-demo-force seed-from-gen-demo seed-from-gen-test export-demo-data test test-quick test-verbose test-specific test-unit test-db \
test-db-unit test-db-integration test-api test-all clear-excess-test-schemas install install-dev \
lint format clean migrate-all migrate-prep migrate-dev migrate-demo migrate-test backup backup-dev backup-demo \
backup-test api-dev api-demo api-test celery-dev celery-demo celery-test flower-dev flower-demo flower-test \
redis-flush-dev redis-flush-demo redis-flush-test redis-keys-dev redis-keys-demo redis-keys-test \
redis-info-dev redis-info-demo redis-info-test \
frontend-install frontend-dev frontend-build frontend-preview frontend-test \
frontend-test-unit frontend-test-watch frontend-test-coverage frontend-test-e2e frontend-test-e2e-headed \
frontend-test-e2e-ui frontend-test-e2e-real-api frontend-test-e2e-real-api-headed frontend-test-e2e-real-api-ui \
frontend-lint frontend-type-check frontend-format frontend-format-write \
test-frontend test-frontend-unit test-frontend-watch test-frontend-coverage test-frontend-e2e test-frontend-e2e-headed \
test-frontend-e2e-ui test-frontend-e2e-real-api test-frontend-e2e-real-api-headed test-frontend-e2e-real-api-ui db-wal-buffers-reset db-wal-buffers-set init-db init-db-drop test-long-running test-coverage docs \
check-env api-dev-profile api-dev-load-test api-production-sim api-demo-load-test api-test-load-test \
clear-excess-test-schemas-keep-3 migrate-down-dev migrate-heads-dev migrate-down-demo migrate-heads-demo \
ontology-refresh ontology-generate ontology-validate ontology-stats ontology-test ontology-json \
md-collate md-export-tsv md-test md-github-sync-down md-github-sync-up md-github-sync

# Load environment variables
ifneq (,$(wildcard ./env/.env))
include ./env/.env
export  # export included vars to child processes
endif

# help: Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "  help                     Show this help message"
	@echo ""
	@echo "Development Lifecycle:"
	@echo "  install                  Install project dependencies"
	@echo "  install-dev              Install development dependencies"
	@echo "  lint                     Run code linting"
	@echo "  format                   Format code"
	@echo "  clean                    Clean temporary files"
	@echo "  check-env                Check environment setup"
	@echo ""
	@echo "Database Initialization:"
	@echo "  init-all                 Initialize all databases (dev, demo, test)"
	@echo "  init-dev                 Initialize development database"
	@echo "  init-demo                Initialize demo database"
	@echo "  init-test                Initialize test database"
	@echo "  init-db                  Alias for init-dev"
	@echo "  init-db-drop             Initialize database, dropping existing tables"
	@echo ""
	@echo "Database Reset:"
	@echo "  reset-db-1-data--demo            Truncate and re-initialize the demo database"
	@echo "  reset-db-1-data--test            Truncate and re-initialize the test database"
	@echo "  reset-db-2-schema--demo          Drop and re-initialize the demo database schema"
	@echo "  reset-db-2-schema--test          Drop and re-initialize the test database schema"
	@echo "  reset-db-3-schema-and-history--demo Reset demo database with migration history cleanup"
	@echo "  reset-db-3-schema-and-history--test Reset test database with migration history cleanup"
	@echo ""
	@echo "Database Seeding:"
	@echo "  re-seed-demo             Re-seed demo database (prompts for confirmation)"
	@echo "  re-seed-demo-force       Re-seed demo database (no confirmation prompt)"
	@echo "  seed-from-gen-demo       Generate synthetic data for demo database"
	@echo "  seed-from-gen-test       Generate synthetic data for test database"
	@echo "  export-demo-data         Export demo database data to test TSV files"
	@echo ""
	@echo "Database Migration:"
	@echo "  migrate-all              Create and apply migrations for all databases"
	@echo "  migrate-prep             Create a new migration revision"
	@echo "  migrate-dev              Upgrade main database schema"
	@echo "  migrate-demo             Upgrade demo database schema"
	@echo "  migrate-test             Upgrade test database schema"
	@echo "  migrate-down-dev         Downgrade development database by one revision"
	@echo "  migrate-heads-dev        Show current heads for development database"
	@echo "  migrate-down-demo        Downgrade demo database by one revision"
	@echo "  migrate-heads-demo       Show current heads for demo database"
	@echo ""
	@echo "Testing (Backend):"
	@echo "  test / test-quick        Run quick tests (< 2 minutes)"
	@echo "  test-long-running        Run performance/stress tests (5-15 minutes)"
	@echo "  test-verbose             Run all tests with verbose output"
	@echo "  test-specific TEST=name  Run specific test module or test case"
	@echo "  test-unit                Run unit tests (no external dependencies)"
	@echo "  test-db                  Run database tests (requires database)"
	@echo "  test-db-unit             Run database unit tests"
	@echo "  test-db-integration      Run database integration tests"
	@echo "  test-api                 Run API integration tests (requires web server)"
	@echo "  test-all                 Run all tests (quick + long-running)"
	@echo "  test-coverage            Run tests with coverage report"
	@echo ""
	@echo "Database Management:"
	@echo "  clear-excess-test-schemas      Clear excess test database schemas"
	@echo "  clear-excess-test-schemas-keep-3 Clear excess test schemas, keeping the 3 latest"
	@echo "  backup                   Backup all databases (dev, demo, test)"
	@echo "  backup-dev               Backup development database"
	@echo "  backup-demo              Backup demo database"
	@echo "  backup-test              Backup test database"
	@echo ""
	@echo "PostgreSQL wal_buffers management:"
	@echo "  db-wal-buffers-reset     Reset wal_buffers to 4MB (requires PostgreSQL restart)"
	@echo "  db-wal-buffers-set VALUE Set wal_buffers to VALUE (e.g., 64MB, requires restart)"
	@echo ""
	@echo "API Server:"
	@echo "  api-dev                  Start FastAPI server for development"
	@echo "  api-demo                 Start FastAPI server for demo"
	@echo "  api-test                 Start FastAPI server for testing"
	@echo "  api-dev-profile          Start FastAPI for development with profiling"
	@echo "  api-dev-load-test        Start FastAPI for development load testing"
	@echo "  api-production-sim       Start FastAPI simulating production"
	@echo "  api-demo-load-test       Start FastAPI for demo load testing"
	@echo "  api-test-load-test       Start FastAPI for test load testing"
	@echo ""
	@echo "Celery Workers:"
	@echo "  celery-dev               Start Celery worker for development"
	@echo "  celery-demo              Start Celery worker for demo"
	@echo "  celery-test              Start Celery worker for test"
	@echo ""
	@echo "Flower Monitoring:"
	@echo "  flower-dev               Start Flower dashboard for development (port 5555)"
	@echo "  flower-demo              Start Flower dashboard for demo (port 5555)"
	@echo "  flower-test              Start Flower dashboard for test (port 5555)"
	@echo ""
	@echo "Redis Management:"
	@echo "  redis-flush-dev          Flush development Redis DB (DB 4)"
	@echo "  redis-flush-demo         Flush demo Redis DB (DB 2)"
	@echo "  redis-flush-test         Flush test Redis DB (DB 3)"
	@echo "  redis-keys-dev           List keys in development Redis DB"
	@echo "  redis-keys-demo          List keys in demo Redis DB"
	@echo "  redis-keys-test          List keys in test Redis DB"
	@echo "  redis-info-dev           Show Redis info for development DB"
	@echo "  redis-info-demo          Show Redis info for demo DB"
	@echo "  redis-info-test          Show Redis info for test DB"
	@echo ""
	@echo "Frontend:"
	@echo "  frontend-install         Install frontend dependencies"
	@echo "  frontend-dev             Start frontend dev server"
	@echo "  frontend-build           Build frontend for production"
	@echo "  frontend-preview         Preview built frontend"
	@echo "  frontend-lint            Lint frontend code"
	@echo "  frontend-type-check      Type-check frontend code"
	@echo "  frontend-format          Check frontend formatting"
	@echo "  frontend-format-write    Format frontend code"
	@echo ""
	@echo "Testing (Frontend):"
	@echo "  frontend-test            Run all frontend tests (unit + e2e)"
	@echo "  frontend-test-unit       Run frontend unit tests only"
	@echo "  frontend-test-watch      Run frontend tests in watch mode"
	@echo "  frontend-test-coverage   Run frontend tests with coverage"
	@echo "  frontend-test-e2e        Run frontend Playwright e2e tests"
	@echo "  frontend-test-e2e-headed Run Playwright tests in headed mode"
	@echo "  frontend-test-e2e-ui     Run Playwright UI mode"
	@echo "  frontend-test-e2e-real-api Run Playwright tests with real API server"
	@echo "  frontend-test-e2e-real-api-headed Run real API tests in headed mode"
	@echo "  frontend-test-e2e-real-api-ui Run real API tests in UI mode"
	@echo ""
	@echo "Frontend Test Aliases (test-frontend*):"
	@echo "  test-frontend            Alias for frontend-test"
	@echo "  test-frontend-unit       Alias for frontend-test-unit"
	@echo "  test-frontend-watch      Alias for frontend-test-watch"
	@echo "  test-frontend-coverage   Alias for frontend-test-coverage"
	@echo "  test-frontend-e2e        Alias for frontend-test-e2e"
	@echo "  test-frontend-e2e-headed Alias for frontend-test-e2e-headed"
	@echo "  test-frontend-e2e-ui     Alias for frontend-test-e2e-ui"
	@echo "  test-frontend-e2e-real-api Alias for frontend-test-e2e-real-api"
	@echo "  test-frontend-e2e-real-api-headed Alias for frontend-test-e2e-real-api-headed"
	@echo "  test-frontend-e2e-real-api-ui Alias for frontend-test-e2e-real-api-ui"
	@echo ""
	@echo "Documentation:"
	@echo "  docs                     Generate documentation"
	@echo ""
	@echo "Ontology:"
	@echo "  ontology-refresh         Extract tags from database and update analysis"
	@echo "  ontology-generate        Generate hierarchy TSV from tag analysis"
	@echo "  ontology-validate        Validate hierarchy TSV consistency"
	@echo "  ontology-stats           Show ontology statistics and coverage"
	@echo "  ontology-test            Run comprehensive ontology test suite"
	@echo "  ontology-json            Convert TSV hierarchy to JSON format"
	@echo ""
	@echo "Markdown Manager:"
	@echo "  md-collate               Scan and catalog markdown files"
	@echo "  md-export-tsv            Export database to TSV files"
	@echo "  md-test                  Run markdown manager tests"
	@echo "  md-github-sync-down      Sync GitHub issues to local files"
	@echo "  md-github-sync-up        Push local files to GitHub issues"
	@echo "  md-github-sync           Bidirectional GitHub sync"


# Database initialization
init-all: init-dev init-demo init-test

init-dev:
	@echo "Initializing database..."
	python -m genonaut.db.init

init-demo:
	@echo "Initializing demo database..."
	GENONAUT_DB_ENVIRONMENT=demo python -c "from genonaut.db.init import initialize_database; initialize_database(drop_existing=True)"

init-test:
	@echo "Initializing test database..."
	@TEST_URL=$${DATABASE_URL_TEST:-$${DATABASE_URL}}; \
	GENONAUT_DB_ENVIRONMENT=test TEST=1 DATABASE_URL=$$TEST_URL DATABASE_URL_TEST=$$TEST_URL python -m genonaut.db.init

reset-db-1-data--demo:
	@echo "Resetting demo database..."
	@python -m genonaut.db.utils.reset --environment demo $(ARGS)

reset-db-1-data--test:
	@echo "Resetting test database..."
	@python -m genonaut.db.utils.reset --environment test

reset-db-2-schema--demo:
	@echo "Resetting demo database schema..."
	@python -m genonaut.db.utils.reset --environment demo --drop-tables $(ARGS)

reset-db-2-schema--test:
	@echo "Resetting test database schema..."
	@python -m genonaut.db.utils.reset --environment test --drop-tables

reset-db-3-schema-and-history--demo:
	@echo "Resetting demo database with migration history cleanup..."
	@python -m genonaut.db.utils.reset --environment demo --with-history $(ARGS)

reset-db-3-schema-and-history--test:
	@echo "Resetting test database with migration history cleanup..."
	@python -m genonaut.db.utils.reset --environment test --with-history

re-seed-demo:
	@echo "Re-seeding demo database..."
	@python -c "import sys; sys.path.append('.'); from genonaut.db.init import reseed_demo; reseed_demo(force=False)"

re-seed-demo-force:
	@echo "Re-seeding demo database (forced)..."
	@python -c "import sys; sys.path.append('.'); from genonaut.db.init import reseed_demo; reseed_demo(force=True)"

# Synthetic data generation
# Helper function for DRY abstraction (accepts database URL as parameter)
define seed-from-gen-helper
	@python -m genonaut.db.demo.seed_data_gen generate --database-url "$(1)" \
	--use-unmodified-wal-buffers \
	--batch-size 5000 \
	--target-rows-users 500 \
	--target-rows-content-items 5000 \
	--target-rows-content-items-auto 100000
endef

seed-from-gen-demo:
	@echo "Generating synthetic data for demo database..."
	$(call seed-from-gen-helper,${DATABASE_URL_DEMO})

seed-from-gen-test:
	@echo "Generating synthetic data for test database..."
	$(call seed-from-gen-helper,${DATABASE_URL_TEST})

export-demo-data:
	@echo "Exporting demo database data to test TSV files..."
	python -m test.db.utils export-demo-data

# PostgreSQL wal_buffers management
# todo: Add support for other databases (dev, test) via parameters like db-wal-buffers-reset-dev, db-wal-buffers-set-test, etc.
db-wal-buffers-reset:
	@echo "Resetting PostgreSQL wal_buffers to 4MB (demo database)..."
	@set -a && source env/.env && python -m genonaut.db.utils.wal_buffers --database-url "$$DATABASE_URL_DEMO" reset
	@echo "⚠️  Please restart PostgreSQL for changes to take effect!"

db-wal-buffers-set:
	@echo "Setting PostgreSQL wal_buffers to $(VALUE) (demo database)..."
	@if [ -z "$(VALUE)" ]; then \
		echo "Error: VALUE parameter is required. Usage: make db-wal-buffers-set VALUE=64MB"; \
		exit 1; \
	fi
	@set -a && source env/.env && python -m genonaut.db.utils.wal_buffers --database-url "$$DATABASE_URL_DEMO" set --value "$(VALUE)"
	@echo "⚠️  Please restart PostgreSQL for changes to take effect!"

# Tests
test:
	@echo "Running quick tests (excluding long-running tests)..."
	pytest test/ -v -m "not longrunning"

test-quick: test

test-long-running:
	@echo "Running long-running tests (performance, stress, large datasets)..."
	@echo "⚠️  Warning: These tests may take 5-15 minutes to complete"
	pytest test/ -v -m "longrunning"

test-verbose:
	@echo "Running quick tests with verbose output..."
	pytest test/ -v -s -m "not longrunning"

test-specific:
	@echo "Running specific test: $(TEST)"
	pytest $(TEST) -v

# Three-tier testing approach
test-unit:
	@echo "Running unit tests (no external dependencies required)..."
	@echo "Testing: Pydantic models, utilities, exceptions, configuration"
	pytest test/api/unit/ -v

test-db:
	@echo "Running database tests (database server required)..."
	@echo "Testing: repositories, services, database operations"
	@echo "Make sure your test database is initialized (make init-test) and configured in .env"
	pytest test/api/db/ test/db/ -v

test-db-unit:
	@echo "Running database unit tests (no external dependencies required)..."
	@echo "Testing: Database models, utilities, initialization logic"
	pytest test/db/unit/ -v

test-db-integration:
	@echo "Running database integration tests (database server required)..."
	@echo "Testing: Database operations, seeding, end-to-end workflows"
	@echo "Make sure your test database is initialized (make init-test) and configured in .env"
	pytest test/db/integration/ -v

test-api:
	@echo "Running API integration tests (web server required)..."
	@echo "Testing: HTTP endpoints, complete workflows, error handling"
	@echo "Prerequisites: API server should be running on http://0.0.0.0:8001. (it's probably running; this is just a reminder)"
	@echo "Start with: make api-test"
	API_BASE_URL=http://0.0.0.0:8001 pytest test/api/integration/ -v

test-all: test-quick test-long-running
	t@echo "✅ All test suites completed successfully!"
	@echo "Summary:"
	@echo "  ✓ Quick tests (fast feedback)"
	@echo "  ✓ Long-running tests (performance & stress)"
	@echo "  ✓ Database tests (DB required)"
	@echo "  ✓ API integration tests (web server required)"

# Database management
clear-excess-test-schemas:
	@echo "Clearing excess test schemas..."
	python test/cli.py --clear-excess-test-schemas

clear-excess-test-schemas-keep-3:
	@echo "Clearing excess test schemas (keeping 3 latest)..."
	python test/cli.py --clear-excess-test-schemas --keep-latest 3

# Ontology management
ontology-refresh:
	@echo "Extracting tags from database and updating analysis..."
	@set -a && source env/.env && PYTHONPATH=. python genonaut/ontologies/tags/scripts/query_tags.py
	@echo "✅ Tag analysis updated"

ontology-generate:
	@echo "Generating hierarchy TSV from tag analysis..."
	@cd genonaut/ontologies/tags/scripts && python curate_final_hierarchy.py
	@echo "✅ Hierarchy generated"

ontology-validate:
	@echo "Validating hierarchy TSV consistency..."
	@cd genonaut/ontologies/tags/scripts && PYTHONPATH=../../../.. python -c "import sys; sys.path.append('../../../..'); from generate_hierarchy import validate_hierarchy; from pathlib import Path; errors = validate_hierarchy(Path('../data/hierarchy.tsv')); print('✅ Validation passed!' if not errors else '❌ Validation issues found:'); [print(f'  {e}') for e in errors]; sys.exit(0 if not errors else 1)"

ontology-stats:
	@echo "Generating ontology statistics..."
	@cd genonaut/ontologies/tags && echo "=== TAG ONTOLOGY STATISTICS ===" && \
	echo "Data files:" && ls -la data/ && echo "" && \
	echo "Hierarchy relationships:" && tail -n +2 data/hierarchy.tsv | wc -l | tr -d ' ' | awk '{print $$1 " parent-child relationships"}' && \
	echo "Unique tags in hierarchy:" && tail -n +2 data/hierarchy.tsv | cut -f2 | sort -u | wc -l | tr -d ' ' | awk '{print $$1 " unique child tags"}' && \
	echo "Root categories:" && tail -n +2 data/hierarchy.tsv | cut -f1 | sort -u | wc -l | tr -d ' ' | awk '{print $$1 " unique parent categories"}' && \
	echo "" && echo "Recent tag analysis:" && head -20 data/tags_analysis.txt

ontology-test:
	@echo "Running comprehensive ontology test suite..."
	@echo "Testing core functionality, data quality, integration, performance, and future compatibility..."
	@PYTHONPATH=. python -m pytest test/ontologies/tags/ -v --tb=short
	@echo "✅ Ontology tests completed"

ontology-json:
	@echo "Converting TSV hierarchy to JSON format..."
	@PYTHONPATH=. python genonaut/ontologies/tags/scripts/generate_json.py
	@echo "✅ JSON conversion completed"

# Development setup
install:
	@echo "Installing project dependencies..."
	pip install -r requirements.txt

install-dev: install
	@echo "Installing development dependencies..."
	pip install pytest pytest-cov black flake8 mypy

# Code quality
lint:
	@echo "Running code linting..."
	@echo "Checking with flake8..."
	flake8 genonaut/ --max-line-length=100 --extend-ignore=E203,W503 || true
	@echo "Checking with mypy..."
	mypy genonaut/ --ignore-missing-imports || true

format:
	@echo "Formatting code with black..."
	black genonaut/ test/ --line-length=100

# Cleanup
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.sqlite" -delete
	find . -type f -name "*.db" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Database initialization
init-db:
	@echo "Initializing database..."
	python -m genonaut.db.init

init-db-drop:
	@echo "Initializing database (dropping existing tables)..."
	python -c "from genonaut.db.init import initialize_database; initialize_database(drop_existing=True)"

# DB migration
# migrate-*: Create auto-generted revision based on SQLAlchemy model changes. Pass with a message, like: `make migrate-all m="my changes`
# !warning: if migrating multiple databases and their db schema is exactly the same, autogeneration should be fine, and
# can then be applied to all 3 databases via 'alembic upgrade head'. However, if they differ, and you create the
# migration using 1 database url, and then try to apply it, it will only work on the database(s) with matching schema.
migrate-all: migrate-prep migrate-demo migrate-dev migrate-test

# todo: when demo is no longer the main DB, the canonical DB URL should change here to just: DATABASE_URL
# migrate-prep: Alt versions:
# dev:
# @ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL} DATABASE_URL=${DATABASE_URL} alembic revision --autogenerate -m "$(m)"
# test:
# @TEST_URL=$${DATABASE_URL_TEST:-$${DATABASE_URL}}; \
# GENONAUT_DB_ENVIRONMENT=test DATABASE_URL=$$TEST_URL DATABASE_URL_TEST=$$TEST_URL ALEMBIC_SQLALCHEMY_URL=$$TEST_URL alembic revision --autogenerate -m "$(m)"
migrate-prep:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL_DEMO} DATABASE_URL=${DATABASE_URL_DEMO} alembic revision --autogenerate -m "$(m)"


# Function to run alembic upgrade with extensions check
# Usage: $(call run-migration,DATABASE_URL,[ENVIRONMENT])
define run-migration
	@python -m genonaut.db.schema_extensions install $(1)
	@echo "📦 Running database migration..."
	@$(if $(2),GENONAUT_DB_ENVIRONMENT=$(2) DATABASE_URL=$(1) DATABASE_URL_TEST=$(1),DATABASE_URL=$(1)) ALEMBIC_SQLALCHEMY_URL=$(1) alembic upgrade head
endef

migrate-dev:
	$(call run-migration,${DATABASE_URL})

migrate-demo:
	$(call run-migration,${DATABASE_URL_DEMO})

migrate-test:
	$(call run-migration,${DATABASE_URL_TEST:-${DATABASE_URL}},test)

migrate-down-dev:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL} DATABASE_URL=${DATABASE_URL} alembic downgrade -1

migrate-heads-dev:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL} DATABASE_URL=${DATABASE_URL} alembic heads

migrate-down-demo:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL_DEMO} DATABASE_URL=${DATABASE_URL_DEMO} alembic downgrade -1

migrate-heads-demo:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL_DEMO} DATABASE_URL=${DATABASE_URL_DEMO} alembic heads

# Coverage
test-coverage:
	@echo "Running tests with coverage..."
	python -m pytest test/ --cov=genonaut --cov-report=html --cov-report=term

# Documentation (if needed in the future)
docs:
	@echo "Generating documentation..."
	@echo "Documentation generation not yet implemented"

# Utility targets
check-env:
	@echo "Checking environment setup..."
	@python -c "import sys; print(f'Python version: {sys.version}')"
	@python -c "import pkg_resources; print('Installed packages:'); [print(f'  {d.project_name}: {d.version}') for d in pkg_resources.working_set]"

# Backup targets
backup-dev:
	@echo "Backing up development database..."
	@python -m genonaut.db.utils.backup ${DATABASE_URL}

backup-demo:
	@echo "Backing up demo database..."
	@python -m genonaut.db.utils.backup ${DATABASE_URL_DEMO}

backup-test:
	@echo "Backing up test database..."
	@TEST_URL=$${DATABASE_URL_TEST:-$${DATABASE_URL}}; \
	python -m genonaut.db.utils.backup $$TEST_URL

backup: backup-dev backup-demo backup-test
	@echo "✅ All database backups completed!"

# FastAPI server
api-dev:
	@echo "Starting FastAPI server for development database..."
	APP_ENV=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload

api-demo:
	@echo "Starting FastAPI server for demo database..."
	APP_ENV=demo uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload

api-test:
	@echo "Starting FastAPI server for test database..."
	APP_ENV=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload

# FastAPI server variants for performance testing
api-dev-profile:
	@echo "Starting FastAPI server for development with profiling (single worker, no reload)..."
	APP_ENV=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --workers 1

api-dev-load-test:
	@echo "Starting FastAPI server for load testing (4 workers)..."
	APP_ENV=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --workers 4

api-production-sim:
	@echo "Starting FastAPI server simulating production (8 workers)..."
	APP_ENV=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --workers 8

api-demo-load-test:
	@echo "Starting FastAPI server for demo load testing (4 workers)..."
	APP_ENV=demo uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --workers 4

api-test-load-test:
	@echo "Starting FastAPI server for test load testing (4 workers)..."
	APP_ENV=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --workers 4

# Celery worker commands
celery-dev:
	@echo "Starting Celery worker for development environment..."
	APP_ENV=dev celery -A genonaut.worker.queue_app:celery_app worker --loglevel=info --queues=default,generation

celery-demo:
	@echo "Starting Celery worker for demo environment..."
	APP_ENV=demo celery -A genonaut.worker.queue_app:celery_app worker --loglevel=info --queues=default,generation

celery-test:
	@echo "Starting Celery worker for test environment..."
	APP_ENV=test celery -A genonaut.worker.queue_app:celery_app worker --loglevel=info --queues=default,generation

# Flower monitoring dashboard
flower-dev:
	@echo "Starting Flower dashboard for development environment..."
	APP_ENV=dev celery -A genonaut.worker.queue_app:celery_app flower --port=5555

flower-demo:
	@echo "Starting Flower dashboard for demo environment..."
	APP_ENV=demo celery -A genonaut.worker.queue_app:celery_app flower --port=5555

flower-test:
	@echo "Starting Flower dashboard for test environment..."
	APP_ENV=test celery -A genonaut.worker.queue_app:celery_app flower --port=5555

# Redis management commands
redis-flush-dev:
	@echo "Flushing Redis DB 4 (dev)..."
	@redis-cli -n 4 FLUSHDB
	@echo "✅ Dev Redis DB flushed"

redis-flush-demo:
	@echo "Flushing Redis DB 2 (demo)..."
	@redis-cli -n 2 FLUSHDB
	@echo "✅ Demo Redis DB flushed"

redis-flush-test:
	@echo "Flushing Redis DB 3 (test)..."
	@redis-cli -n 3 FLUSHDB
	@echo "✅ Test Redis DB flushed"

redis-keys-dev:
	@echo "Listing keys in Redis DB 4 (dev)..."
	@redis-cli -n 4 KEYS '*'

redis-keys-demo:
	@echo "Listing keys in Redis DB 2 (demo)..."
	@redis-cli -n 2 KEYS '*'

redis-keys-test:
	@echo "Listing keys in Redis DB 3 (test)..."
	@redis-cli -n 3 KEYS '*'

redis-info-dev:
	@echo "Redis info for dev (DB 4)..."
	@redis-cli -n 4 DBSIZE

redis-info-demo:
	@echo "Redis info for demo (DB 2)..."
	@redis-cli -n 2 DBSIZE

redis-info-test:
	@echo "Redis info for test (DB 3)..."
	@redis-cli -n 3 DBSIZE

# Frontend helpers
frontend-install:
	@echo "Installing frontend dependencies..."
	npm --prefix frontend install

frontend-dev:
	@echo "Starting frontend dev server..."
	npm --prefix frontend run dev

frontend-build:
	@echo "Building frontend..."
	npm --prefix frontend run build

frontend-preview:
	@echo "Previewing built frontend..."
	npm --prefix frontend run preview

frontend-test-unit:
	@echo "Running frontend unit tests..."
	npm --prefix frontend run test-unit

frontend-test:
	@echo "Running all frontend tests (unit + e2e)..."
	npm --prefix frontend run test

frontend-test-watch:
	@echo "Running frontend tests in watch mode..."
	npm --prefix frontend run test:watch

frontend-test-coverage:
	@echo "Running frontend tests with coverage..."
	npm --prefix frontend run test:coverage

frontend-test-e2e:
	@echo "Running frontend Playwright tests..."
	npm --prefix frontend run test:e2e

frontend-test-e2e-headed:
	@echo "Running frontend Playwright tests in headed mode..."
	npm --prefix frontend run test:e2e:headed

frontend-test-e2e-ui:
	@echo "Running Playwright UI mode..."
	npm --prefix frontend run test:e2e:ui

frontend-test-e2e-real-api:
	@echo "Running Playwright tests with real API server..."
	npm --prefix frontend run test:e2e:real-api

frontend-test-e2e-real-api-headed:
	@echo "Running real API Playwright tests in headed mode..."
	npm --prefix frontend run test:e2e:real-api:headed

frontend-test-e2e-real-api-ui:
	@echo "Running real API Playwright tests in UI mode..."
	npm --prefix frontend run test:e2e:real-api:ui

frontend-lint:
	@echo "Linting frontend code..."
	npm --prefix frontend run lint

frontend-type-check:
	@echo "Type-checking frontend code..."
	npm --prefix frontend run type-check

frontend-format:
	@echo "Checking frontend formatting..."
	npm --prefix frontend run format

frontend-format-write:
	@echo "Formatting frontend code..."
	npm --prefix frontend run format:write

# Frontend test aliases (test-frontend* variants)
test-frontend: frontend-test
test-frontend-unit: frontend-test-unit
test-frontend-watch: frontend-test-watch
test-frontend-coverage: frontend-test-coverage
test-frontend-e2e: frontend-test-e2e
test-frontend-e2e-headed: frontend-test-e2e-headed
test-frontend-e2e-ui: frontend-test-e2e-ui
test-frontend-e2e-real-api: frontend-test-e2e-real-api
test-frontend-e2e-real-api-headed: frontend-test-e2e-real-api-headed
test-frontend-e2e-real-api-ui: frontend-test-e2e-real-api-ui

# todo: find a better place in file
# Integration checks
## ComfyUI
COMFY_EXAMPLE_FILE=test/integrations/comfy_ui/input/1.json
COMFY_HOST=127.0.0.1
COMFY_PORT=8000  # Manual/portable (python main.py): defaults to 8188 unless you set --port. Desktop app (macOS build): commonly ships with 8000 as the baked-in default.

check-comfyui-create-img:
	curl -X POST http://localhost:8000/prompt \
	     -H "Content-Type: application/json" \
	     -d @$${COMFY_EXAMPLE_FILE}

# Lib: Markdown Manager
md-collate:
	cd libs/md_manager && source env/bin/activate && python -m md_manager.cli --config-path ../../notes/md-manager.json collate

# todo: ideally would dynamically open every TSV in that dir
md-export-tsv:
	rm -rf notes/_archive/md-manager/export/
	mkdir -p notes/_archive/md-manager/export/
	cd libs/md_manager && source env/bin/activate && python -m md_manager.cli --config-path ../../notes/md-manager.json export --export-path ../../notes/_archive/md-manager/export/
	open notes/_archive/md-manager/export/files.tsv

md-test:
	cd libs/md_manager && source env/bin/activate && python -m pytest test/ -v

# GitHub Sync Commands
md-github-sync-down:
	@echo "Syncing GitHub issues to local files..."
	@if [ ! -f "notes/md-manager.json" ]; then \
		echo "Error: Configuration file notes/md-manager.json not found"; \
		echo "Please create the configuration file or set GITHUB_TOKEN environment variable"; \
		exit 1; \
	fi
	@if [ -z "$$GITHUB_TOKEN" ] && [ -z "$$MD_MANAGER_TOKEN" ]; then \
		echo "Warning: No GitHub token found in environment variables"; \
		echo "Please set GITHUB_TOKEN or MD_MANAGER_TOKEN, or configure in md-manager.json"; \
	fi
	cd libs/md_manager && source env/bin/activate && python -m md_manager.cli --config-path ../../notes/md-manager.json sync || (echo "Error: GitHub → Local sync failed"; exit 1)
	@echo "✅ GitHub → Local sync completed successfully"

md-github-sync-up:
	@echo "Pushing local files to GitHub issues..."
	@if [ ! -f "notes/md-manager.json" ]; then \
		echo "Error: Configuration file notes/md-manager.json not found"; \
		exit 1; \
	fi
	@if [ -z "$$GITHUB_TOKEN" ] && [ -z "$$MD_MANAGER_TOKEN" ]; then \
		echo "Warning: No GitHub token found in environment variables"; \
		echo "Please set GITHUB_TOKEN or MD_MANAGER_TOKEN, or configure in md-manager.json"; \
	fi
	cd libs/md_manager && source env/bin/activate && python -m md_manager.cli --config-path ../../notes/md-manager.json push || (echo "Error: Local → GitHub sync failed"; exit 1)
	@echo "✅ Local → GitHub sync completed successfully"

md-github-sync:
	@echo "Running bidirectional GitHub sync..."
	@if [ ! -f "notes/md-manager.json" ]; then \
		echo "Error: Configuration file notes/md-manager.json not found"; \
		exit 1; \
	fi
	@if [ -z "$$GITHUB_TOKEN" ] && [ -z "$$MD_MANAGER_TOKEN" ]; then \
		echo "Warning: No GitHub token found in environment variables"; \
		echo "Please set GITHUB_TOKEN or MD_MANAGER_TOKEN, or configure in md-manager.json"; \
	fi
	cd libs/md_manager && source env/bin/activate && python -m md_manager.cli --config-path ../../notes/md-manager.json sync-bidirectional || (echo "Error: Bidirectional sync failed"; exit 1)
	@echo "✅ Bidirectional sync completed successfully"

# Redis
REDIS_STORAGE_PATH=env/redis/storage/
REDIS_CONFIG_PATH=redis.conf

$(REDIS_STORAGE_PATH):
	mkdir -p $@

redis-start: | $(REDIS_STORAGE_PATH)
	redis-server $(REDIS_CONFIG_PATH)

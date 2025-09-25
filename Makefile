# Common development tasks and utilities
.PHONY: help init-all init-dev init-demo init-test reset-db-1-data--demo reset-db-1-data--test reset-db-2-schema--demo \
reset-db-2-schema--test reset-db-3-schema-and-history--demo reset-db-3-schema-and-history--test re-seed-demo \
re-seed-demo-force seed-from-gen-demo seed-from-gen-test test test-quick test-verbose test-specific test-unit test-db \
test-db-unit test-db-integration test-api test-all clear-excess-test-schemas install install-dev \
lint format clean migrate-all migrate-prep migrate-dev migrate-demo migrate-test backup backup-dev backup-demo \
backup-test api-dev api-demo api-test frontend-install frontend-dev frontend-build frontend-preview frontend-test \
frontend-test-unit frontend-test-watch frontend-test-coverage frontend-test-e2e frontend-test-e2e-headed \
frontend-test-e2e-ui frontend-lint frontend-type-check frontend-format frontend-format-write \
test-frontend test-frontend-unit test-frontend-watch test-frontend-coverage test-frontend-e2e test-frontend-e2e-headed \
test-frontend-e2e-ui db-wal-buffers-reset db-wal-buffers-set

# Load environment variables
ifneq (,$(wildcard ./env/.env))
include ./env/.env
export  # export included vars to child processes
endif

# help: Default target
help:
	@echo "Available targets:"
	@echo "  help                     Show this help message"
	@echo "  init                     Initialize database with schema"
	@echo "  init-demo                Initialize demo database with schema"
	@echo "  init-test                Initialize test database with schema"
	@echo "  reset-db-1-data--demo            Truncate and re-initialize the 	demo database"
	@echo "  reset-db-1-data--test            Truncate and re-initialize the test database"
	@echo "  reset-db-2-schema--demo          Drop and re-initialize the demo database schema"
	@echo "  reset-db-2-schema--test          Drop and re-initialize the test database schema"
	@echo "  reset-db-3-schema-and-history--demo Reset demo database with migration history cleanup"
	@echo "  reset-db-3-schema-and-history--test Reset test database with migration history cleanup"
	@echo "  re-seed-demo             Re-seed demo database (prompts for confirmation)"
	@echo "  re-seed-demo-force       Re-seed demo database (no confirmation prompt)"
	@echo "  seed-from-gen-demo       Generate synthetic data for demo database"
	@echo "  seed-from-gen-test       Generate synthetic data for test database"
	@echo "  test / test-quick        Run quick tests (< 2 minutes)"
	@echo "  test-long-running        Run performance/stress tests (5-15 minutes)"
	@echo "  test-verbose             Run all tests with verbose output"
	@echo "  test-specific TEST=name  Run specific test module or test case"
	@echo "  test-unit                Run unit tests (no external dependencies)"
	@echo "  test-db                  Run database tests (requires database)"
	@echo "  test-db-unit             Run database unit tests (no external dependencies)"
	@echo "  test-db-integration      Run database integration tests (requires database)"
	@echo "  test-api                 Run API integration tests (requires web server)"
	@echo "  test-all                 Run all tests (quick + long-running)"
	@echo "  clear-excess-test-schemas Clear excess test database schemas"
	@echo "  install                  Install project dependencies"
	@echo "  install-dev              Install development dependencies"
	@echo "  lint                     Run code linting"
	@echo "  format                   Format code"
	@echo "  clean                    Clean temporary files"
	@echo "  migrate-dev              Upgrade main database schema"
	@echo "  migrate-demo             Upgrade demo database schema"
	@echo "  migrate-test             Generate migration revision for test database"
	@echo "  backup                   Backup all databases (dev, demo, test)"
	@echo "  backup-dev               Backup development database"
	@echo "  backup-demo              Backup demo database"
	@echo "  backup-test              Backup test database"
	@echo "  api-dev                  Start FastAPI server for development database"
	@echo "  api-demo                 Start FastAPI server for demo database"
	@echo "  api-test                 Start FastAPI server for test database"
	@echo ""
	@echo "PostgreSQL wal_buffers management:"
	@echo "  db-wal-buffers-reset     Reset wal_buffers to 4MB (requires PostgreSQL restart)"
	@echo "  db-wal-buffers-set VALUE Set wal_buffers to VALUE (e.g., 64MB, requires restart)"
	@echo ""
	@echo "Frontend commands:"
	@echo "  frontend-install         Install frontend dependencies"
	@echo "  frontend-dev             Start frontend dev server"
	@echo "  frontend-build           Build frontend for production"
	@echo "  frontend-preview         Preview built frontend"
	@echo "  frontend-test            Run all frontend tests (unit + e2e)"
	@echo "  frontend-test-unit       Run frontend unit tests only"
	@echo "  frontend-test-watch      Run frontend tests in watch mode"
	@echo "  frontend-test-coverage   Run frontend tests with coverage"
	@echo "  frontend-test-e2e        Run frontend Playwright e2e tests"
	@echo "  frontend-test-e2e-headed Run Playwright tests in headed mode"
	@echo "  frontend-test-e2e-ui     Run Playwright UI mode"
	@echo "  frontend-lint            Lint frontend code"
	@echo "  frontend-type-check      Type-check frontend code"
	@echo "  frontend-format          Check frontend formatting"
	@echo "  frontend-format-write    Format frontend code"
	@echo ""
	@echo "Frontend test aliases (test-frontend* variants):"
	@echo "  test-frontend            Alias for frontend-test (all tests)"
	@echo "  test-frontend-unit       Alias for frontend-test-unit"
	@echo "  test-frontend-watch      Alias for frontend-test-watch"
	@echo "  test-frontend-coverage   Alias for frontend-test-coverage"
	@echo "  test-frontend-e2e        Alias for frontend-test-e2e"
	@echo "  test-frontend-e2e-headed Alias for frontend-test-e2e-headed"
	@echo "  test-frontend-e2e-ui     Alias for frontend-test-e2e-ui"

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
	@echo "✅ All test suites completed successfully!"
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


migrate-dev:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL} DATABASE_URL=${DATABASE_URL} alembic upgrade head

migrate-demo:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL_DEMO} DATABASE_URL=${DATABASE_URL_DEMO} alembic upgrade head

migrate-test:
	@TEST_URL=${DATABASE_URL_TEST:-${DATABASE_URL}}; \
	GENONAUT_DB_ENVIRONMENT=test DATABASE_URL=$$TEST_URL DATABASE_URL_TEST=$$TEST_URL ALEMBIC_SQLALCHEMY_URL=$$TEST_URL alembic upgrade head

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
	API_ENVIRONMENT=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload

api-demo:
	@echo "Starting FastAPI server for demo database..."
	API_ENVIRONMENT=demo uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload

api-test:
	@echo "Starting FastAPI server for test database..."
	API_ENVIRONMENT=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload

# FastAPI server variants for performance testing
api-dev-profile:
	@echo "Starting FastAPI server for development with profiling (single worker, no reload)..."
	API_ENVIRONMENT=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --workers 1

api-dev-load-test:
	@echo "Starting FastAPI server for load testing (4 workers)..."
	API_ENVIRONMENT=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --workers 4

api-production-sim:
	@echo "Starting FastAPI server simulating production (8 workers)..."
	API_ENVIRONMENT=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --workers 8

api-demo-load-test:
	@echo "Starting FastAPI server for demo load testing (4 workers)..."
	API_ENVIRONMENT=demo uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --workers 4

api-test-load-test:
	@echo "Starting FastAPI server for test load testing (4 workers)..."
	API_ENVIRONMENT=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --workers 4

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

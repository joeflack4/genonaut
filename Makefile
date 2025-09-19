# Makefile for Genonaut project
# Provides common development tasks and utilities

.PHONY: help init-all init-dev init-demo init-test re-seed-demo re-seed-demo-force test test-verbose test-specific test-unit test-db test-api test-all clear-excess-test-schemas install install-dev \
lint format clean migrate-all migrate-dev migrate-demo migrate-test migrate-step2-all migrate-step2-dev migrate-step2-demo migrate-step2-test api-dev api-demo api-test

ifneq (,$(wildcard ./env/.env))
include ./env/.env
export  # export included vars to child processes
endif

# Default target
help:
	@echo "Available targets:"
	@echo "  help                     Show this help message"
	@echo "  init                     Initialize database with schema"
	@echo "  init-demo                Initialize demo database with schema"
	@echo "  init-test                Initialize test database with schema"
	@echo "  re-seed-demo             Re-seed demo database (prompts for confirmation)"
	@echo "  re-seed-demo-force       Re-seed demo database (no confirmation prompt)"
	@echo "  test                     Run all tests (legacy command)"
	@echo "  test-verbose             Run all tests with verbose output"
	@echo "  test-specific TEST=name  Run specific test module or test case"
	@echo "  test-unit                Run unit tests (no external dependencies)"
	@echo "  test-db                  Run database tests (requires database)"
	@echo "  test-api                 Run API integration tests (requires web server)"
	@echo "  test-all                 Run all test suites (unit + db + api)"
	@echo "  clear-excess-test-schemas Clear excess test database schemas"
	@echo "  install                  Install project dependencies"
	@echo "  install-dev              Install development dependencies"
	@echo "  lint                     Run code linting"
	@echo "  format                   Format code"
	@echo "  clean                    Clean temporary files"
	@echo "  migrate-dev              Upgrade main database schema"
	@echo "  migrate-demo             Upgrade demo database schema"
	@echo "  migrate-test             Generate migration revision for test database"
	@echo "  api-dev                  Start FastAPI server for development database"
	@echo "  api-demo                 Start FastAPI server for demo database"
	@echo "  api-test                 Start FastAPI server for test database"

# Database initialization
init-all: init-dev init-demo init-test

init-dev:
	@echo "Initializing database..."
	DEMO=0 python -m genonaut.db.init

init-demo:
	@echo "Initializing demo database..."
	DEMO=1 python -m genonaut.db.init

init-test:
	@echo "Initializing test database..."
	@TEST_URL=$${DATABASE_URL_TEST:-$${DATABASE_URL}}; \
	GENONAUT_DB_ENVIRONMENT=test TEST=1 DATABASE_URL=$$TEST_URL DATABASE_URL_TEST=$$TEST_URL python -m genonaut.db.init

re-seed-demo:
	@echo "Re-seeding demo database..."
	@python -c "import sys; sys.path.append('.'); from genonaut.db.init import reseed_demo; reseed_demo(force=False)"

re-seed-demo-force:
	@echo "Re-seeding demo database (forced)..."
	@python -c "import sys; sys.path.append('.'); from genonaut.db.init import reseed_demo; reseed_demo(force=True)"

# Tests
test:
	@echo "Running all tests (legacy)..."
	pytest test/ -v

test-verbose:
	@echo "Running all tests with verbose output..."
	pytest test/ -v -s

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
	pytest test/api/db/ test/test_database*.py test/test_schema.py -v

test-api:
	@echo "Running API integration tests (web server required)..."
	@echo "Testing: HTTP endpoints, complete workflows, error handling"
	@echo "Prerequisites: API server should be running on http://0.0.0.0:8000. (it's probably running; this is just a reminder)"
	@echo "Start with: make api-test"
	API_BASE_URL=http://0.0.0.0:8000 pytest test/api/integration/ -v

test-all: test-unit test-db test-api
	@echo "✅ All test suites completed successfully!"
	@echo "Summary:"
	@echo "  ✓ Unit tests (no dependencies)"
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
migrate-all: migrate-dev migrate-demo migrate-test

migrate-dev:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL} DATABASE_URL=${DATABASE_URL} alembic revision --autogenerate -m "$(m)"

migrate-demo:
	@DEMO=1 ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL_DEMO} DATABASE_URL=${DATABASE_URL_DEMO} alembic revision --autogenerate -m "$(m)"

migrate-test:
	@TEST_URL=$${DATABASE_URL_TEST:-$${DATABASE_URL}}; \
	GENONAUT_DB_ENVIRONMENT=test DATABASE_URL=$$TEST_URL DATABASE_URL_TEST=$$TEST_URL ALEMBIC_SQLALCHEMY_URL=$$TEST_URL alembic revision --autogenerate -m "$(m)"

migrate-step2-all: migrate-step2-dev migrate-step2-demo migrate-step2-test

migrate-step2-dev:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL} DATABASE_URL=${DATABASE_URL} alembic upgrade head

migrate-step2-demo:
	@DEMO=1 ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL_DEMO} DATABASE_URL=${DATABASE_URL_DEMO} alembic upgrade head

migrate-step2-test:
	@TEST_URL=$${DATABASE_URL_TEST:-$${DATABASE_URL}}; \
	GENONAUT_DB_ENVIRONMENT=test DATABASE_URL=$$TEST_URL DATABASE_URL_TEST=$$TEST_URL ALEMBIC_SQLALCHEMY_URL=$$TEST_URL alembic upgrade head

migrate-down-dev:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL} DATABASE_URL=${DATABASE_URL} alembic downgrade -1

migrate-heads-dev:
	@ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL} DATABASE_URL=${DATABASE_URL} alembic heads

migrate-down-demo:
	@DEMO=1 ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL_DEMO} DATABASE_URL=${DATABASE_URL_DEMO} alembic downgrade -1

migrate-heads-demo:
	@DEMO=1 ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL_DEMO} DATABASE_URL=${DATABASE_URL_DEMO} alembic heads

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

show-db-url:
	@echo "Current database configuration:"
	@python -c "import os; from genonaut.db.utils import get_database_url; print(f'Database URL: {get_database_url()}')" 2>/dev/null || echo "Database configuration not available (missing environment variables)"

# FastAPI server
api-dev:
	@echo "Starting FastAPI server for development database..."
	API_ENVIRONMENT=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8000 --reload

api-demo:
	@echo "Starting FastAPI server for demo database..."
	API_ENVIRONMENT=demo uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8000 --reload

api-test:
	@echo "Starting FastAPI server for test database..."
	API_ENVIRONMENT=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8000 --reload

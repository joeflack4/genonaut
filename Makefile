# Makefile for Genonaut project
# Provides common development tasks and utilities

.PHONY: help init test test-verbose test-specific clear-excess-test-schemas install install-dev lint format clean

# Default target
help:
	@echo "Available targets:"
	@echo "  help                     Show this help message"
	@echo "  init                     Initialize database with schema"
	@echo "  test                     Run all tests"
	@echo "  test-verbose             Run all tests with verbose output"
	@echo "  test-specific TEST=name  Run specific test module or test case"
	@echo "  clear-excess-test-schemas Clear excess test database schemas"
	@echo "  install                  Install project dependencies"
	@echo "  install-dev              Install development dependencies"
	@echo "  lint                     Run code linting"
	@echo "  format                   Format code"
	@echo "  clean                    Clean temporary files"

# Database initialization
init:
	@echo "Initializing database..."
	python -m genonaut.db.init

# Tests
test:
	@echo "Running all tests..."
	pytest test/ -v

test-verbose:
	@echo "Running all tests with verbose output..."
	pytest test/ -v -s

test-specific:
	@echo "Running specific test: $(TEST)"
	pytest $(TEST) -v

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
migrate-new:
	alembic revision --autogenerate -m "$(m)"

migrate-up:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-heads:
	alembic heads

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

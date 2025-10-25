# Common development tasks and utilities
.PHONY: help init-all init-dev init-demo init-test reset-db-1-data--demo reset-db-1-data--test reset-db-2-schema--demo \
reset-db-2-schema--test reset-db-3-schema-and-history--demo reset-db-3-schema-and-history--test re-seed-demo \
re-seed-demo-force seed-from-gen-demo seed-from-gen-test seed-static-demo seed-static-test export-demo-data test \
test-quick test-verbose test-specific test-unit test-db test-db-unit test-db-integration test-api test-tag-queries \
test-all clear-excess-test-schemas install install-dev \
lint format clean migrate-all migrate-all-auto migrate-prep migrate-dev migrate-demo migrate-test backup backup-dev backup-demo \
backup-test api-dev api-demo api-demo-alt api-test celery-dev celery-demo celery-test flower-dev flower-demo flower-test \
redis-flush-dev redis-flush-demo redis-flush-test redis-keys-dev redis-keys-demo redis-keys-test \
redis-info-dev redis-info-demo redis-info-test redis-start celery-check-running-workers \
frontend-install frontend-dev frontend-dev-debug frontend-dev-debug-alt frontend-build frontend-preview frontend-test \
frontend-test-unit frontend-test-watch frontend-test-coverage frontend-test-e2e frontend-test-e2e-headed \
frontend-test-e2e-ui frontend-test-e2e-debug frontend-test-e2e-debug-headed frontend-test-e2e-skip-missing \
frontend-test-e2e-w frontend-test-e2e-headed-w frontend-test-e2e-debug-w frontend-test-e2e-debug-headed-w \
frontend-test-e2e-real-api frontend-test-e2e-real-api-headed frontend-test-e2e-real-api-ui frontend-test-e2e-real-api-debug frontend-test-e2e-real-api-debug-headed frontend-test-e2e-real-api-skip-missing \
frontend-test-e2e-real-api-w frontend-test-e2e-real-api-headed-w frontend-test-e2e-real-api-debug-w frontend-test-e2e-real-api-debug-headed-w \
frontend-lint frontend-type-check frontend-format frontend-format-write \
test-frontend test-frontend-unit test-frontend-watch test-frontend-coverage test-frontend-e2e test-frontend-e2e-headed \
test-frontend-e2e-ui test-frontend-e2e-debug test-frontend-e2e-debug-headed \
test-frontend-e2e-w test-frontend-e2e-headed-w test-frontend-e2e-debug-w test-frontend-e2e-debug-headed-w \
test-frontend-e2e-performance test-frontend-e2e-performance-headed test-frontend-e2e-performance-ui \
test-frontend-e2e-performance-debug test-frontend-e2e-performance-debug-headed \
test-frontend-e2e-performance-w test-frontend-e2e-performance-headed-w test-frontend-e2e-performance-debug-w test-frontend-e2e-performance-debug-headed-w \
test-frontend-e2e-real-api test-frontend-e2e-real-api-headed test-frontend-e2e-real-api-ui test-frontend-e2e-real-api-debug test-frontend-e2e-real-api-debug-headed \
test-frontend-e2e-real-api-w test-frontend-e2e-real-api-headed-w test-frontend-e2e-real-api-debug-w test-frontend-e2e-real-api-debug-headed-w \
db-wal-buffers-reset db-wal-buffers-set init-db init-db-drop test-long-running test-coverage docs \
check-env api-dev-profile api-dev-load-test api-production-sim api-demo-load-test api-test-load-test \
clear-excess-test-schemas-keep-3 migrate-down-dev migrate-heads-dev migrate-down-demo migrate-heads-demo \
ontology-refresh ontology-generate ontology-validate ontology-stats ontology-test ontology-json \
md-collate md-export-tsv md-test md-github-sync-down md-github-sync-up md-github-sync \
tf-bootstrap-init tf-bootstrap-apply tf-bootstrap-destroy tf-init tf-plan tf-apply tf-destroy tf-fmt tf-validate \
tf-console aws-login tf-login refresh-tag-stats refresh-tag-stats-dev refresh-tag-stats-demo refresh-tag-stats-test

# Load environment variables
ifneq (,$(wildcard ./env/.env.shared))
include ./env/.env.shared
export  # export included vars to child processes
endif

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
	@echo "  seed-static-demo         Load static seed data from CSV files (demo)"
	@echo "  seed-static-test         Load static seed data from CSV files (test)"
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
	@echo "  test-performance         Run performance tests (requires live demo server on port 8001)"
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
	@echo "  api-demo-alt             Start FastAPI server for demo on port 8003"
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
	@echo "  beat-status              Show Celery Beat schedule status (demo)"
	@echo "  beat-status-dev          Show Celery Beat schedule status (dev)"
	@echo "  beat-status-demo         Show Celery Beat schedule status (demo)"
	@echo "  beat-status-test         Show Celery Beat schedule status (test)"
	@echo ""
	@echo "Flower Monitoring:"
	@echo "  flower-dev               Start Flower dashboard for development (port 5555)"
	@echo "  flower-demo              Start Flower dashboard for demo (port 5555)"
	@echo "  flower-test              Start Flower dashboard for test (port 5555)"
	@echo ""
	@echo "Redis Management:"
	@echo "  redis-start          	  Run redis server"
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
	@echo "  frontend-dev-debug       Start frontend dev server with debug logging"
	@echo "  frontend-dev-debug-alt   Start frontend dev server with debug logging (port 8003 API, port 5174 frontend)"
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
	@echo "  frontend-test-e2e        Run frontend Playwright e2e tests (excludes performance tests)"
	@echo "  frontend-test-e2e-headed Run Playwright tests in headed mode"
	@echo "  frontend-test-e2e-ui     Run Playwright UI mode"
	@echo "  frontend-test-e2e-debug  Run Playwright tests with verbose debug logging"
	@echo "  frontend-test-e2e-debug-headed Run Playwright tests with debug + browser UI"
	@echo "  frontend-test-e2e-skip-missing Run Playwright tests (skip when data missing)"
	@echo "  frontend-test-e2e-real-api Run Playwright tests with real API server"
	@echo "  frontend-test-e2e-real-api-headed Run real API tests in headed mode"
	@echo "  frontend-test-e2e-real-api-ui Run real API tests in UI mode"
	@echo "  frontend-test-e2e-real-api-debug Run real API tests with debug logging"
	@echo "  frontend-test-e2e-real-api-debug-headed Run real API tests with debug + browser UI"
	@echo "  frontend-test-e2e-real-api-skip-missing Run real API tests (skip when data missing)"
	@echo ""
	@echo "Frontend Test Aliases (test-frontend*):"
	@echo "  test-frontend            Alias for frontend-test"
	@echo "  test-frontend-unit       Alias for frontend-test-unit"
	@echo "  test-frontend-watch      Alias for frontend-test-watch"
	@echo "  test-frontend-coverage   Alias for frontend-test-coverage"
	@echo "  test-frontend-e2e        Alias for frontend-test-e2e"
	@echo "  test-frontend-e2e-headed Alias for frontend-test-e2e-headed"
	@echo "  test-frontend-e2e-ui     Alias for frontend-test-e2e-ui"
	@echo "  test-frontend-e2e-debug  Alias for frontend-test-e2e-debug"
	@echo "  test-frontend-e2e-debug-headed Alias for frontend-test-e2e-debug-headed"
	@echo "  test-frontend-e2e-real-api Alias for frontend-test-e2e-real-api"
	@echo "  test-frontend-e2e-real-api-headed Alias for frontend-test-e2e-real-api-headed"
	@echo "  test-frontend-e2e-real-api-ui Alias for frontend-test-e2e-real-api-ui"
	@echo "  test-frontend-e2e-real-api-debug Alias for frontend-test-e2e-real-api-debug"
	@echo "  test-frontend-e2e-real-api-debug-headed Alias for frontend-test-e2e-real-api-debug-headed"
	@echo ""
	@echo "Documentation:"
	@echo "  docs                     Generate documentation"
	@echo ""
	@echo "Mock Services:"
	@echo "  comfyui-mock             Start mock ComfyUI server (port 8189)"
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
	@echo ""
	@echo "Infrastructure:"
	@echo "  tf-bootstrap-init        Initialize Terraform bootstrap directory"
	@echo "  tf-bootstrap-apply       Apply Terraform bootstrap configuration"
	@echo "  tf-bootstrap-destroy     Destroy Terraform bootstrap resources"
	@echo "  tf-init             Initialize main Terraform directory"
	@echo "  tf-plan             Create a plan for the main Terraform infrastructure"
	@echo "  tf-apply            Apply main Terraform infrastructure changes"
	@echo "  tf-destroy          Destroy main Terraform infrastructure"
	@echo "  tf-fmt              Format Terraform code in the main directory"
	@echo "  tf-validate         Validate Terraform code in the main directory"
	@echo "  tf-console          Open Terraform console for the main directory"

# ============================================
# Various: todo: move these commands around to their correct sections || make new sections
# ============================================
# Database initialization
init-all: init-dev init-demo init-test

init-dev:
	@echo "Initializing development database..."
	python -m genonaut.cli_main init-db --env-target local-dev

init-demo:
	@echo "Initializing demo database..."
	python -m genonaut.cli_main init-db --env-target local-demo --drop-existing

init-test:
	@echo "Initializing test database..."
	python -m genonaut.cli_main init-db --env-target local-test

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
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('demo'))") && \
	$(call seed-from-gen-helper,$$DB_URL)

seed-from-gen-test:
	@echo "Generating synthetic data for test database..."
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('test'))") && \
	$(call seed-from-gen-helper,$$DB_URL)

# Static data seeding
# Helper function for seeding static data from CSV files
define seed-static-helper
	@python -m genonaut.db.demo.seed_data_gen seed-static --database-url "$(1)"
endef

seed-static-demo:
	@echo "Loading static seed data into demo database..."
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('demo'))") && \
	$(call seed-static-helper,$$DB_URL)

seed-static-test:
	@echo "Loading static seed data into test database..."
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('test'))") && \
	$(call seed-static-helper,$$DB_URL)

export-demo-data:
	@echo "Exporting demo database data to test TSV files..."
	python -m test.db.utils export-demo-data

# PostgreSQL wal_buffers management
# todo: Add support for other databases (dev, test) via parameters like db-wal-buffers-reset-dev, db-wal-buffers-set-test, etc.
db-wal-buffers-reset:
	@echo "Resetting PostgreSQL wal_buffers to 4MB (demo database)..."
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('demo'))") && \
	python -m genonaut.db.utils.wal_buffers --database-url "$$DB_URL" reset
	@echo "⚠️  Please restart PostgreSQL for changes to take effect!"

db-wal-buffers-set:
	@echo "Setting PostgreSQL wal_buffers to $(VALUE) (demo database)..."
	@if [ -z "$(VALUE)" ]; then \
		echo "Error: VALUE parameter is required. Usage: make db-wal-buffers-set VALUE=64MB"; \
		exit 1; \
	fi
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('demo'))") && \
	python -m genonaut.db.utils.wal_buffers --database-url "$$DB_URL" set --value "$(VALUE)"
	@echo "⚠️  Please restart PostgreSQL for changes to take effect!"

# Tests
# - "not manual": Manual tests are meant to be run in very specific circumstances, e.g. TestWalBuffersPostRestartVerification: verify wal_buffers after PostgreSQL restart | as of 2025/10/14 there are 100's of tests and only this 1 manual test
# --durations=0 --durations-min=0.5  - This shows any test taking longer than 500ms
test:
	@echo "Running quick tests (excluding long-running, manual, and performance tests)..."
	pytest test/ -v -m "not manual and not longrunning and not performance" --durations=0 --durations-min=0.5

test-quick: test

#test-verbose:
#	@echo "Running quick tests with verbose output..."
#	pytest test/ -v -s -m "not longrunning and not manual and not performance"

test-long-running:
	@echo "Running long-running tests (performance, stress, large datasets)..."
	@echo "⚠️  Warning: These tests may take 5-15 minutes to complete"
	@echo "Includes: comfyui_poll, comfyui_e2e, api_server, ontology_perf, and other longrunning tests"
	pytest test/ -v -m "longrunning"  --durations=0

test-performance:
	@echo "Running performance tests against live demo server..."
	@echo "⚠️  Prerequisites: Demo server must be running on port 8001"
	@echo "   Start with: make api-demo"
	pytest test/ -v -s -m "performance" --durations=0

test-tag-queries:
	@echo "Running tag query combination tests against demo database..."
	@echo "⚠️  Prerequisites: Demo server must be running on port 8001"
	@echo "   Start with: make api-demo"
	@echo "Note: These tests verify tag filtering correctness with real data"
	pytest test/ -v -s -m "tag_queries" --durations=0

test-comfyui-poll:
	@echo "Running mock ComfyUI polling tests (wait-for-completion scenarios)..."
	@echo "Note: These are also included in 'make test-long-running'"
	pytest test/ -v -m "comfyui_poll" --durations=0 --durations-min=0.5

test-comfyui-e2e:
	@echo "Running ComfyUI end-to-end workflow tests (Celery-style processing)..."
	@echo "Note: These are also included in 'make test-long-running'"
	pytest test/ -v -m "comfyui_e2e" --durations=0 --durations-min=0.5

test-api-server:
	@echo "Running API server integration suites (uvicorn startup, HTTP flows)..."
	@echo "Note: These are also included in 'make test-long-running' (some tests have both markers)"
	pytest test/ -v -m "api_server" --durations=0 --durations-min=0.5

test-ontology-perf:
	@echo "Running ontology performance/CLI tests (large datasets & subprocess calls)..."
	@echo "Note: These are standalone tests, not in 'make test-long-running'"
	pytest test/ -v -m "ontology_perf" --durations=0 --durations-min=0.5

test-all:
	@echo "Running ALL test suites (excluding manual tests)..."
	@echo "⚠️  Note: This may take 15-20 minutes and requires demo server on port 8001"
	@echo ""
	pytest test/ -v -m "not manual" --durations=0 --durations-min=0.5
	@echo ""
	@echo "✅ All test suites completed successfully!"
	@echo "Summary:"
	@echo "  ✓ Quick tests (not longrunning and not performance)"
	@echo "  ✓ Long-running tests (longrunning marker)"
	@echo "  ✓ Performance tests (performance marker - requires demo server)"
	@echo "  ✓ Ontology performance tests (ontology_perf marker)"
	@echo "  ✓ API server tests (api_server marker)"

# Three-tier testing approach
# - these are not exclusive sets of marked test sets (pytest.mark). These are just subsets of 'make test'
test-unit:
	@echo "Running unit tests (no external dependencies required)..."
	@echo "Testing: Pydantic models, utilities, exceptions, configuration"
	pytest test/api/unit/ -v --durations=0 --durations-min=0.5

test-db:
	@echo "Running database tests (database server required)..."
	@echo "Testing: repositories, services, database operations"
	@echo "Make sure your test database is initialized (make init-test) and configured in .env"
	pytest test/api/db/ test/db/ -v --durations=0 --durations-min=0.5

test-db-unit:
	@echo "Running database unit tests (no external dependencies required)..."
	@echo "Testing: Database models, utilities, initialization logic"
	pytest test/db/unit/ -v --durations=0 --durations-min=0.5

test-db-integration:
	@echo "Running database integration tests (database server required)..."
	@echo "Testing: Database operations, seeding, end-to-end workflows"
	@echo "Make sure your test database is initialized (make init-test) and configured in .env"
	pytest test/db/integration/ -v --durations=0 --durations-min=0.5

test-api:
	@echo "Running API integration tests (web server required)..."
	@echo "Testing: HTTP endpoints, complete workflows, error handling"
	@echo "Prerequisites: API server should be running on http://0.0.0.0:8001. (it's probably running; this is just a reminder)"
	@echo "Start with: make api-test"
	API_BASE_URL=http://0.0.0.0:8001 pytest test/api/integration/ -v --durations=0 --durations-min=0.5

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
	find . -type f -name "*.db" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

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

# ============================================
# DB commands
# ============================================
# Database initialization
init-db:
	@echo "Initializing database..."
	python -m genonaut.cli_main init-db --env-target local-dev

# not sure why we would have this, at least not on local-dev
#init-db-drop:
#	@echo "Initializing database (dropping existing tables)..."
#	python -m genonaut.cli_main init-db --env-target local-dev --drop-existing

# DB migration
# migrate-*: Create auto-generted revision based on SQLAlchemy model changes. Pass with a message, like: `make migrate-all m="my changes`
# !warning: if migrating multiple databases and their db schema is exactly the same, autogeneration should be fine, and
# can then be applied to all 3 databases via 'alembic upgrade head'. However, if they differ, and you create the
# migration using 1 database url, and then try to apply it, it will only work on the database(s) with matching schema.
migrate-all: migrate-demo migrate-dev migrate-test

migrate-all-auto: migrate-prep migrate-all

# todo: when demo is no longer the main DB, the canonical DB URL should change here to just: DATABASE_URL
# migrate-prep: Alt versions:
# dev:
# @ALEMBIC_SQLALCHEMY_URL=${DATABASE_URL} DATABASE_URL=${DATABASE_URL} alembic revision --autogenerate -m "$(m)"
# test:
# @TEST_URL=$${DATABASE_URL_TEST:-$${DATABASE_URL}}; \
# GENONAUT_DB_ENVIRONMENT=test DATABASE_URL=$$TEST_URL DATABASE_URL_TEST=$$TEST_URL ALEMBIC_SQLALCHEMY_URL=$$TEST_URL alembic revision --autogenerate -m "$(m)"
migrate-prep:
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('demo'))"); \
	ALEMBIC_SQLALCHEMY_URL="$$DB_URL" DATABASE_URL="$$DB_URL" alembic revision --autogenerate -m "$(m)"


# Function to run alembic upgrade with extensions check
# Usage: $(call run-migration,DATABASE_URL,[ENVIRONMENT])
define run-migration
	@python -m genonaut.db.schema_extensions install $(1)
	@echo "📦 Running database migration..."
	@$(if $(2),GENONAUT_DB_ENVIRONMENT=$(2) DATABASE_URL=$(1) DATABASE_URL_TEST=$(1),DATABASE_URL=$(1)) ALEMBIC_SQLALCHEMY_URL=$(1) alembic upgrade head
endef

migrate-dev:
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('dev'))") && \
	python -m genonaut.db.schema_extensions install "$$DB_URL" && \
	echo "📦 Running database migration..." && \
	DATABASE_URL="$$DB_URL" ALEMBIC_SQLALCHEMY_URL="$$DB_URL" alembic upgrade head

migrate-demo:
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('demo'))") && \
	python -m genonaut.db.schema_extensions install "$$DB_URL" && \
	echo "📦 Running database migration..." && \
	DATABASE_URL="$$DB_URL" ALEMBIC_SQLALCHEMY_URL="$$DB_URL" alembic upgrade head

# TODO temp
migrate-demo-temp:
	@DB_URL=postgresql://genonaut_admin:chocolateRainbows858@localhost:5432/genonaut_demo_restoretest && \
	python -m genonaut.db.schema_extensions install "$$DB_URL" && \
	echo "📦 Running database migration..." && \
	DATABASE_URL="$$DB_URL" ALEMBIC_SQLALCHEMY_URL="$$DB_URL" alembic upgrade head

migrate-test:
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('test'))") && \
	python -m genonaut.db.schema_extensions install "$$DB_URL" && \
	echo "📦 Running database migration..." && \
	GENONAUT_DB_ENVIRONMENT=test DATABASE_URL="$$DB_URL" DATABASE_URL_TEST="$$DB_URL" ALEMBIC_SQLALCHEMY_URL="$$DB_URL" alembic upgrade head

# Test-init database targets (for initialization/seeding tests)
init-test-init:
	@echo "Initializing test-init database (for init/seeding tests)..."
	python -m genonaut.cli_main init-db --env-target local-test-init

migrate-test-init:
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url_by_config; print(get_database_url_by_config('local-test-init'))") && \
	python -m genonaut.db.schema_extensions install "$$DB_URL" && \
	echo "📦 Running database migration on test-init..." && \
	ENV_TARGET=local-test-init APP_CONFIG_PATH=config/local-test-init.json DATABASE_URL="$$DB_URL" ALEMBIC_SQLALCHEMY_URL="$$DB_URL" alembic upgrade head

drop-test-init:
	@echo "Dropping test-init database..."
	@DB_PASSWORD=$${DB_PASSWORD_ADMIN} && \
	PGPASSWORD="$$DB_PASSWORD" psql -h localhost -U genonaut_admin -d postgres -c "DROP DATABASE IF EXISTS genonaut_test_init;"

recreate-test-init: drop-test-init init-test-init

migrate-down-dev:
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('dev'))") && \
	ALEMBIC_SQLALCHEMY_URL="$$DB_URL" DATABASE_URL="$$DB_URL" alembic downgrade -1

migrate-heads-dev:
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('dev'))") && \
	ALEMBIC_SQLALCHEMY_URL="$$DB_URL" DATABASE_URL="$$DB_URL" alembic heads

migrate-down-demo:
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('demo'))") && \
	ALEMBIC_SQLALCHEMY_URL="$$DB_URL" DATABASE_URL="$$DB_URL" alembic downgrade -1

migrate-heads-demo:
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('demo'))") && \
	ALEMBIC_SQLALCHEMY_URL="$$DB_URL" DATABASE_URL="$$DB_URL" alembic heads

# Backup targets
backup-dev:
	@echo "Backing up development database..."
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('dev'))") && \
	python -m genonaut.db.utils.backup "$$DB_URL"

backup-demo:
	@echo "Backing up demo database..."
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('demo'))") && \
	python -m genonaut.db.utils.backup "$$DB_URL"

backup-test:
	@echo "Backing up test database..."
	@DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('test'))") && \
	python -m genonaut.db.utils.backup "$$DB_URL"

backup: backup-dev backup-demo backup-test
	@echo "✅ All database backups completed!"

# ============================================
# Web API commands
# ============================================
# FastAPI server
# Legacy targets (use new targets below for explicit env control)
api-dev:
	@echo "Starting FastAPI server for development database..."
	python -m genonaut.cli_main run-api --env-target local-dev

api-demo:
	@echo "Starting FastAPI server for demo database..."
	python -m genonaut.cli_main run-api --env-target local-demo

api-demo-alt:
	@echo "Starting FastAPI server for demo database on port 8003..."
	python -m genonaut.cli_main run-api --env-target local-alt-demo

api-test:
	@echo "Starting FastAPI server for test database..."
	python -m genonaut.cli_main run-api --env-target local-test

# New environment-specific API targets
api-local-dev:
	@echo "Starting API server for local-dev environment..."
	python -m genonaut.cli_main run-api --env-target local-dev

api-local-demo:
	@echo "Starting API server for local-demo environment..."
	python -m genonaut.cli_main run-api --env-target local-demo

api-local-test:
	@echo "Starting API server for local-test environment..."
	python -m genonaut.cli_main run-api --env-target local-test

api-cloud-dev:
	@echo "Starting API server for cloud-dev environment..."
	python -m genonaut.cli_main run-api --env-target cloud-dev

api-cloud-demo:
	@echo "Starting API server for cloud-demo environment..."
	python -m genonaut.cli_main run-api --env-target cloud-demo

api-cloud-test:
	@echo "Starting API server for cloud-test environment..."
	python -m genonaut.cli_main run-api --env-target cloud-test

api-cloud-prod:
	@echo "Starting API server for cloud-prod environment..."
	python -m genonaut.cli_main run-api --env-target cloud-prod --reload=false

# FastAPI server variants for performance testing
api-dev-profile:
	@echo "Starting FastAPI server for development with profiling (single worker, no reload)..."
	python -m genonaut.cli_main run-api --env-target local-dev --workers 1 --reload=false

api-dev-load-test:
	@echo "Starting FastAPI server for load testing (4 workers)..."
	python -m genonaut.cli_main run-api --env-target local-dev --workers 4

api-production-sim:
	@echo "Starting FastAPI server simulating production (8 workers)..."
	python -m genonaut.cli_main run-api --env-target local-dev --workers 8

api-demo-load-test:
	@echo "Starting FastAPI server for demo load testing (4 workers)..."
	python -m genonaut.cli_main run-api --env-target local-demo --workers 4

api-test-load-test:
	@echo "Starting FastAPI server for test load testing (4 workers)..."
	python -m genonaut.cli_main run-api --env-target local-test --workers 4

# ============================================
# Queuing / message broking: Redis & Celery
# ============================================
celery-dev:
	@echo "Starting Celery worker with Beat scheduler for development environment..."
	@set -a && [ -f env/.env.shared ] && . env/.env.shared && [ -f env/.env.local-dev ] && . env/.env.local-dev && set +a && \
	ENV_TARGET=local-dev APP_CONFIG_PATH=config/local-dev.json celery -A genonaut.worker.queue_app:celery_app worker --loglevel=info --queues=default,generation -B --scheduler redbeat.RedBeatScheduler

celery-demo:
	@echo "Starting Celery worker with Beat scheduler for demo environment..."
	@set -a && [ -f env/.env.shared ] && . env/.env.shared && [ -f env/.env.local-demo ] && . env/.env.local-demo && set +a && \
	ENV_TARGET=local-demo APP_CONFIG_PATH=config/local-demo.json celery -A genonaut.worker.queue_app:celery_app worker --loglevel=info --queues=default,generation -B --scheduler redbeat.RedBeatScheduler

celery-test:
	@echo "Starting Celery worker with Beat scheduler for test environment..."
	@set -a && [ -f env/.env.shared ] && . env/.env.shared && [ -f env/.env.local-test ] && . env/.env.local-test && set +a && \
	ENV_TARGET=local-test APP_CONFIG_PATH=config/local-test.json celery -A genonaut.worker.queue_app:celery_app worker --loglevel=info --queues=default,generation -B --scheduler redbeat.RedBeatScheduler

# alt: python -c "from genonaut.api.services.generation_service import check_celery_workers_available; print('Workers available:', check_celery_workers_available())"
celery-check-running-workers:
	ps aux | grep celery | grep -v grep

# Show Celery Beat schedule status
beat-status: beat-status-demo

beat-status-dev:
	@set -a && [ -f env/.env.shared ] && . env/.env.shared && [ -f env/.env.local-dev ] && . env/.env.local-dev && set +a && \
	ENV_TARGET=local-dev APP_CONFIG_PATH=config/local-dev.json python genonaut/worker/beat_status.py

beat-status-demo:
	@set -a && [ -f env/.env.shared ] && . env/.env.shared && [ -f env/.env.local-demo ] && . env/.env.local-demo && set +a && \
	ENV_TARGET=local-demo APP_CONFIG_PATH=config/local-demo.json python genonaut/worker/beat_status.py

beat-status-test:
	@set -a && [ -f env/.env.shared ] && . env/.env.shared && [ -f env/.env.local-test ] && . env/.env.local-test && set +a && \
	ENV_TARGET=local-test APP_CONFIG_PATH=config/local-test.json python genonaut/worker/beat_status.py

# Specific tasks
# - refresh-tag-stats (AKA cardinality / popular tags)
refresh-tag-stats: refresh-tag-stats-demo

refresh-tag-stats-dev:
	@echo "🔄 Refreshing tag cardinality stats (dev database)..."
	@START=$$(date +%s); \
	DB_NAME=genonaut_dev python genonaut/db/refresh_tag_stats.py; \
	END=$$(date +%s); \
	ELAPSED=$$((END - START)); \
	echo "⏱️  Completed in $${ELAPSED}s"

refresh-tag-stats-demo:
	@echo "🔄 Refreshing tag cardinality stats (demo database)..."
	@START=$$(date +%s); \
	DB_NAME=genonaut_demo python genonaut/db/refresh_tag_stats.py; \
	END=$$(date +%s); \
	ELAPSED=$$((END - START)); \
	echo "⏱️  Completed in $${ELAPSED}s"

refresh-tag-stats-test:
	@echo "🔄 Refreshing tag cardinality stats (test database)..."
	@START=$$(date +%s); \
	DB_NAME=genonaut_test python genonaut/db/refresh_tag_stats.py; \
	END=$$(date +%s); \
	ELAPSED=$$((END - START)); \
	echo "⏱️  Completed in $${ELAPSED}s"

# - refresh-gen-source-stats
refresh-gen-source-stats: refresh-gen-source-stats-demo

refresh-gen-source-stats-dev:
	@echo "🔄 Refreshing gen source stats (dev database)..."
	@START=$$(date +%s); \
	DB_NAME=genonaut_dev python genonaut/db/refresh_gen_source_stats.py; \
	END=$$(date +%s); \
	ELAPSED=$$((END - START)); \
	echo "⏱️  Completed in $${ELAPSED}s"

refresh-gen-source-stats-demo:
	@echo "🔄 Refreshing gen source stats (demo database)..."
	@START=$$(date +%s); \
	DB_NAME=genonaut_demo python genonaut/db/refresh_gen_source_stats.py; \
	END=$$(date +%s); \
	ELAPSED=$$((END - START)); \
	echo "⏱️  Completed in $${ELAPSED}s"

refresh-gen-source-stats-test:
	@echo "🔄 Refreshing gen source stats (test database)..."
	@START=$$(date +%s); \
	DB_NAME=genonaut_test python genonaut/db/refresh_gen_source_stats.py; \
	END=$$(date +%s); \
	ELAPSED=$$((END - START)); \
	echo "⏱️  Completed in $${ELAPSED}s"


# Flower monitoring dashboard
flower-dev:
	@echo "Starting Flower dashboard for development environment..."
	@set -a && [ -f env/.env.shared ] && . env/.env.shared && [ -f env/.env.local-dev ] && . env/.env.local-dev && set +a && \
	ENV_TARGET=local-dev APP_CONFIG_PATH=config/local-dev.json celery -A genonaut.worker.queue_app:celery_app flower --port=5555

flower-demo:
	@echo "Starting Flower dashboard for demo environment..."
	@set -a && [ -f env/.env.shared ] && . env/.env.shared && [ -f env/.env.local-demo ] && . env/.env.local-demo && set +a && \
	ENV_TARGET=local-demo APP_CONFIG_PATH=config/local-demo.json celery -A genonaut.worker.queue_app:celery_app flower --port=5555

flower-test:
	@echo "Starting Flower dashboard for test environment..."
	@set -a && [ -f env/.env.shared ] && . env/.env.shared && [ -f env/.env.local-test ] && . env/.env.local-test && set +a && \
	ENV_TARGET=local-test APP_CONFIG_PATH=config/local-test.json celery -A genonaut.worker.queue_app:celery_app flower --port=5555

# Redis
REDIS_STORAGE_PATH=env/redis/storage/
REDIS_CONFIG_PATH=env/redis.conf

$(REDIS_STORAGE_PATH):
	mkdir -p $@

redis-start: | $(REDIS_STORAGE_PATH)
	redis-server $(REDIS_CONFIG_PATH)

redis-flush-dev:
	@echo "Flushing Redis DB 4 (dev)..."
	@redis-cli -a ${REDIS_PASSWORD} -n 4 FLUSHDB
	@echo "✅ Dev Redis DB flushed"

redis-flush-demo:
	@echo "Flushing Redis DB 2 (demo)..."
	@redis-cli -a ${REDIS_PASSWORD} -n 2 FLUSHDB
	@echo "✅ Demo Redis DB flushed"

redis-flush-test:
	@echo "Flushing Redis DB 3 (test)..."
	@redis-cli -a ${REDIS_PASSWORD} -n 3 FLUSHDB
	@echo "✅ Test Redis DB flushed"

redis-keys-dev:
	@echo "Listing keys in Redis DB 4 (dev)..."
	@redis-cli -a ${REDIS_PASSWORD} -n 4 KEYS '*'

redis-keys-demo:
	@echo "Listing keys in Redis DB 2 (demo)..."
	@redis-cli -a ${REDIS_PASSWORD} -n 2 KEYS '*'

redis-keys-test:
	@echo "Listing keys in Redis DB 3 (test)..."
	@redis-cli -a ${REDIS_PASSWORD} -n 3 KEYS '*'

redis-info-dev:
	@echo "Redis info for dev (DB 4)..."
	@redis-cli -a ${REDIS_PASSWORD} -n 4 DBSIZE

redis-info-demo:
	@echo "Redis info for demo (DB 2)..."
	@redis-cli -a ${REDIS_PASSWORD} -n 2 DBSIZE

redis-info-test:
	@echo "Redis info for test (DB 3)..."
	@redis-cli -a ${REDIS_PASSWORD} -n 3 DBSIZE

# ============================================
# Frontend helpers
# ============================================
frontend-install:
	@echo "Installing frontend dependencies..."
	npm --prefix frontend install

frontend-dev:
	@echo "Starting frontend dev server..."
	npm --prefix frontend run dev

frontend-dev-debug:
	@echo "Starting frontend dev server with debug logging..."
	npm --prefix frontend run dev:debug

frontend-dev-debug-alt:
	@echo "Starting frontend dev server with debug logging (port 8003 API, port 5174 frontend)..."
	VITE_API_BASE_URL=http://localhost:8003 npm --prefix frontend run dev:debug -- --port 5174

frontend-build:
	@echo "Building frontend..."
	npm --prefix frontend run build

frontend-preview:
	@echo "Previewing built frontend..."
	npm --prefix frontend run preview

# ============================================
# Frontend tests
# ============================================
# Configuration for parallel test execution
STRESS_FRONTEND_N_WORKERS ?= 5

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
	@echo "Running frontend Playwright tests (excluding performance tests)..."
	npm --prefix frontend run test:e2e -- --workers=1

frontend-test-e2e-headed:
	@echo "Running frontend Playwright tests in headed mode (excluding performance tests)..."
	npm --prefix frontend run test:e2e:headed -- --workers=1

frontend-test-e2e-ui:
	@echo "Running Playwright UI mode (excluding performance tests)..."
	npm --prefix frontend run test:e2e:ui

frontend-test-e2e-debug:
	@echo "Running frontend Playwright tests with debug logging (excluding performance tests)..."
	npm --prefix frontend run test:e2e:debug -- --workers=1

frontend-test-e2e-debug-headed:
	@echo "Running frontend Playwright tests with debug logging in headed mode (excluding performance tests)..."
	npm --prefix frontend run test:e2e:debug:headed -- --workers=1

frontend-test-e2e-skip-missing:
	@echo "Running frontend Playwright tests (skipping tests when data is missing)..."
	npm --prefix frontend run test:e2e:skip-missing -- --workers=1

# Multi-worker variants (-w suffix)
frontend-test-e2e-w:
	@echo "Running frontend Playwright tests with $(STRESS_FRONTEND_N_WORKERS) workers (excluding performance tests)..."
	npm --prefix frontend run test:e2e -- --workers=$(STRESS_FRONTEND_N_WORKERS)

frontend-test-e2e-headed-w:
	@echo "Running frontend Playwright tests in headed mode with $(STRESS_FRONTEND_N_WORKERS) workers (excluding performance tests)..."
	npm --prefix frontend run test:e2e:headed -- --workers=$(STRESS_FRONTEND_N_WORKERS)

frontend-test-e2e-debug-w:
	@echo "Running frontend Playwright tests with debug logging and $(STRESS_FRONTEND_N_WORKERS) workers (excluding performance tests)..."
	npm --prefix frontend run test:e2e:debug -- --workers=$(STRESS_FRONTEND_N_WORKERS)

frontend-test-e2e-debug-headed-w:
	@echo "Running frontend Playwright tests with debug logging in headed mode and $(STRESS_FRONTEND_N_WORKERS) workers (excluding performance tests)..."
	npm --prefix frontend run test:e2e:debug:headed -- --workers=$(STRESS_FRONTEND_N_WORKERS)

frontend-test-e2e-real-api:
	@echo "Running Playwright tests with real API server..."
	npm --prefix frontend run test:e2e:real-api -- --workers=1

frontend-test-e2e-real-api-headed:
	@echo "Running real API Playwright tests in headed mode..."
	npm --prefix frontend run test:e2e:real-api:headed -- --workers=1

frontend-test-e2e-real-api-ui:
	@echo "Running real API Playwright tests in UI mode..."
	npm --prefix frontend run test:e2e:real-api:ui

frontend-test-e2e-real-api-debug:
	@echo "Running real API Playwright tests with debug logging..."
	npm --prefix frontend run test:e2e:real-api:debug -- --workers=1

frontend-test-e2e-real-api-debug-headed:
	@echo "Running real API Playwright tests with debug logging in headed mode..."
	npm --prefix frontend run test:e2e:real-api:debug:headed -- --workers=1

frontend-test-e2e-real-api-skip-missing:
	@echo "Running real API Playwright tests (skipping tests when data is missing)..."
	npm --prefix frontend run test:e2e:real-api:skip-missing -- --workers=1

# Multi-worker variants (-w suffix)
frontend-test-e2e-real-api-w:
	@echo "Running Playwright tests with real API server and $(STRESS_FRONTEND_N_WORKERS) workers..."
	npm --prefix frontend run test:e2e:real-api -- --workers=$(STRESS_FRONTEND_N_WORKERS)

frontend-test-e2e-real-api-headed-w:
	@echo "Running real API Playwright tests in headed mode with $(STRESS_FRONTEND_N_WORKERS) workers..."
	npm --prefix frontend run test:e2e:real-api:headed -- --workers=$(STRESS_FRONTEND_N_WORKERS)

frontend-test-e2e-real-api-debug-w:
	@echo "Running real API Playwright tests with debug logging and $(STRESS_FRONTEND_N_WORKERS) workers..."
	npm --prefix frontend run test:e2e:real-api:debug -- --workers=$(STRESS_FRONTEND_N_WORKERS)

frontend-test-e2e-real-api-debug-headed-w:
	@echo "Running real API Playwright tests with debug logging in headed mode and $(STRESS_FRONTEND_N_WORKERS) workers..."
	npm --prefix frontend run test:e2e:real-api:debug:headed -- --workers=$(STRESS_FRONTEND_N_WORKERS)

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
test-frontend-e2e-debug: frontend-test-e2e-debug
test-frontend-e2e-debug-headed: frontend-test-e2e-debug-headed
test-frontend-e2e-w: frontend-test-e2e-w
test-frontend-e2e-headed-w: frontend-test-e2e-headed-w
test-frontend-e2e-debug-w: frontend-test-e2e-debug-w
test-frontend-e2e-debug-headed-w: frontend-test-e2e-debug-headed-w
test-frontend-e2e-real-api: frontend-test-e2e-real-api
test-frontend-e2e-real-api-headed: frontend-test-e2e-real-api-headed
test-frontend-e2e-real-api-ui: frontend-test-e2e-real-api-ui
test-frontend-e2e-real-api-debug: frontend-test-e2e-real-api-debug
test-frontend-e2e-real-api-debug-headed: frontend-test-e2e-real-api-debug-headed
test-frontend-e2e-real-api-w: frontend-test-e2e-real-api-w
test-frontend-e2e-real-api-headed-w: frontend-test-e2e-real-api-headed-w
test-frontend-e2e-real-api-debug-w: frontend-test-e2e-real-api-debug-w
test-frontend-e2e-real-api-debug-headed-w: frontend-test-e2e-real-api-debug-headed-w

# todo: find a better place in file
# ============================================
# Integration checks
# ============================================
## ComfyUI
COMFY_EXAMPLE_FILE=test/integrations/comfy_ui/input/1.json
COMFY_HOST=127.0.0.1
COMFY_PORT=8000  # Manual/portable (python main.py): defaults to 8000 unless you set --port. Desktop app (macOS build): commonly ships with 8000 as the baked-in default.

comfyui-mock:
	@echo "Starting mock ComfyUI server on port 8189..."
	python test/_infra/mock_services/comfyui/server.py

check-comfyui-create-img:
	curl -X POST http://localhost:8000/prompt \
	     -H "Content-Type: application/json" \
	     -d @$${COMFY_EXAMPLE_FILE}

# ============================================
# Infrastructure
# ============================================
# Note: If terraform gives error like "│ Error: No valid credential sources found", run: `make aws login`

# Terraform directories
DEPLOY_TF_BOOTSTRAP_DIR := infra/bootstrap
DEPLOY_MAIN_DIR := infra/main
DEPLOY_ENVS := dev test demo prod
DEPLOY_RECONFIGURE ?= 1  # add this flag so switching envs doesn't error
INIT_FLAGS := $(if $(DEPLOY_RECONFIGURE),-reconfigure,)

# Login
# This goal is used to make sure your local CLI session is authenticated
# with AWS via SSO before running Terraform or other AWS CLI commands.
# `aws sts get-caller-identity` is a diagnostic command — it prints
# the current authenticated AWS account ID, user ARN, and user ID.
# If this succeeds, Terraform will also have valid credentials.
aws-login:
#	@echo ">>> Logging in with AWS SSO for profile: $(DEPLOY_AWS_PROFILE)"
#	AWS_PROFILE=$(DEPLOY_AWS_PROFILE) AWS_REGION=$(DEPLOY_AWS_REGION) AWS_SDK_LOAD_CONFIG=1 \
#		aws sso login
	@echo ">>> Verifying AWS identity..."
	AWS_PROFILE=$(DEPLOY_AWS_PROFILE) AWS_REGION=$(DEPLOY_AWS_REGION) AWS_SDK_LOAD_CONFIG=1 \
		aws sso login --profile $(DEPLOY_AWS_PROFILE)
	AWS_PROFILE=$(DEPLOY_AWS_PROFILE) AWS_REGION=$(DEPLOY_AWS_REGION) AWS_SDK_LOAD_CONFIG=1 \
		aws sts get-caller-identity  --profile $(DEPLOY_AWS_PROFILE)
	@echo "✅ Login complete — credentials are valid."

tf-login: aws-login

# Bootstrap commands: 1-time setup
tf-bootstrap-init:
	cd $(DEPLOY_TF_BOOTSTRAP_DIR) && \
	AWS_PROFILE=$(DEPLOY_AWS_PROFILE) AWS_REGION=$(DEPLOY_AWS_REGION) \
	terraform init

tf-bootstrap-apply:
	cd $(DEPLOY_TF_BOOTSTRAP_DIR) && \
	AWS_PROFILE=$(DEPLOY_AWS_PROFILE) AWS_REGION=$(DEPLOY_AWS_REGION) \
	terraform apply -auto-approve \
	  -var="state_bucket_name=$(DEPLOY_TF_STATE_BUCKET_NAME)" \
	  -var="dynamodb_table_name=$(DEPLOY_TF_DYNAMO_DB_TABLE)" \
	  -var="region=$(DEPLOY_AWS_REGION)"

tf-bootstrap-destroy:
	cd $(DEPLOY_TF_BOOTSTRAP_DIR) && \
	AWS_PROFILE=$(DEPLOY_AWS_PROFILE) AWS_REGION=$(DEPLOY_AWS_REGION) \
	terraform destroy -auto-approve \
	  -var="state_bucket_name=$(DEPLOY_TF_STATE_BUCKET_NAME)" \
	  -var="dynamodb_table_name=$(DEPLOY_TF_DYNAMO_DB_TABLE)" \
	  -var="region=$(DEPLOY_AWS_REGION)"

# Main commands
# - generator for per-env terraform targets
define TF_ENV_RULES
.PHONY: tf-init-$(1) tf-plan-$(1) tf-apply-$(1) tf-destroy-$(1)
tf-init-$(1):
	cd $(DEPLOY_MAIN_DIR) && \
	AWS_PROFILE=$(DEPLOY_AWS_PROFILE) AWS_REGION=$(DEPLOY_AWS_REGION) \
	terraform init $(INIT_FLAGS) \
	  -backend-config="bucket=$(DEPLOY_TF_STATE_BUCKET_NAME)" \
	  -backend-config="key=envs/$(1)/terraform.tfstate" \
	  -backend-config="region=$(DEPLOY_AWS_REGION)" \
	  -backend-config="dynamodb_table=$(DEPLOY_TF_DYNAMO_DB_TABLE)" \
	  -backend-config="encrypt=true"

tf-plan-$(1):
	cd $(DEPLOY_MAIN_DIR) && \
	AWS_PROFILE=$(DEPLOY_AWS_PROFILE) AWS_REGION=$(DEPLOY_AWS_REGION) \
	terraform plan \
		-var="env=$(1)" \
		-var="region=$(DEPLOY_AWS_REGION)"

tf-apply-$(1):
	cd $(DEPLOY_MAIN_DIR) && \
	AWS_PROFILE=$(DEPLOY_AWS_PROFILE) AWS_REGION=$(DEPLOY_AWS_REGION) \
	terraform apply -auto-approve \
		-var="env=$(1)" \
		-var="region=$(DEPLOY_AWS_REGION)"

tf-destroy-$(1):
	cd $(DEPLOY_MAIN_DIR) && \
	AWS_PROFILE=$(DEPLOY_AWS_PROFILE) AWS_REGION=$(DEPLOY_AWS_REGION) \
	terraform destroy -auto-approve \
	  -var="env=$(1)" \
	  -var="region=$(DEPLOY_AWS_REGION)"
endef

$(foreach e,$(DEPLOY_ENVS),$(eval $(call TF_ENV_RULES,$(e))))

# default: demo
tf-init:   tf-init-demo
tf-plan:   tf-plan-demo
tf-apply:  tf-apply-demo
tf-destroy: tf-destroy-demo

# Utility commands
tf-fmt:
	cd $(DEPLOY_MAIN_DIR) && terraform fmt -recursive

tf-validate:
	cd $(DEPLOY_MAIN_DIR) && terraform validate

tf-console:
	cd $(DEPLOY_MAIN_DIR) && terraform console

# ============================================
# Helper libs
# ============================================
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

# Cache Analysis Tools
.PHONY: cache-analysis cache-analysis-relative

cache-analysis:
	@ENV_TARGET=local-demo python -m genonaut.cli.cache_analysis \
		--count=$(or $(n),10) \
		--days=$(or $(days),7) \
		--format=$(or $(format),table)

cache-analysis-relative:
	@ENV_TARGET=local-demo python -m genonaut.cli.cache_analysis_relative \
		--count=$(or $(n),10) \
		--days=$(or $(days),7) \
		--format=$(or $(format),table)

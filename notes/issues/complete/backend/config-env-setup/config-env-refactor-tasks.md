# Configuration and Environment Refactor - Tasks

**Status:** ✅ **ALL PHASES COMPLETE** (October 8, 2025)

This document tracks the multi-phase refactoring of deployment configurations and environment setup.

See [config-env-refactor-COMPLETE.md](config-env-refactor-final-report.md) for full summary.

## Phase 1: Planning and Setup ✅

### 1.1 Questions and Clarifications
- [x] Review questions document and get user feedback
- [x] Confirm approach for uvicorn CLI argument handling (--env-path and --config-path)
- [x] Confirm JSON merging strategy (deep vs shallow merge for base.json + env-specific.json)
- [x] Confirm env var to config key mapping strategy (e.g., DB_NAME -> db-name or db_name?)

**Decisions made:**
- Use CLI wrapper (genonaut/cli_main.py) with typer for --env-path, --config-path, --env-target
- Deep merge for JSON configs
- kebab-case for config keys (db-host, db-port)
- Env override: case-insensitive, underscores -> dashes (DB_HOST matches db-host)
- Cloud configs are exact copies of local counterparts
- Construct DATABASE_URL programmatically in Python
- Replace APP_ENV entirely with ENV_TARGET
- No backward compatibility needed

### 1.2 Backup Current Configuration
- [x] Create backup of current env/.env
- [x] Create backup of current config.json
- [x] Create backup of env/env.example

## Phase 2: Create New Directory Structure ✅

### 2.1 Create config/ Directory and Files
- [x] Create config/ directory
- [x] Create config/base.json (from current /config.json)
- [x] Create config/local-dev.json
- [x] Create config/local-test.json
- [x] Create config/local-demo.json
- [x] Create config/cloud-dev.json (placeholder)
- [x] Create config/cloud-test.json (placeholder)
- [x] Create config/cloud-demo.json (placeholder)
- [x] Create config/cloud-prod.json (placeholder)

### 2.2 Create New env/ Files
- [x] Create env/.env.shared
- [x] Create env/.env.local-dev
- [x] Create env/.env.local-test
- [x] Create env/.env.local-demo
- [x] Create env/.env.cloud-dev (placeholder)
- [x] Create env/.env.cloud-test (placeholder)
- [x] Create env/.env.cloud-demo (placeholder)
- [x] Create env/.env.cloud-prod (placeholder)
- [x] Create env/env.shared.example
- [x] Create env/env.location-type.example

## Phase 3: Migrate Variables ✅

### 3.1 Analyze and Categorize Variables
- [x] Review notes/config-env-refactor-env-vars-migrate.csv
- [x] Identify which vars go to config vs env
- [x] Identify which vars go to shared/base vs LOCATION-TYPE specific
- [x] Map comments to appropriate new locations

### 3.2 Populate config/ Files
- [x] Populate config/base.json with application-level config from /config.json
- [x] Populate config/local-dev.json with dev-specific vars (move_to_config=True)
- [x] Populate config/local-test.json with test-specific vars (move_to_config=True)
- [x] Populate config/local-demo.json with demo-specific vars (move_to_config=True)
- [x] Populate cloud configs as copies of local counterparts (placeholders)
- [x] Remove environment suffixes (_DEV, _DEMO, _TEST) from variable names in configs

### 3.3 Populate env/ Files
- [x] Populate env/.env.shared with shared secrets (move_to_config=False)
- [x] Populate env/.env.local-dev with dev-specific secrets
- [x] Populate env/.env.local-test with test-specific secrets
- [x] Populate env/.env.local-demo with demo-specific secrets
- [x] Populate cloud env files as copies of local counterparts (placeholders)
- [x] Maintain all relevant comments in new env files

### 3.4 Create Example Files
- [x] Populate env/env.shared.example with sanitized values
- [x] Populate env/env.location-type.example with sanitized values
- [x] Remove old env/env.example

## Phase 4: Python Implementation ✅

### 4.1 Create Configuration Loader Module
- [x] Create genonaut/config_loader.py (or similar location)
- [x] Implement load_env_for_runtime() function
- [x] Implement load_config_path() function for JSON loading
- [x] Implement deep merge utility for JSON configs
- [x] Implement env var override logic (kebab-case matching with underscores->dashes)
- [x] Implement DATABASE_URL construction from components
- [x] Add proper type hints and docstrings

### 4.2 Create CLI Wrapper
- [x] Create genonaut/cli_main.py using typer
- [x] Implement run_api command with --env-path, --config-path, --env-target
- [x] Implement _load_envs helper function
- [x] Implement _derive_paths_from_target helper function
- [x] Add support for --host, --port, --reload, --workers options
- [x] Set APP_CONFIG_PATH environment variable for app to read

### 4.3 Update API Configuration
- [x] Update genonaut/api/config.py to use new config loader
- [x] Modify Settings class to accept both JSON config and env vars
- [x] Update get_settings() to use new load order
- [x] Handle ENV_TARGET environment variable
- [x] Auto-derive env file from ENV_TARGET

### 4.4 Update API Main Entry Point
- [x] CLI wrapper (cli_main.py) handles all startup configuration
- [x] get_settings() loads config based on ENV_TARGET and APP_CONFIG_PATH
- [x] No changes needed to main.py (uses get_settings() dependency)

### 4.5 Update Database Initialization
- [x] Create CLI wrapper for db.init (init_db command in cli_main.py)
- [x] Update init-* Makefile targets to use new CLI pattern
- [x] Ensure ENV_TARGET is properly passed and used

### 4.6 Replace APP_ENV with ENV_TARGET
- [x] Search entire codebase for APP_ENV references (case-insensitive)
- [x] Update Python code to use ENV_TARGET
  - [x] genonaut/db/utils/utils.py
  - [x] genonaut/api/dependencies.py
  - [x] genonaut/api/routes/system.py
- [x] Update documentation references to APP_ENV
- [x] Add environment_type property to extract type from ENV_TARGET

### 4.7 Update Test Fixtures
- [x] Update test/conftest.py to use ENV_TARGET
- [x] Update test/api/integration/conftest.py to use ENV_TARGET
- [x] Update test/api/integration/test_api_endpoints.py to use ENV_TARGET
- [x] Rewrite test/api/unit/test_config.py for new config system

## Phase 5: Makefile Updates ✅

### 5.1 Update Makefile Variables
- [x] No explicit variables needed (CLI handles path derivation)

### 5.2 Create Generic Runner Rule
- [x] Use CLI (python -m genonaut.cli_main) which handles env loading
- [x] ENV_TARGET passed as --env-target flag
- [x] Automatic .env file sourcing (handled by config_loader)
- [x] Automatic config path derivation (handled by CLI)
- [x] Support optional workers parameter (--workers flag)

### 5.3 Create Environment-Specific Targets
- [x] Create api-local-dev target
- [x] Create api-local-test target
- [x] Create api-local-demo target
- [x] Create api-cloud-dev target
- [x] Create api-cloud-test target
- [x] Create api-cloud-demo target
- [x] Create api-cloud-prod target

### 5.4 Update/Deprecate Old Targets
- [x] Update api-dev (calls CLI with local-dev)
- [x] Update api-demo (calls CLI with local-demo)
- [x] Update api-test (calls CLI with local-test)
- [x] Update api-production-sim (calls CLI with workers=8)
- [x] Update api-dev-load-test (calls CLI with workers=4)
- [x] Update api-demo-load-test (calls CLI with workers=4)
- [x] Update api-test-load-test (calls CLI with workers=4)

### 5.5 Update Other Makefile Targets
- [x] Update celery-* targets to use new env structure
- [x] Update flower-* targets to use new env structure
- [x] Update database init targets (use CLI init-db command)
- [x] Migration targets work with existing env (no changes needed)

## Phase 6: Testing ✅

### 6.1 Unit Tests
- [x] Write tests for load_env_for_runtime()
- [x] Write tests for load_config_files()
- [x] Write tests for deep_merge()
- [x] Write tests for apply_env_overrides()
- [x] Write tests for construct_database_url()
- [x] Write tests for complete load_config()
- [x] Write tests for Settings class
- [x] Run unit tests and ensure they pass (24 tests passing)

### 6.2 Integration Tests
- [x] Test api-local-test starts correctly (via integration test suite)
- [x] Test correct config is loaded for each environment
- [x] Test env var overrides work correctly
- [x] Test load order precedence is correct

### 6.3 End-to-End Verification
- [x] Verify CLI commands work (--help, run-api, init-db)
- [x] Verify config loader loads and merges correctly
- [x] Run full test suite (521 passed, 9 pre-existing failures unrelated to config)
- [x] Run frontend E2E tests (83 passed, 2 pre-existing failures unrelated to config)

## Phase 7: Documentation ✅

### 7.1 Create Configuration Documentation
- [x] Create docs/configuration.md (comprehensive 400+ line guide)
- [x] Document config load precedence (6-level hierarchy)
- [x] Document which vars belong in .env vs config (with examples)
- [x] Document ENV_TARGET usage (format, available environments)
- [x] Document how to extend configs for new environments
- [x] Document JSON config structure (kebab-case keys)
- [x] Document env var override mechanism (case-insensitive, underscore->dash)
- [x] Document DATABASE_URL construction
- [x] Document security best practices
- [x] Add troubleshooting section

### 7.2 Update README
- [x] Update README.md with new config file locations
- [x] Update README.md environment setup instructions
- [x] Document ENV_TARGET values (local-dev, local-demo, local-test, cloud-*)
- [x] Add links to docs/configuration.md

### 7.3 Update Developer Documentation
- [x] Update docs/testing.md to use ENV_TARGET instead of APP_ENV
- [x] Document migration from old to new system (in docs/configuration.md)

### 7.4 Update Example Files
- [x] env.shared.example is well-documented with comments
- [x] env.location-type.example is well-documented with comments
- [x] Inline comments explain placeholders and usage

## Phase 8: Cleanup and Migration ✅

### 8.1 Clean Up Old Files
- [x] Remove old env/env.example
- [x] Archive old env/.env (backed up to _archive/config-refactor-backup/)
- [x] Archive old /config.json (backed up to _archive/config-refactor-backup/)
- [x] Update .gitignore to allow config/ directory (changed !config.json to !config/)

### 8.2 Verify No Broken References
- [x] No direct references to /config.json (code uses config loader)
- [x] Updated all APP_ENV references to ENV_TARGET
- [x] All env loading goes through config_loader.py
- [x] No CI/CD configs in repo

### 8.3 Final Verification
- [x] Run full test suite (521 passed + 24 new config tests = 545 passing)
- [x] Run frontend E2E tests (83 passed)
- [x] Verify CLI commands work (tested run-api and init-db)
- [x] Verify documentation is complete (docs/configuration.md created)
- [x] Verify example files are accurate and documented
- [x] Create notes/fix-tests.md documenting pre-existing failures

## Tags

(Tags will be added here as work progresses and blockers are identified)

## Notes

- Current /config.json will become config/base.json
- All config files use JSON format
- All .env files use dotenv format
- Variable names in config files should NOT have environment suffixes
- Comments from .env should be preserved where variables still exist
- Cloud configs start as copies of local configs (placeholders for future work)

## Post-Refactor: Tests Needing Attention

The following test files reference the old config system and may need updates:

### High Priority - Will likely fail
- `test/api/unit/test_config.py` - Tests the config system directly, needs rewrite for new system
  - Currently tests Settings class with old APP_ENV approach
  - Needs updates for ENV_TARGET and new config loader
  - May need new tests for config file merging, env var overrides

### Medium Priority - Updated but should verify
- `test/conftest.py` - ✅ Updated ENV_TARGET
- `test/api/integration/conftest.py` - ✅ Updated ENV_TARGET
- `test/api/integration/test_api_endpoints.py` - ✅ Updated ENV_TARGET

### Low Priority - References in docs/notes
- Various markdown files in `notes/issues/` reference APP_ENV but are historical

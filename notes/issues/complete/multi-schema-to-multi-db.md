# DB Restructure Plan

## Current Observations
- `get_database_url()` always targets `DB_NAME` (`genonaut`) and does not differentiate between app/demo contexts.
- Database init pipeline (`genonaut/db/init.py`) creates two schemas (`app`, `demo`) inside a single database.
- `init.sql` provisions roles and only creates the `genonaut` database; schemas get created later by Python code.
- Alembic env (`genonaut/db/migrations/env.py`) always connects via `get_database_url()` with no knob for the demo database.
- Tests (e.g., `test/test_database_postgres_integration.py`) assert the presence of both `app` and `demo` schemas within one DB.
- Makefile currently has generic migration targets (`migrate-up/down`) and a single `init` that targets one DB.

## Desired End State
- Two separate databases: `genonaut` and `genonaut_demo` (names configurable via `DB_NAME` / `DB_NAME_DEMO`).
- Ability to select DB context (dev vs demo) when constructing the SQLAlchemy URL, running migrations, and initializing.
- `make migrate-dev` and `make migrate-demo` targets that set a `DEMO` flag and run Alembic upgrades against the appropriate DB.
- `make init` (or related helpers) should bootstrap both databases with the correct schemas/tables/seed data rather than creating schemas inside a single DB.

## Key Work Items
- Update `get_database_url` to accept either a `demo: bool` parameter or to respect a `DEMO` environment variable when building URLs.
- Plumb the demo flag through call sites: database initializer, Alembic environment, Makefile targets, CLI helpers, tests.
- Adjust initialization flow in `genonaut/db/init.py` so it can create two separate databases (potentially via two passes of the initializer or a loop).
- Rework `init.sql` (or create an additional template) to support creating both databases and applying grants.
- Rewrite tests that currently assume schemas to align with the two-DB design; add coverage for both dev/demo initialization paths.
- Ensure documentation (`README.md`, developer docs) reflects the new DB setup and environment variables.



## User Decisions / Clarifications
- Shared roles (`genonaut_admin`, `genonaut_rw`, `genonaut_ro`) remain for both databases.
- `make init` should initialize only the main database; add a new `make init-demo` target for the demo DB.
- Drop the `app`/`demo` schemas; each database uses `public` going forward.
- Demo database requires distinct seed data. Create a top-level `config.json` to declare seed data paths per database and have `init.py` load the appropriate one.
- No downstream dependencies on the old schema names.

## Updated Task Breakdown
- [x] Extend `get_database_url(demo: bool = False)` (and/or `DEMO` env handling) to select `DB_NAME` vs `DB_NAME_DEMO`.
- [x] Update Alembic wiring (`genonaut/db/migrations/env.py`, Make targets) to respect demo flag/`DEMO` env, and add `make migrate-dev`/`make migrate-demo` goals.
- [x] Refactor `DatabaseInitializer`/`initialize_database` to handle separate DBs, remove schema creation logic, and call seed routines based on new config file.
- [x] Create `config.json` with seed path definitions; adjust init pipeline to read from it.
- [x] Update `init.sql` (or introduce companion template section) to create both databases or run per DB without schema specifics.
- [x] Introduce `make init-demo` target and ensure `make init` handles main DB only.
- [x] Revise tests (unit + integration) to align with two-database approach and ensure coverage for both contexts.
- [x] Refresh docs (README, developer docs) to describe the new environment variables and workflow.

## Design Outline (draft)
- Extend `get_database_url` signature to `get_database_url(demo: Optional[bool] = None)`; default picks up `DEMO` env (treated as truthy when `"1"`, `"true"`, etc.). Choose DB name via `DB_NAME`/`DB_NAME_DEMO` env with sensible defaults.
- Update `DatabaseInitializer` to accept `demo` flag (store on instance, forward to `get_database_url`, reuse for seed selection, logging).
- Replace schema-centric initialization with database-level flow:
  - Remove `create_schemas` calls for normal execution.
  - `initialize_database` selects seed path via config (see below), conditionally seeds using returned path.
  - Keep optional `schema_name` for tests but make it deprecated/limited to Postgres test helpers; default path uses public schema only.
- Introduce repository-root `config.json` structure:
  ```json
  {
    "seed_data": {
      "main": "io/input/init/rdbms",
      "demo": "docs/demo/demo_app/init/rdbms"
    }
  }
  ```
  - `main` corresponds to primary DB; `demo` to demo DB. `initialize_database` resolves appropriate key based on `demo` flag with safe fallbacks and clear error if path missing.
- Adjust `init.sql` to: ensure both databases exist (create if not), or refactor to be parameterized per DB run. Keep shared roles/grants; switch to templated block that can be run twice (main + demo) driven by python rather than embedding both in SQL.
- Alembic changes: allow `DEMO` env or CLI override to pick DB when running migrations; update Make targets to set `DEMO` appropriately.
- Seed logic: maintain TSV import; ensure `seed_from_tsv_directory` uses whichever path provided (likely now per DB; still optional).
- Tests: update Postgres integration tests to verify separate DB behavior (no `app`/`demo` schemas, multiple DB connections); adjust unit tests for `get_database_url` to cover `demo=True` and `DEMO` env fallback.
- Documentation: README / developer docs note new env var `DB_NAME_DEMO`, mention `DEMO` flag workflow, describe new Make targets (`init-demo`, `migrate-dev`, `migrate-demo`).

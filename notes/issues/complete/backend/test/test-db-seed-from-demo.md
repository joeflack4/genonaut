# Preamble
Ok. I'd like to come up with a way to properly seed our test database. Right now we have two existing ways in the 
codebase to do this:

1. Test static files: There are some TSVs with very few rows that we can simply import. I think in some cases this is 
already being done during some test setUps. We can continue to let that happen. But we can't entirely rely on this 
2. because the DB has many more tables now than is represented by these TSVs.
Seed data generation / synthetic data: Located at path: genonaut/db/demo/seed_data_gen/. This will run a complex 
script that takes probably at least 20 minutes, which loads the database up with more than a million rows in most of the
tables in the DB.

So, we have these two methods, but neither of them are very good. I want to propose a new way to ensure the test 
database is seeded with sufficient data for tests: exporting some rows from the demo database. So that's what we're 
going to do now.

I want to export up to 100 rows from every table in the database. However, many rows have foreign key dependencies that 
need to be respected, so we can’t just export the first 100 rows of each table blindly. We need to identify which tables 
are independent first, export rows from those, and then recursively traverse dependent tables to export only the rows 
that match the foreign key relationships based on the data we’ve already selected.

Put a new script for this in: genonaut/db/demo/seed_data_gen/. Make a makefile command that can call it, which will do 
the export. It needs to connect to the demo database and then do the export. Then another command which does the import
of this into the test database. Then, a 3rd command which does both of those things in order.

For the import, we have a similar problem in that some rows will be dependent on other rows, so you should make sure 
that the importer imports things in the correct order.

The files should be exported as TSVs in: test/db/input/rdbms_init_from_demo/. We will commit these and update them 
periodically.

Start by thinking about this and writing a multi-phase set of lists of markdown checkbox tasks below. Then begin 
executing on those tasks.

# Tasks

## Phase 1 – Scoping & Data Requirements
- [x] Confirm connection details + credentials for demo (`genonaut_demo`) and test (`genonaut_test`) DBs
- [x] Inventory tables + critical foreign-key chains to understand export ordering needs
- [x] Define maximum row counts per table (default 100, allow overrides for small/high-priority tables)
- [x] Decide deterministic selection criteria (e.g., ORDER BY primary key) to keep exports stable

## Phase 2 – Export Tooling
- [x] Design Python script `export_seed_from_demo.py` (location: `genonaut/db/demo/seed_data_gen/`)
- [x] Implement dependency graph builder (introspect `information_schema` to know FK parents/children)
- [x] Generate export plan: start from independent tables, then traverse dependents filtering to matching FK values
- [x] Dump selected rows to TSV files under `test/db/input/rdbms_init_from_demo/`
- [x] Ensure TSV schema includes header row + consistent column ordering via SQLAlchemy metadata

## Phase 3 – Import Tooling
- [x] Design importer script `import_seed_to_test.py` in same directory
- [x] Reuse dependency order to import parents before children; wrap per-table inserts in transactions
- [x] Add upsert/`ON CONFLICT DO NOTHING` handling so repeated imports are idempotent
- [x] Validate constraints post-import (counts per table, missing FK rows, etc.)

## Phase 4 – Makefile + Automation
- [x] Add `make export-demo-seed` (runs exporter against demo DB)
- [x] Add `make import-demo-seed-to-test` (loads TSVs into test DB)
- [x] Add `make refresh-test-seed-from-demo` that chains export + import
- [x] Ensure commands activate `env/python_venv` automatically and accept optional limits/flags

## Phase 5 – Verification & Docs
- [ ] Smoke-test exporter/importer locally; confirm TSVs are generated + applied successfully
- [ ] Document workflow in `docs/testing.md` (or new doc) and mention new Make targets in README quick reference
- [ ] Note schedule/process for updating committed TSV snapshots

## Phase 6 – Completeness Guardrails
- [x] Investigate zero-row exports for `tag_ratings`, `user_notifications`, `user_search_history`, and `user_interactions`
- [x] Add export-time assertion so tables that contain rows in the source DB can never silently skip
- [x] Re-run exporter/importer once guards are in place to ensure these tables populate their TSVs

# Reports

## 2025-10-26 Phase 1 notes
- Demo DB: `genonaut_demo` (config/local-demo.json) on localhost:5432, accessed via `genonaut_admin` / `genonaut_rw` / `genonaut_ro`; passwords in `env/.env.shared` (`DB_PASSWORD_ADMIN`, etc.).
- Test DB: `genonaut_test` (config/local-test.json) same host/port and credential set.
- Default connection strings follow `postgresql://genonaut_admin:<DB_PASSWORD_ADMIN>@localhost:5432/<db>`; `DATABASE_URL_TEST` is available for direct wiring.
- FK inventory summary (from `genonaut/db/schema.py`):
  - Root tables (no incoming FK requirements): `users`, `tags`, `available_models`, `models_checkpoints`, `models_loras`, `generation_events`, `generation_metrics_hourly`, `route_analytics`, `route_analytics_hourly`.
  - Content hierarchy: `content_items`/`content_items_auto` depend on `users`; `content_items_ext` & `_auto_ext` depend on their parents; `content_tags` bridges `content_(items|auto)` -> `tags` using `content_source` discriminator.
  - Engagement data: `user_notifications`, `user_search_history`, `user_interactions`, `recommendations`, `generation_jobs`, `flagged_content`, `gen_source_stats`, `route_analytics`, `route_analytics_hourly`, `tag_ratings`, `tag_cardinality_stats` reference `users`/`tags`/`content_items`.
  - Taxonomy helpers: `tag_parents`, `tag_ratings`, `tag_cardinality_stats` depend on `tags` (and `users` for ratings).
  - Generation metadata: `generation_jobs` -> (`users`, `content_items`), `generation_events` (no FK), `generation_metrics_hourly` (aggregated, no FK), `generation_events` referencing optional `user_id` w/o constraint.
  - Analytics tables mostly reference `users` optionally; can be imported late because they only depend on base ids selected elsewhere.
- Row-count plan: default cap 100 rows/table plus override map (still <=100) for special cases (e.g., `content_items_auto_ext` 50, `route_analytics` 50, `route_analytics_hourly` 24, `generation_metrics_hourly` 24). Scripts will expose CLI flags to change defaults without editing code.
- Deterministic selection: exporter will introspect each table's primary key columns via SQLAlchemy metadata, `ORDER BY` them ascending, and (for compound PKs) order by each component. When PK is synthetic but not monotonic (e.g., `content_tags` triple key), we still order by the composite to keep stable diff-friendly TSVs; fallback order will be `created_at` then PK if metadata lacks PK info.

## 2025-10-26 Phase 2 notes
- Added `genonaut/db/demo/seed_data_gen/export_seed_from_demo.py`:
  - Uses SQLAlchemy metadata + `TopologicalSorter` to derive dependency order (excludes `alembic_version`, `content_items_all`).
  - Applies FK-aware filters so dependent tables only export rows whose parent IDs are part of the sampled dataset (nullable FKs fall back to `IS NULL` checks).
  - Serializes rows to TSV with header rows + deterministic column order, honoring per-table limit overrides (`--table-limit content_tags=80`) and default limit flags.
  - Outputs to `test/db/input/rdbms_init_from_demo/` by default; directory creation handled automatically.
  - CLI exposes `--tables` subset selection, custom output path, and verbosity control.
- Local Postgres access is blocked inside the current sandbox (connection attempts to `localhost:5432` return “Operation not permitted”), so exporter hasn't been smoke-tested yet; expected to work once run directly on the host with DB access.

### 2025-10-27 Exporter follow-up
- Dependent tables like `tag_ratings`, `user_notifications`, and `user_search_history` were coming up empty when the sampled parent rows (first 100 users/tags) didn’t cover their foreign keys. The exporter now deduplicates all rows in memory and, whenever it exports a child row, automatically pulls in any missing parent rows (and their ancestors) so these tables always have matching parents in the TSVs.
- Added a fallback path in `fetch_rows`: when FK filters have no matching parent IDs yet, the exporter now logs a debug message and selects rows without the FK filter (still honoring the row limit). Those rows then trigger the parent backfill logic above, so we no longer skip populated tables just because their parents weren’t part of the initial sample.

## 2025-10-26 Phase 3 notes
- Added `genonaut/db/demo/seed_data_gen/import_seed_to_test.py`:
  - Reads TSV fixtures for each table, converts columns back to native Python types (UUID, JSON, Decimal, datetime, etc.), and inserts via `postgresql.insert(...).on_conflict_do_nothing` for idempotency.
  - Shares the same dependency ordering logic so parents load before children; optional `--truncate-first` truncates in reverse order to avoid FK issues.
  - `--verify` flag compares DB row counts vs TSV row counts (simple guardrail to detect short imports / FK violations) and logs warnings if mismatched.
  - Missing fixture files are skipped with info logging so partial imports are easy to orchestrate.
  - Automatically ensures the `alembic_version` table exists (populated with hash `672c99981361` by default, override via `--alembic-version`) so migrations remain in sync after fixture imports.
  - New `--table` flag (repeatable) joins the existing `--tables` option so we can import just a handful of TSVs (e.g., `--table user_notifications --table tag_ratings`) on top of an already-seeded database.

## 2025-10-26 Phase 4 notes
- Added Make targets + help entries:
  - `make export-demo-seed [ARGS="--tables users"]` runs the new exporter (defaults to demo DB + committed output dir).
  - `make import-demo-seed-to-test [ARGS="--truncate-first --verify"]` imports fixtures into the test DB.
  - `make refresh-test-seed-from-demo EXPORT_ARGS="..." IMPORT_ARGS="..."` chains both commands so we can update the TSV snapshot + immediately load it.

## 2025-10-27 Phase 6 notes
- Exporter now raises if a table contains rows in the source database but produced an empty TSV, preventing the "Skipping ... (0 rows)" scenario when data really exists.
- Added planning tasks to track a deeper investigation for `tag_ratings`, `user_notifications`, `user_search_history`, and `user_interactions` so we confirm their parents get sampled and their TSVs are populated.

### 2025-10-27 Phase 6 completion - FK filter retry logic
- Fixed the FK traversal issue that was causing `user_search_history` and other tables to fail export despite having data.
- Root cause: When child table rows referenced parent IDs outside the initial sample (e.g., search history for users not in first 100), the FK filter would match 0 rows and trigger an error instead of adapting.
- Solution: Modified `fetch_rows` to accept `skip_fk_filter` parameter, and updated `export_tables` to retry without FK constraints when a table has data but FK filter returns 0 rows.
- The retry logic triggers parent backfill via `ensure_parent_rows`, so child rows and their required parents are both exported.
- Verified successful export of all previously failing tables:
  - `user_search_history`: 13 rows exported with parent users backfilled
  - `user_interactions`: 2 rows exported
  - `recommendations`: 1 row exported
  - `user_notifications`: 1 row exported
  - `tag_ratings`: 3 rows exported
- All 17 tables with demo data now export correctly to TSV fixtures.

### 2025-10-27 Importer logging improvements
- Updated `import_seed_to_test.py` to provide accurate feedback about import operations:
  - `insert_rows()` now returns tuple `(inserted_count, skipped_count)` using SQLAlchemy's `result.rowcount`
  - Log messages distinguish between new inserts and skipped rows (already present due to PK conflicts)
  - Example outputs:
    - All new: `users: 104 new rows inserted`
    - All skipped: `users: 0 new rows inserted, 104 skipped (already present)`
    - Mixed: `users: 50 new rows inserted, 54 skipped (already present)`
- Eliminates confusion when running `make import-demo-seed-to-test` multiple times - now clearly shows 0 inserted vs 104 skipped instead of misleadingly claiming "Imported 104 rows" every time.

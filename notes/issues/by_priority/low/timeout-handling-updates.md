# Stability Hardening Add-Ons (beyond your current timeout plan)

> Extra defenses to prevent/diagnose hangs, ensure ^C works, and keep API responsive. These **do not** repeat items from your existing "Database Statement Timeout Implementation" doc.

---

## 1) Postgres-side guardrails
- **Idle/lock timeouts**
  - `idle_in_transaction_session_timeout = '30s'`
  - `lock_timeout = '5s'`
- **Visibility + diagnostics**
  - `log_min_duration_statement = 1000`  # 1s
  - `log_lock_waits = on`
  - `deadlock_timeout = '1s'`
  - Install `pg_stat_statements`; persist top queries dashboard.
    ```sql
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
    ```
- **Prevent long-lived TXs in app roles**
  ```sql
  ALTER ROLE genonaut_app IN DATABASE genonaut
    SET idle_in_transaction_session_timeout = '30s';
  ```

## 2) SQL/Schema performance helpers
- **Keyset pagination** on heavy list endpoints (avoid deep OFFSET).
- **Covering/partial indexes** only for hot filters (e.g., `WHERE user_id=? AND created_at>now()-interval '90 days'`).
- **Materialized view (nightly)** for expensive "unified" joins; `CONCURRENTLY` refresh in off-peak.
- **Avoid N+1**: prefetch tag joins via `ARRAY(SELECT ...)` or JSON aggregation in one query.

## 3) SQLAlchemy / engine resilience
- **Connection health**
  ```py
  engine = create_engine(
      url,
      pool_size=10, max_overflow=20,
      pool_pre_ping=True,          # drop dead conns
      pool_recycle=1800,           # avoid stale TCP
      connect_args={"options": "-c lock_timeout=5s -c idle_in_transaction_session_timeout=30s"}
  )
  ```
- **Per-call cancel token**
  - Run long queries in a worker thread and call `connection.cancel()` on timeout.
- **Retry only for safe cases** (e.g., `SerializationFailure`) with jittered backoff.

## 4) FastAPI/Starlette responsiveness
- **Client disconnect cancellation**
  ```py
  @router.get("/content/unified")
  async def unified(request: Request, db: Session = Depends(get_db)):
      async with anyio.create_task_group() as tg:
          tg.start_soon(cancel_on_disconnect, request, db)  # calls conn.cancel()
          return await build_response(db)
  ```
- **Ensure ^C works under reloader**
  - Prefer running **without** `--reload` in prod.
  - On dev start, register faulthandler explicitly so `SIGUSR1` dumps stacks even if you wrap uvicorn:
    ```py
    import faulthandler, signal; faulthandler.register(signal.SIGUSR1)
    ```
- **Request timeouts at ASGI layer**
  - Add middleware using `anyio.fail_after(15)` to bound handler time and bubble a 504.
- **Streaming + cleanup**
  - For stream responses, `try/finally: cursor.close(); session.close()` to avoid `idle in transaction`.

## 5) Uvicorn/Gunicorn/Nginx timeouts (defense in depth)
- Uvicorn: `--timeout-keep-alive 5` (shorter keep-alive reduces dangling clients).
- Gunicorn (if used): `--graceful-timeout 20 --timeout 30 --worker-tmp-dir /dev/shm`.
- Reverse proxy (nginx/traefik):
  - `proxy_read_timeout 30s; proxy_send_timeout 30s; keepalive_timeout 5s;`

## 6) Observability & tracing
- **Request IDs** (e.g., `X-Request-ID`) + structured JSON logs (endpoint, user_id, SQL ms, rows).
- **OpenTelemetry**: trace spans for HTTP handler -> DB query; export to Jaeger/OTLP.
- **Slow SQL logging**: log SQL with bind params when duration > 500ms (redact secrets).

## 7) Ops playbooks & safeguards
- **Kill playbook**: SQL to list/cancel long queries; shell to kill **process group** (reloader-safe).
- **Chaos test**: nightly job that runs a deliberately slow query; verify timeouts, logs, UI message.
- **Load test**: k6/Locust scenario focusing on `/content/unified` with tag filters.

## 8) Data hygiene
- **Autovacuum tuning** for hottest tables (lower `vacuum_scale_factor`, raise worker cost limit).
- **Bloat watch**: `pgstattuple` or `pg_bloat_check` job weekly; rebuild/REINDEX when thresholds hit.
- **Analyze cadence**: `ANALYZE` after large migrations/bulk updates to refresh stats.

---

## Deliverables checklist

### Phase 1: PostgreSQL Configuration
- [x] Set `idle_in_transaction_session_timeout = '30s'` at database level
- [x] Set `lock_timeout = '5s'` at database level
- [x] Set `log_min_duration_statement = 1000` (1 second)
- [x] Enable `log_lock_waits = on`
- [x] Set `deadlock_timeout = '1s'`
- [x] Install `pg_stat_statements` extension
- [x] Configure role-level timeout for `genonaut_rw` role (actual app role)
- [x] Verify all settings via SQL queries (`SHOW` commands)
- [x] Document PostgreSQL configuration in `docs/db.md`

### Phase 2: SQLAlchemy Engine Hardening
- [x] Add `pool_pre_ping=True` to engine configuration
- [x] Configure `pool_size=10` and `max_overflow=20`
- [x] Add `pool_recycle=1800` (30 minutes)
- [x] Update `connect_args` to include `lock_timeout` and `idle_in_transaction_session_timeout`
- [x] Read pool configuration from `base.json`
- [x] Add pool configuration validation
- [x] Write unit test for pool configuration
- [x] Write integration test to verify pool behavior and connection health

### Phase 3: Request Cancellation on Disconnect
- [ ] Research client disconnect detection in FastAPI/Starlette
- [ ] Create middleware or dependency to detect client disconnects
- [ ] Implement connection cancellation logic for active DB queries
- [ ] Test with long-running endpoint (e.g., `/content/unified`)
- [ ] Add logging for cancelled requests
- [ ] Write integration test simulating client disconnect
- [ ] Document disconnect handling in `docs/api.md`

### Phase 4: Request Timeout Middleware
- [ ] Create ASGI middleware using `anyio.fail_after()`
- [ ] Make timeout configurable via `base.json`
- [ ] Return 504 Gateway Timeout on middleware timeout
- [ ] Ensure middleware timeout > statement_timeout
- [ ] Add structured logging for middleware timeouts
- [ ] Write unit test for middleware
- [ ] Write integration test triggering middleware timeout
- [ ] Document middleware in `docs/api.md`

### Phase 5: Faulthandler for Debugging
- [x] Register faulthandler with `SIGUSR1` signal in application startup
- [x] Add configuration option to enable/disable faulthandler
- [ ] Test stack trace dumping with `kill -USR1 <pid>` @manual-testing
- [x] Document faulthandler usage in `docs/developer.md`
- [x] Add to developer playbook for debugging hangs

### Phase 6: Query Performance Monitoring
- [ ] Verify `pg_stat_statements` is collecting data @requires-postgres-config
- [x] Create SQL query to view top queries by total time
- [x] Create SQL query to view top queries by mean time
- [ ] Add endpoint or admin command to view query stats @future-work
- [ ] Add slow query logging (log queries > 500ms with bind params) @future-work
- [ ] Ensure secrets are redacted from logs @future-work
- [x] Document query monitoring in `docs/db.md`

### Phase 7: Schema & Query Optimization (Optional)
- [ ] Audit endpoints using OFFSET pagination
- [ ] Identify candidates for keyset pagination (e.g., gallery)
- [ ] Implement keyset pagination for high-traffic endpoints
- [ ] Review hot query filters and add covering indexes if needed
- [ ] Audit for N+1 queries in tag/content joins
- [ ] Consider materialized view for expensive unified queries (if needed)
- [ ] Document optimization decisions

### Phase 8: Reverse Proxy & ASGI Timeouts
- [ ] Document recommended uvicorn timeout settings
- [ ] Document recommended nginx/reverse proxy settings
- [ ] Align all timeout layers (nginx -> uvicorn -> middleware -> DB)
- [ ] Create timeout layer diagram
- [ ] Add to deployment documentation

### Phase 9: Observability & Tracing
- [ ] Add request ID middleware (X-Request-ID header)
- [ ] Include request ID in all structured logs
- [ ] Add SQL execution time to logs
- [ ] Add rows returned to logs
- [ ] Research OpenTelemetry integration (optional, future work)
- [ ] Document logging structure in `docs/developer.md`

### Phase 10: Testing & Validation
- [ ] Create chaos test script for deliberately slow queries
- [ ] Test that slow queries trigger timeouts at all layers
- [ ] Test that timeout errors appear in logs
- [ ] Test that frontend shows timeout notification
- [ ] Verify session cleanup after timeouts (no connection leaks)
- [ ] Load test `/content/unified` with tag filters
- [ ] Document test scenarios

### Phase 11: Operational Playbooks
- [ ] Create SQL playbook for listing long-running queries
- [ ] Create SQL playbook for cancelling queries
- [ ] Create shell playbook for killing hung processes
- [ ] Document how to identify and diagnose hangs
- [ ] Add troubleshooting section to `docs/developer.md`

### Phase 12: Data Hygiene (Optional, Lower Priority)
- [ ] Review autovacuum settings for hot tables
- [ ] Set up bloat monitoring (weekly check)
- [ ] Document ANALYZE cadence after bulk operations
- [ ] Add to database maintenance documentation

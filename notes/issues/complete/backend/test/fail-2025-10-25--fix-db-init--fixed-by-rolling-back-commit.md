# Preamble
I'd like you to find out for me why our tests are now taking so long to start.

I'm very confident that this is due to changes made in the last commit, if not the previous commit, else combined. I'd 
first look at what was changed in the last commit.

You can actually see details about what was committed here: notes/fail-2025-10-25.md.

That document is about two things: (1) fixing some failing tests, (2) fixing a root cause behind some failures. That 
root cause being that sometimes there wasn't sufficient data in the databases that were being tested against. Sometimes,
that could be the demo database, othertimes the test database, and test_init is its own sort of thing. I directed the 
agent to set up a hook in the setUp of tests, which should now run for the relevant backend tests as well as frontend 
e2e tests, which (i) checks if the database is sufficiently up to date to run the tests (mainly, there sould be data in
the relevant rows; a sufficient number of rows), and (ii) if not, set up those tables; seed some data.

However, I worry that the agent forgot to do part (i) of this. And additionally, I don't think that it did (ii) efficiently.

Or maybe it just added some bug which is causing things to freeze or take a long time.

The problem I'm having now is that when I run tests, it gets to just the start of the tests, and then the terminal that
is running the test seems to freeze. Normally, I can cancel a process. But in this case, when i hit Ctrl+C to do that,
it doesn't allow it. I think this is because it's waiting on another process call to finish, probably postgres, which
is probably in the middle of doing some seeding.

Indeed, I just did a test where I had 2 test suites running and hanging, and I just stopped the postgres service, and
when I did that, these processes stopped hanging and continued.

I think you should do a diff on the last commit and see if you can figure out what it is doing, and make a report in
notes/fail-2025-10-25--fix-db-init.md. In that report, write what you found in the "Reports" section. See if you can
figure out what it is doing, why it is taking so long, and propose some solutions to see how to make it more efficient.
It should not be taking such a long time. It should not be running the 'seed data' / 'synthetic data' generator. If 
anything it should just be populating with a small amount of rows for these tables. I have some ideas for how to do 
that, and I can tell you later about that. But for now just do your initial report. You should also look to see if it 
is doing part (i) "checks if the database is sufficiently up to date to run the tests".

You should also first read: docs/testing.md to get a good understanding of the test setup.

You should also look at these logs where I ran the tests. Where I have '...' is where the test froze for about 10 
minutes before i stopped postgres and then they continued on.

```
# make test
make test; beep
time make test; beep
Running quick tests (excluding long-running, manual, and performance tests)..
pytest test/ -v -m "not manual and not longrunning and not performance" --durations=0 --durations-min=0.5
============================= test session starts ==============================
platform darwin -- Python 3.11.10, pytest-8.4.2, pluggy-1.6.0 -- /Users/joeflack4/projects/genonaut/env/python_venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/joeflack4/projects/genonaut
configfile: pytest.ini
plugins: Faker-37.8.0, anyio-4.10.0
collecting 0 items                                                  collecting 0 items                                                  collecting 326 items                                                collecting 718 items                                                collected 1334 items / 61 deselected / 1273 selected

test/api/db/test_repositories.py::TestUserRepository::test_create_user
...
```

```
# make test long-running
time make test-long-running; beep
Running long-running tests (performance, stress, large datasets)...
⚠️  Warning: These tests may take 5-15 minutes to complete
Includes: comfyui_poll, comfyui_e2e, api_server, ontology_perf, and other longrunning tests
pytest test/ -v -m "longrunning"  --durations=0
...
```

# Reports

## 2025-10-26 Initial Investigation: DB init hook regressions

**What changed**
- Commit `66b7376` added a new pytest session hook plus the backend copy of `ensureTestDatabase()` so every backend run now executes `pytest_sessionstart` (test/conftest.py:198-252) followed immediately by the autouse `ensure_seeded_test_db` fixture (test/conftest.py:258-275).
- Frontend E2E helpers gained a likewise `ensureTestDatabase()` (frontend/tests/e2e/utils/realApiHelpers.ts:29-126) that shells out with `execSync` before each spec.

**Observed behavior**
1. The session-start hook truncates every table in `genonaut_test` on every pytest invocation. Because the alembic version table is preserved, we keep schema metadata but lose all rows, so any subsequent "is DB ready?" check always finds an empty database.
2. The backend ensure function only checks `Tag` count (test/db/test_utils/test_database_utils.py:31-88). After the forced truncate this count is always 0, so it immediately calls `seed_test_database()` which defers to `initialize_database(... environment="test", auto_seed=True)` (test/db/test_utils/test_database_utils.py:91-118).
3. When `initialize_database` sees `environment == "test"` it unconditionally drops all tables, runs the full Alembic migration history, and replays every TSV fixture (genonaut/db/init.py:905-1018). This is effectively `make init-test` at the start of every test run, which explains the 8-10 minute hang and why Ctrl+C appears stuck (Alembic and TSV imports ignore the signal until they finish).
4. On the frontend side each Playwright worker has its own Node process, so the module-level `databaseEnsured` flag does not prevent multiple workers from running the same `execSync` sequence in parallel. Those invocations also run `initialize_database`, so we end up with several concurrent schema resets that contend on Postgres locks and block any pytest session that is trying to start at the same time.
5. The frontend helper’s readiness check always hits `http://localhost:8001` even when the tests target the API on port 8002, so it can be looking at the wrong database entirely. Because it only asks `/api/v1/tags?page_size=1`, it does not prove that the rest of the seed data exists anyway, so requirement (i) ("verify sufficient data") is not really satisfied for either backend or frontend.

**Why startup now feels frozen**
- Every `pytest` or `npm run test:e2e` invocation now chains: truncate -> drop tables -> run Alembic -> materialize every TSV -> optionally run `psql` to add the admin user. On my machine that sequence takes several minutes; while it runs, pytest is still at "collecting 0 items ..." and SIGINT is swallowed by Alembic/subprocess until they finish.
- When backend and frontend tests run close together the concurrent `initialize_database` calls contend for global locks (e.g., dropping the same tables), so the later processes just sit waiting on Postgres; killing Postgres releases the lock, which matches what you observed.

**Initial recommendations / next steps**
- Stop calling `initialize_database` automatically from tests. Instead, run `make init-test` manually (or via CI setup) and only run a lightweight health check inside tests (e.g., `SELECT COUNT(*) FROM content_items`, `tags`, `users`).
- Remove or gate the `pytest_sessionstart` truncate hook; the rollback fixtures already isolate state for most tests, and we can keep an opt-in `RESET_TEST_DB=1` flag for the rare cases that need a hard reset.
- For frontend, reuse the existing `detectApiPort()` helper so readiness checks hit the same server the tests use, and replace the `execSync` seeding with a small API smoke check (or call into a fast "minimal seed" function instead of rerunning Alembic).
- If we still need automatic seeding, build a lightweight fixture loader that inserts a handful of rows directly instead of shelling out to the heavyweight `initialize_database` pipeline.

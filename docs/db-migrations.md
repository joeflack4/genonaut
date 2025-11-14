# DB migrations (Alembic)
**When to use:** Any schema or data change.  
**Principle:** Forward-only in prod; rollbacks are for local/dev.

## SOP: Changing database schema 
1) Create, modify, or delete SQLAlchemy models.
- DO NOT DO: plan/create raw SQL to execute to make the changes.
2) Create revision: Autogen (ORM): Run the makefile goals to do `alembic revision --autogenerate -m "xyz"` and 
`alembic upgrade head` either all DBs at once, or 1 DB at a time. The makefile commands follow the pattern, `migrate-*`,
e.g. `migrate-demo`, and there is a `migrate-all` command. There are some comments written directly above those 
commands;  Bgive them a read as well.
- DO NOT DO: Manual (SQL): `alembic revision -m "xyz"`
3) Optional (Probably for humans only; agents can skip this): Review and edit the new script under 
`alembic/versions/*.py` (write `downgrade()` only for safe, local use).
4CI/CD: run migrations during deploy (if applicable); use one DB per env.

### Special considerations
Always start by syncing with main, then run `PYTHONPATH=. alembic heads` (or `alembic history --verbose | tail`) to 
confirm there is exactly one head and note its revision id. If more than one head appears, stop and reconcile before 
creating anything new.

Make sure your target database is on that same head with `alembic current` (or `alembic current -n <name>` for each DSN 
you maintain). Upgrade or downgrade until everything reports the single head revision.

Generate new migrations with Alembic’s CLI (`alembic revision --autogenerate -m "<message>"`). The tool automatically 
sets`down_revision` to the sole current head. Avoid hand-copying the template unless you have to; if you do, paste the 
revision id you saw from `alembic heads` into the `down_revision` field instead of reusing an older value.

After the new file is created, re-run `alembic heads`. You should again see only one head (the new revision). If you see 
two, the `down_revision` was wrong—fix it before proceeding.

Run `alembic upgrade head` (against every environment you maintain: dev, demo, test, etc.) to verify the migration 
applies cleanly and leaves the `alembic_version` table at the new revision.

Only then run the rest of the test suite. Because each environment has been upgraded in lockstep, integration tests 
shouldn't trip over multiple heads or schema drift.

## Data migrations (safe patterns)
- Prefer **forward fixes** in prod; avoid `downgrade` there.  
- For drops: two-step — stop writes, (optional) archive data, then drop next release.  
- For non-null new columns: add with `server_default`, backfill, then remove default.  
- Archive strategy: copy to `archive_*` table or JSONB snapshot before destructive ops.

## Indexes without downtime (Postgres)
```python
from alembic import op
# Outside transaction:
with op.get_context().autocommit_block():
    op.create_index("ix_users_email", "users", ["email"], unique=True, postgresql_concurrently=True)
```

## Troubleshooting / Gotchas
- **Autogenerate is empty but I changed models**
  - Ensure `target_metadata = Base.metadata`.
  - Check your `__init__.py` imports so models are imported.
  - Use `compare_type=True` and `compare_server_default=True`.
- **Multiple heads error** (`alembic heads` shows >1)
  - Resolve: `alembic merge -m "merge heads" <head1> <head2>` then upgrade.
- **Bad autogen for exotic things (partial indexes, triggers)**
  - Write manual `op.execute(...)` SQL; add `depends_on=`/comments in script.
- **Long locks adding indexes**
  - Use `postgresql_concurrently=True` + `autocommit_block()` (see above).
- **Need to revert in prod**
  - Don't `downgrade`. Ship a new **forward** migration that restores old shape or data.
- **Type change on large table**
  - Create shadow column, backfill in batches, swap in a short transaction, drop old later.
- **"Target database is not up to date" or "database_url argument required" errors**
  - After config system refactor, `DATABASE_URL_DEMO` and `DATABASE_URL_TEST` are no longer defined in env files.
  - Database URLs are now constructed dynamically via `get_database_url(environment)` from `genonaut.db.utils`.
  - The Makefile migration commands have been updated to use Python's `get_database_url()` function.
  - Config precedence: config/base.json -> config/{ENV_TARGET}.json -> env/.env.shared -> env/.env.{ENV_TARGET} -> process env -> env/.env
  - If you see migration errors, ensure your Makefile uses: `DB_URL=$$(python -c "from genonaut.db.utils import get_database_url; print(get_database_url('demo'))")`
- **Migration fails with "constraint does not exist"**
  - Some migrations may try to drop constraints that don't exist in certain database states.
  - Fixed migrations use conditional logic: check if constraint exists before dropping with `sa.inspect(bind).get_unique_constraints()`.
  - For test database issues, consider: `make init-test` to recreate with latest schema, or manually drop/recreate the database.

## Examples
### Example: add a column

**Goal:** add `nickname TEXT` to `users` (non-null, default to empty), with clean backfill.

#### 1. Update model
```python
# myapp/models.py
class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True)
    email = sa.Column(sa.String, nullable=False, unique=True)
    nickname = sa.Column(sa.Text, nullable=False, server_default="")  # new
```

#### 2. Create migration
```
alembic revision --autogenerate -m "add users.nickname"
```

#### 3. Edit the generated script (if needed)
`alembic/versions/<rev>_add_users_nickname.py`:
```python
from alembic import op
import sqlalchemy as sa

revision = "abcd1234"
down_revision = "prevrev"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("nickname", sa.Text(), nullable=False, server_default=""))
    # optional: drop the default to avoid future implicit defaults
    op.alter_column("users", "nickname", server_default=None)

def downgrade():
    # local-only safety: this will drop data in nickname
    op.drop_column("users", "nickname")
```

**Variant: manual data backfill**  
Use this pattern if you want to fill the new column with values derived from existing data instead of a static default:

```python
def upgrade():
    op.add_column("users", sa.Column("nickname", sa.Text(), nullable=True))
    op.execute("UPDATE users SET nickname = split_part(email, '@', 1)")
    op.alter_column("users", "nickname", nullable=False)
```

#### 4. Apply
```
alembic upgrade head
```

#### 5. Commit
- **Commit:** model change(s), `alembic.ini`, `alembic/env.py`, the new file under `alembic/versions/`.  
- **Do NOT commit:** actual DB, secrets, local .env.


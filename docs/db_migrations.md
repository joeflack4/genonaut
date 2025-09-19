# DB migrations (Alembic)
**When to use:** Any schema or data change.  
**Principle:** Forward-only in prod; rollbacks are for local/dev.

## SOP: Changing database schema 
1) Create, modify, or delete SQLAlchemy models.
- DO NOT DO: plan/create raw SQL to execute to make the changes.
2) Create revision: Autogen (ORM): Run the makefile goals to do `alembic revision --autogenerate -m "xyz"` on respective
DBs, which follow the pattern, `migrate-*`, e.g. `migrate-demo`.
- DO NOT DO: Manual (SQL): `alembic revision -m "xyz"`
3) Optional (Probably for humans only; agents can skip this): Review and edit the new script under 
`alembic/versions/*.py` (write `downgrade()` only for safe, local use).  
4) Apply: Run the makefile goals to do `alembic upgrade head` on respective DBs, which follow the pattern, 
`migrate-step2-*`, e.g. `migrate-step2-demo`.    
5) CI/CD: run migrations during deploy (if applicable); use one DB per env.

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
  - Don’t `downgrade`. Ship a new **forward** migration that restores old shape or data.
- **Type change on large table**  
  - Create shadow column, backfill in batches, swap in a short transaction, drop old later.

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


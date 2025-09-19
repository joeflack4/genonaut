# Genonaut
Recommender systems &amp; perpetual generation for gen AI.

## Set up
### Installation
Prerequisites
  - Python 3.10+

Installation steps:
1. Create virtual environment  
2. `pip install -r requirements.txt`
3. Create Postgres DB
  - Create your `.env` file (see "Environment variables" below)
  - Run: `make init` or `python -m genonaut.db.init`

### Environment variables
Genonaut requires database configuration via environment variables. 

**Setup:**
1. Copy the example environment file: `cp env/env.example .env`
2. Edit `.env` with your actual database credentials.

**Required Variables:**

| Variable            | Description                                      | Example               | Default |
|---------------------|--------------------------------------------------|-----------------------|---------|
| `DB_PASSWORD_ADMIN` | Admin user password (full database privileges)   | `your_admin_password` | None    |
| `DB_PASSWORD_RW`    | Read/write user password (data operations only)  | `your_rw_password`    | None    |
| `DB_PASSWORD_RO`    | Read-only user password (select operations only) | `your_ro_password`    | None    |

**Optional Variables:**

| Variable       | Description                                                     | Example                                                          | Default     |
|----------------|-----------------------------------------------------------------|------------------------------------------------------------------|-------------|
| `DATABASE_URL` | Complete PostgreSQL connection URL (recommended for production) | `postgresql://genonaut_admin:admin_pass@localhost:5432/genonaut` | None        |
| `DB_HOST`      | Database host                                                   | `localhost`                                                      | `localhost` |
| `DB_PORT`      | Database port                                                   | `5432`                                                           | `5432`      |
| `DB_NAME`      | Database name                                                   | `genonaut`                                                       | `genonaut`  |
| `DB_NAME_DEMO` | Demo database name                                              | `genonaut_demo`                                                  | `genonaut_demo` |
| `DB_USER`      | Legacy database username                                        | `postgres`                                                       | `postgres`  |
| `DB_PASSWORD`  | Legacy database password                                        | `your_secure_password`                                           | None        |
| `DB_ECHO`      | Enable SQL query logging                                        | `true`                                                           | `false`     |
| `DEMO`         | When truthy, operate against the demo database                  | `1`                                                              | `0`         |

**Three-Tier User System:**
Genonaut uses a three-tier database user system for security:
- **Admin User** (`genonaut_admin`): Full privileges for database initialization, schema creation, and administration
- **Read/Write User** (`genonaut_rw`): Can insert, update, and delete data but cannot modify database structure
- **Read-Only User** (`genonaut_ro`): Can only read data, useful for reporting and analytics

**Configuration Behavior:**
- If `DATABASE_URL` is provided and not empty, it will be used directly
- Otherwise, the system will construct the database URL from the individual DB_* variables
- For initialization, admin credentials (`DB_PASSWORD_ADMIN`) are used by default
- For production, using `DATABASE_URL` with admin credentials is recommended for database setup

**Notes:**
- The `.env` file is gitignored and should never be committed

### Database Setup

After configuring environment variables, initialize the database:

```bash
make init          # main database
make init-demo     # demo database
```

This will create the necessary database tables and schema for Genonaut. Alembic
migrations can be applied via `make migrate-dev` and `make migrate-demo`.

Seed-data directories for the main and demo databases are configured in
`config.json` at the project root. Adjust those paths if you relocate the TSV
fixtures.

## Running
`python -m genonaut`

## Developer docs
Running tests:
`make test` or `pytest test/ -v` (`-v` optional, for verbosity) 

See more: [full dev docs](docs/developer.md))

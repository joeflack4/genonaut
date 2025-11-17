# Configuration Management

This document describes Genonaut's configuration system, which separates application configuration from deployment secrets and supports multiple deployment environments.

## Overview

Genonaut uses a two-tier configuration system:
- **JSON config files** - Non-sensitive application configuration (committed to git)
- **.env files** - Sensitive credentials and secrets (excluded from git)

## Directory Structure

```
config/
  base.json                # Shared config across all environments
  local-dev.json           # Local development environment
  local-demo.json          # Local demo environment
  local-test.json          # Local test environment
  cloud-dev.json           # Cloud development environment
  cloud-demo.json          # Cloud demo environment
  cloud-test.json          # Cloud test environment
  cloud-prod.json          # Cloud production environment

env/
  .env.shared              # Shared secrets (passwords, API keys)
  .env.local-dev           # Dev-specific secrets
  .env.local-demo          # Demo-specific secrets
  .env.local-test          # Test-specific secrets
  .env.cloud-dev           # Cloud dev secrets
  .env.cloud-demo          # Cloud demo secrets
  .env.cloud-test          # Cloud test secrets
  .env.cloud-prod          # Cloud prod secrets
  .env                     # Optional: developer overrides (gitignored)
  env.shared.example       # Template for .env.shared
  env.location-type.example # Template for environment-specific files
```

Frontend-specific configuration (for example, UI timeouts or feature toggles) now lives under `frontend/src/config/`. Use the root-level `config/` directory only for backend settings.

## Configuration Load Order

Settings are loaded with the following precedence (lowest to highest):

1. `config/base.json` - Base application config
2. `config/{ENV_TARGET}.json` - Environment-specific config
3. `env/.env.shared` - Shared secrets
4. `env/.env.{ENV_TARGET}` - Environment-specific secrets
5. Process environment variables - CI/shell exports
6. `env/.env` - Local developer overrides (optional)

**Later sources override earlier sources.**

## Environment Targets

The `ENV_TARGET` variable specifies which environment you're running. Format: `{location}-{type}`

### Available Environments

**Local Environments:**
- `local-dev` - Local development
- `local-demo` - Local demo database
- `local-test` - Local test database

**Cloud Environments:**
- `cloud-dev` - Cloud development
- `cloud-demo` - Cloud demo/staging
- `cloud-test` - Cloud testing
- `cloud-prod` - Cloud production

### Environment Type Extraction

The system can extract the environment type from ENV_TARGET:
- `local-dev` → type is `dev`
- `cloud-prod` → type is `prod`

This is used for backward compatibility with code that needs to know if it's running in dev/demo/test/prod.

## Which Variables Go Where?

### Config Files (config/*.json)

**Use JSON config files for:**
- Database connection parameters (host, port, name, user)
- API server settings (host, port, debug mode)
- Service URLs (Redis, ComfyUI)
- Feature flags and defaults
- File paths and directories
- Any non-sensitive configuration

**Example:**
```json
{
  "db-host": "localhost",
  "db-port": 5432,
  "db-name": "genonaut_dev",
  "api-port": 8001,
  "redis-ns": "genonaut_dev"
}
```

### Environment Files (env/.env.*)

**Use .env files for:**
- Passwords and credentials
- API keys and tokens
- Secrets and sensitive data
- Database URLs with embedded passwords

**Example:**
```bash
# Shared secrets
DB_PASSWORD_ADMIN=your_password_here
API_SECRET_KEY=your_secret_key

# Environment-specific
REDIS_URL=redis://localhost:6379/4
CELERY_BROKER_URL=redis://localhost:6379/4
```

## Naming Conventions

### Config File Keys (kebab-case)
```json
{
  "db-host": "localhost",
  "api-port": 8001,
  "redis-ns": "genonaut_dev"
}
```

### Environment Variable Keys (UPPER_SNAKE_CASE)
```bash
DB_HOST=localhost
API_PORT=8001
REDIS_NS=genonaut_dev
```

### Environment Variable Overrides

Environment variables can override config values using case-insensitive matching with underscores converted to dashes:

- `DB_HOST` overrides `db-host`
- `API_PORT` overrides `api-port`
- `REDIS_NS` overrides `redis-ns`

## Database Statement Timeout

The API enforces a PostgreSQL `statement_timeout` on every connection to prevent runaway queries from blocking the system.

- **Config key:** `statement-timeout` (kebab-case in JSON, exposed as `statement_timeout` in Python configuration)
- **Format:** integer value followed by a unit (`ms`, `s`, or `min`). Examples: `"500ms"`, `"15s"`, `"2min"`.
- **Defaults:**
  - Development/test environments (`config/base.json`): `"15s"`
  - Production (`config/cloud-prod.json`): `"30s"`

Update the value in the appropriate `config/*.json` file to tune the timeout for your environment. No database restart is required—restart the API service and new connections will pick up the change automatically.

> **Tip:** When testing timeout handling end-to-end, temporarily lower the value in your local config (e.g., `"1s"`) and run a deliberately slow query (`SELECT pg_sleep(2)`).

## Running Services

### Using Make Targets

```bash
# Local environments
make api-dev          # Start dev API
make api-demo         # Start demo API
make api-test         # Start test API

# Cloud environments (when ready)
make api-cloud-prod   # Start production API

# With workers
make api-dev-load-test  # Dev with 4 workers
```

### Using CLI Directly

```bash
# Using env-target shortcut
python -m genonaut.cli_main run-api --env-target local-dev

# With explicit paths
python -m genonaut.cli_main run-api \
  --env-path env/.env.local-dev \
  --config-path config/local-dev.json

# With workers
python -m genonaut.cli_main run-api \
  --env-target local-dev \
  --workers 4 \
  --no-reload
```

### Database Initialization

```bash
# Using Make
make init-dev
make init-demo
make init-test

# Using CLI
python -m genonaut.cli_main init-db --env-target local-dev
python -m genonaut.cli_main init-db --env-target local-demo --drop-existing
```

## Adding a New Environment

To add a new environment (e.g., `cloud-staging`):

1. **Create config file:** `config/cloud-staging.json`
   ```json
   {
     "db-host": "staging.db.example.com",
     "db-port": 5432,
     "db-name": "genonaut_staging",
     "api-port": 8001
   }
   ```

2. **Create env file:** `env/.env.cloud-staging`
   ```bash
   REDIS_URL=redis://staging.redis.example.com:6379/0
   CELERY_BROKER_URL=redis://staging.redis.example.com:6379/0
   ```

3. **Add Makefile targets:**
   ```makefile
   api-cloud-staging:
       @echo "Starting API server for cloud-staging..."
       python -m genonaut.cli_main run-api --env-target cloud-staging
   ```

4. **Update shared secrets if needed** in `env/.env.shared`

## Environment Variable Construction

Some variables are constructed programmatically:

### DATABASE_URL
Automatically constructed from components:
```python
# From config:
db-host, db-port, db-name, db-user-admin

# From env:
DB_PASSWORD_ADMIN

# Result:
DATABASE_URL=postgresql://user:password@host:port/name
```

This ensures passwords are never in config files.

## Developer Overrides

Create `env/.env` (gitignored) for local overrides:

```bash
# Override any setting for local development
DB_PORT=5433  # Use different port
API_DEBUG=true  # Enable debug mode
```

This file has highest precedence and won't be committed to git.

## Troubleshooting

### Check which config is loaded
```bash
python -m genonaut.cli_main run-api --env-target local-dev
# Output shows:
#   ENV_TARGET: local-dev
#   Config: config/local-dev.json
#   Env file: env/.env.local-dev
```

### Missing config file
```
Error: Environment config not found: config/local-dev.json
```
**Solution:** Ensure the config file exists for your ENV_TARGET

### Missing password
```
ValueError: DB_PASSWORD_ADMIN environment variable is required
```
**Solution:** Set DB_PASSWORD_ADMIN in env/.env.shared or env/.env.{ENV_TARGET}

### Wrong database connection
Check that:
1. ENV_TARGET is correct
2. Config file has correct db-host, db-port, db-name
3. .env file has correct DB_PASSWORD_ADMIN

## Migration from Old System

The old system used `APP_ENV` with values: `dev`, `demo`, `test`

**Old way:**
```bash
APP_ENV=dev make api-dev
```

**New way:**
```bash
make api-dev  # Uses ENV_TARGET=local-dev internally
# or
python -m genonaut.cli_main run-api --env-target local-dev
```

All `APP_ENV` references have been replaced with `ENV_TARGET`.

## Security Best Practices

1. **Never commit secrets** to config files
2. **Use .env files** for all passwords and keys
3. **Keep .env.shared** with dummy values in git
4. **Use .env** (gitignored) for real local credentials
5. **Rotate secrets** when adding new team members
6. **Use environment-specific** secrets in CI/CD

## Frontend UI Configuration

Frontend-specific UI settings are configured in `frontend/src/config/ui.ts`.

### Notification/Toast/Snackbar Settings

Controls the appearance and behavior of notifications throughout the application:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `NOTIFICATIONS.AUTO_HIDE_DURATION.error` | `number \| null` | `null` | Auto-hide duration for error notifications in milliseconds. `null` = stays until dismissed |
| `NOTIFICATIONS.AUTO_HIDE_DURATION.warning` | `number \| null` | `8000` | Auto-hide duration for warning notifications (8 seconds) |
| `NOTIFICATIONS.AUTO_HIDE_DURATION.info` | `number \| null` | `6000` | Auto-hide duration for info notifications (6 seconds) |
| `NOTIFICATIONS.AUTO_HIDE_DURATION.success` | `number \| null` | `4000` | Auto-hide duration for success notifications (4 seconds) |
| `NOTIFICATIONS.DISABLE_AUTO_HIDE` | `boolean` | `false` | If `true`, all notifications stay on screen until manually dismissed, overriding individual duration settings |
| `NOTIFICATIONS.POSITION.vertical` | `'top' \| 'bottom'` | `'bottom'` | Vertical position of notifications |
| `NOTIFICATIONS.POSITION.horizontal` | `'left' \| 'center' \| 'right'` | `'left'` | Horizontal position of notifications |

**Example:**

To make all notifications auto-hide after 5 seconds:

```typescript
// frontend/src/config/ui.ts
export const UI_CONFIG = {
  NOTIFICATIONS: {
    AUTO_HIDE_DURATION: {
      error: 5000,
      warning: 5000,
      info: 5000,
      success: 5000,
    },
    DISABLE_AUTO_HIDE: false,
    // ...
  },
}
```

To disable auto-hide globally:

```typescript
export const UI_CONFIG = {
  NOTIFICATIONS: {
    // ...
    DISABLE_AUTO_HIDE: true,
  },
}
```

**Component Override:**

Individual components can override these defaults by passing props:

```tsx
<TimeoutNotification
  severity="warning"
  autoHideDuration={10000}  // Override to 10 seconds
  position={{ vertical: 'top', horizontal: 'right' }}
/>
```

### Other UI Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `GENERATION_TIMEOUT_WARNING_MS` | `number` | `60000` | Time before showing "request taking longer than expected" warning during image generation (60 seconds) |
| `MIN_SUBMIT_DURATION_MS` | `number` | `300` | Minimum duration to show submission state to prevent UI flashing on fast requests |
| `SEARCH_HISTORY_DROPDOWN_LIMIT` | `number` | `5` | Maximum number of recent search history items to display in dropdown widgets |

## Frontend Feature Configuration

Frontend feature flags and settings are configured in `frontend/src/config/features.ts`.

### Pagination Settings

Controls the pagination strategy used in the gallery and other list views:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `PAGINATION.USE_CURSOR_PAGINATION` | `boolean` | `false` | Use cursor-based vs offset-based pagination. `false` = simple offset-based (reliable), `true` = cursor-based (better for large datasets) |
| `PAGINATION.DEFAULT_PAGE_SIZE` | `number` | `50` | Default number of items per page |
| `PAGINATION.MAX_PAGE_SIZE` | `number` | `100` | Maximum allowed page size |

**Pagination Modes:**
- **Offset-based (default)**: Simple, reliable pagination using `page` and `page_size` parameters. Best for datasets < 10,000 items.
- **Cursor-based**: Performance-optimized pagination using opaque cursor tokens. Better for very large datasets but more complex.

**Example:**

To enable cursor-based pagination:

```typescript
// frontend/src/config/features.ts
export const FEATURES_CONFIG = {
  PAGINATION: {
    USE_CURSOR_PAGINATION: true,  // Enable cursor mode
    DEFAULT_PAGE_SIZE: 50,
    MAX_PAGE_SIZE: 100,
  },
}
```

**Backend Support:**

The backend automatically detects which pagination mode to use based on the parameters sent:
- If `cursor` parameter is provided → Uses cursor-based pagination
- If only `page` parameter is provided → Uses offset-based pagination

No backend configuration is needed; it adapts to the frontend's choice.

### Virtual Scrolling Settings

Controls virtual scrolling behavior in galleries:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `VIRTUAL_SCROLLING.ENABLED` | `boolean` | `false` | Enable virtual scrolling for large galleries |
| `VIRTUAL_SCROLLING.PAGE_SIZE` | `number` | `200` | Page size when virtual scrolling is enabled |

## See Also

- [Database Documentation](./db.md)
- [Testing Documentation](./testing.md)
- [API Documentation](./api.md)

# Database Documentation

Genonaut uses PostgreSQL with a multi-database architecture supporting development, demo, and test environments.

## Database Architecture

### Multi-Database Environment Support

| Environment | Database Name | Purpose | Access Pattern |
|-------------|---------------|---------|----------------|
| **Development** | `genonaut` | Main development database | Default for local development |
| **Demo** | `genonaut_demo` | Demo data and testing | Stable demo environment |
| **Test** | `genonaut_test` | Automated testing | Isolated test environment |

### Three-Tier User System

Genonaut uses a three-tier database user system for security:

- **Admin User** (`genonaut_admin`): Full privileges for database initialization, schema creation, and administration
- **Read/Write User** (`genonaut_rw`): Can insert, update, and delete data but cannot modify database structure
- **Read-Only User** (`genonaut_ro`): Can only read data, useful for reporting and analytics

## Environment Variables

### Required Variables

| Variable            | Description                                      | Example               | Default |
|---------------------|--------------------------------------------------|-----------------------|---------|
| `DB_PASSWORD_ADMIN` | Admin user password (full database privileges)   | `your_admin_password` | None    |
| `DB_PASSWORD_RW`    | Read/write user password (data operations only)  | `your_rw_password`    | None    |
| `DB_PASSWORD_RO`    | Read-only user password (select operations only) | `your_ro_password`    | None    |

### Optional Variables

| Variable       | Description                                                     | Example                                                          | Default     |
|----------------|-----------------------------------------------------------------|------------------------------------------------------------------|-------------|
| `DATABASE_URL` | Complete PostgreSQL connection URL (recommended for production) | `postgresql://genonaut_admin:admin_pass@localhost:5432/genonaut` | None        |
| `DATABASE_URL_TEST` | Dedicated connection string for the test database        | `postgresql://genonaut_admin:admin@localhost:5432/genonaut_test` | None        |
| `DATABASE_URL_DEMO` | Demo database connection URL                     | `postgresql://user:pass@localhost:5432/genonaut_demo` | Uses `DATABASE_URL` with demo DB name |
| `DB_HOST`      | Database host                                                   | `localhost`                                                      | `localhost` |
| `DB_PORT`      | Database port                                                   | `5432`                                                           | `5432`      |
| `DB_NAME`      | Database name                                                   | `genonaut`                                                       | `genonaut`  |
| `DB_NAME_DEMO` | Demo database name                                              | `genonaut_demo`                                                  | `genonaut_demo` |
| `DB_NAME_TEST` | Test database name                                              | `genonaut_test`                                                  | `genonaut_test` |
| `DB_USER`      | Legacy database username                                        | `postgres`                                                       | `postgres`  |
| `DB_PASSWORD`  | Legacy database password                                        | `your_secure_password`                                           | None        |
| `DB_ECHO`      | Enable SQL query logging                                        | `true`                                                           | `false`     |
| `DEMO`         | When truthy, operate against the demo database                  | `1`                                                              | `0`         |
| `GENONAUT_DB_ENVIRONMENT` | Force init/migration helpers to target a specific database (`dev`/`demo`/`test`) | `test` | None |

### Configuration Behavior

- If `DATABASE_URL` is provided and not empty, it will be used directly
- Otherwise, the system will construct the database URL from the individual DB_* variables
- For initialization, admin credentials (`DB_PASSWORD_ADMIN`) are used by default
- For production, using `DATABASE_URL` with admin credentials is recommended for database setup
- When `GENONAUT_DB_ENVIRONMENT=test` (or `API_ENVIRONMENT=test`) the helpers route all initialization and session management to the dedicated test database.
- If `DATABASE_URL_TEST` is absent, the tooling clones `DATABASE_URL`/`DB_NAME` and swaps in `DB_NAME_TEST` so the test environment stays isolated.

**Notes:**
- The `.env` file is gitignored and should never be committed
- Use a dedicated Postgres database/schema for the test environment (do not reuse the demo instance) to avoid destructive resets.

## Database Setup

### Initial Setup

After configuring environment variables, initialize the database:

```bash
make init          # main database
make init-demo     # demo database
make init-test     # test database (truncates & re-seeds with demo fixtures)
```

This will create the necessary database tables and schema for Genonaut.

### Migration Management

Alembic migrations can be applied via:

```bash
make migrate-dev        # Generate migration for dev database
make migrate-demo       # Generate migration for demo database
make migrate-test       # Generate migration for test database

make migrate-step2-dev  # Apply migrations to dev database
make migrate-step2-demo # Apply migrations to demo database
make migrate-step2-test # Apply migrations to test database
```

### Seed Data

Seed-data directories for the main and demo databases are configured in `config.json` at the project root. Adjust those paths if you relocate the TSV fixtures.

## Database Schema

### Core Tables

**Users Table (`users`):**
- `id` (Primary Key): Unique user identifier
- `username`: Unique username for the user
- `email`: User's email address (unique)
- `is_active`: Whether the user account is active
- `preferences`: JSONB column for flexible user preferences
- `created_at`: Timestamp when user was created
- `updated_at`: Timestamp when user was last updated

**Content Items Table (`content_items`):**
- `id` (Primary Key): Unique content identifier
- `title`: Content title
- `content_type`: Type of content (text, image, video, audio)
- `content_data`: The actual content data
- `creator_id` (Foreign Key): Reference to the user who created this content
- `item_metadata`: JSONB column for flexible metadata storage
- `tags`: Array of tags associated with the content
- `quality_score`: Quality score for the content (0.0 to 1.0)
- `is_public`: Whether the content is publicly visible
- `is_private`: Whether the content is private
- `created_at`: Timestamp when content was created
- `updated_at`: Timestamp when content was last updated

**User Interactions Table (`user_interactions`):**
- `id` (Primary Key): Unique interaction identifier
- `user_id` (Foreign Key): Reference to the user
- `content_item_id` (Foreign Key): Reference to the content item
- `interaction_type`: Type of interaction (view, like, share, comment, download)
- `rating`: Optional rating (1-5 scale)
- `duration`: Duration of interaction in seconds
- `metadata`: JSONB column for additional interaction data
- `created_at`: Timestamp when interaction occurred

**Recommendations Table (`recommendations`):**
- `id` (Primary Key): Unique recommendation identifier
- `user_id` (Foreign Key): Reference to the user
- `content_item_id` (Foreign Key): Reference to the recommended content
- `recommendation_score`: Score indicating recommendation strength (0.0 to 1.0)
- `algorithm_version`: Version of the recommendation algorithm used
- `metadata`: JSONB column for algorithm-specific data
- `served_at`: Timestamp when recommendation was served to user (nullable)
- `created_at`: Timestamp when recommendation was created

**Generation Jobs Table (`generation_jobs`):**
- `id` (Primary Key): Unique job identifier
- `user_id` (Foreign Key): Reference to the user who requested generation
- `job_type`: Type of generation job (text_generation, image_generation, etc.)
- `status`: Current job status (pending, running, completed, failed)
- `prompt`: Input prompt for generation
- `parameters`: JSONB column for generation parameters
- `result`: Generated content result
- `error_message`: Error message if job failed
- `created_at`: Timestamp when job was created
- `updated_at`: Timestamp when job was last updated
- `started_at`: Timestamp when job processing started
- `completed_at`: Timestamp when job completed

### Database Indexes

Key indexes for performance:

**Users:**
- `ix_users_username` (unique)
- `ix_users_email` (unique)
- `ix_users_is_active`

**Content Items:**
- `ix_content_items_creator_id`
- `ix_content_items_content_type`
- `ix_content_items_is_public`
- `ix_content_items_created_at`
- `ix_content_items_quality_score`

**User Interactions:**
- `ix_user_interactions_user_id`
- `ix_user_interactions_content_item_id`
- `ix_user_interactions_interaction_type`
- `ix_user_interactions_created_at`

**Recommendations:**
- `ix_recommendations_user_id`
- `ix_recommendations_content_item_id`
- `ix_recommendations_served_at`
- `ix_recommendations_recommendation_score`

**Generation Jobs:**
- `ix_generation_jobs_user_id`
- `ix_generation_jobs_status`
- `ix_generation_jobs_job_type`
- `ix_generation_jobs_created_at`

## JSONB Usage

Genonaut makes extensive use of PostgreSQL's JSONB columns for flexible data storage:

### User Preferences
```python
# Example user preferences JSONB structure
{
    "theme": "dark",
    "notifications": True,
    "language": "en",
    "content_types": ["text", "image"],
    "categories": ["technology", "science"]
}
```

### Content Metadata
```python
# Example content metadata JSONB structure
{
    "category": "technology",
    "keywords": ["python", "fastapi", "database"],
    "difficulty": "intermediate",
    "estimated_reading_time": 5,
    "author_notes": "Updated for 2024"
}
```

### Interaction Metadata
```python
# Example interaction metadata JSONB structure
{
    "source": "mobile_app",
    "device_type": "smartphone",
    "location": "home_page",
    "referrer": "search_results",
    "session_id": "abc123"
}
```

### Recommendation Metadata
```python
# Example recommendation metadata JSONB structure
{
    "algorithm": "collaborative_filtering",
    "confidence": 0.85,
    "reasons": ["similar_users", "content_similarity"],
    "fallback_used": False,
    "computation_time_ms": 45
}
```

## Database Operations

### Common Query Patterns

**Querying JSONB columns:**
```sql
-- Find users with specific preferences
SELECT * FROM users WHERE preferences->>'theme' = 'dark';

-- Find content with specific metadata
SELECT * FROM content_items WHERE item_metadata @> '{"category": "technology"}';

-- Find interactions from mobile devices
SELECT * FROM user_interactions WHERE metadata->>'device_type' = 'smartphone';
```

**Advanced JSONB operations:**
```sql
-- Update nested JSONB values
UPDATE users SET preferences = jsonb_set(preferences, '{notifications}', 'false') WHERE id = 1;

-- Query array elements in JSONB
SELECT * FROM content_items WHERE item_metadata->'keywords' ? 'python';

-- Aggregate JSONB data
SELECT metadata->>'source', COUNT(*) FROM user_interactions GROUP BY metadata->>'source';
```

### Performance Considerations

**JSONB Indexing:**
```sql
-- Create GIN index for JSONB columns (already included in migrations)
CREATE INDEX CONCURRENTLY ix_users_preferences_gin ON users USING gin(preferences);
CREATE INDEX CONCURRENTLY ix_content_metadata_gin ON content_items USING gin(item_metadata);
```

**Query Optimization:**
- Use `@>` operator for containment queries on JSONB
- Use `->` for accessing JSONB keys, `->>` for text values
- Consider partial indexes for frequently queried JSONB properties
- Use `jsonb_path_query` for complex path expressions

## Backup and Recovery

### Database Backup
```bash
# Full database backup
pg_dump -h localhost -U genonaut_admin genonaut > backup_$(date +%Y%m%d_%H%M%S).sql

# Schema-only backup
pg_dump -h localhost -U genonaut_admin --schema-only genonaut > schema_backup.sql

# Data-only backup
pg_dump -h localhost -U genonaut_admin --data-only genonaut > data_backup.sql
```

### Database Restore
```bash
# Restore full database
psql -h localhost -U genonaut_admin genonaut < backup_20241201_120000.sql

# Restore schema only
psql -h localhost -U genonaut_admin genonaut < schema_backup.sql

# Restore data only
psql -h localhost -U genonaut_admin genonaut < data_backup.sql
```

## Monitoring and Maintenance

### Performance Monitoring
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('genonaut'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Database Health Checks
```sql
-- Check for bloat
SELECT 
    schemaname,
    tablename,
    n_dead_tup,
    n_live_tup,
    round(n_dead_tup::float / (n_live_tup + n_dead_tup) * 100, 2) as bloat_percentage
FROM pg_stat_user_tables
WHERE n_live_tup > 0
ORDER BY bloat_percentage DESC;

-- Check connection counts
SELECT 
    state,
    count(*)
FROM pg_stat_activity
WHERE datname = 'genonaut'
GROUP BY state;
```

## Troubleshooting

### Common Issues

**Connection Issues:**
```bash
# Test database connection
psql -h localhost -U genonaut_admin -d genonaut -c "SELECT version();"

# Check if database exists
psql -h localhost -U postgres -l | grep genonaut
```

**Migration Issues:**
```bash
# Check current migration status
alembic current

# Show migration history
alembic history

# Stamp database with current migration (if out of sync)
alembic stamp head
```

**Performance Issues:**
```sql
-- Find slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    stddev_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Analyze table statistics
ANALYZE;

-- Update table statistics
VACUUM ANALYZE;
```

For more detailed migration procedures and troubleshooting, see [Database Migrations](./db_migrations.md).
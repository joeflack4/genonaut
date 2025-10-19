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

| Variable                  | Description                                                     | Example                                                          | Default     |
|---------------------------|-----------------------------------------------------------------|------------------------------------------------------------------|-------------|
| `DATABASE_URL`            | Complete PostgreSQL connection URL (recommended for production) | `postgresql://genonaut_admin:admin_pass@localhost:5432/genonaut` | None        |
| `DATABASE_URL_TEST`       | Dedicated connection string for the test database        | `postgresql://genonaut_admin:admin@localhost:5432/genonaut_test` | None        |
| `DATABASE_URL_DEMO`       | Demo database connection URL                     | `postgresql://user:pass@localhost:5432/genonaut_demo` | Uses `DATABASE_URL` with demo DB name |
| `DB_HOST`                 | Database host                                                   | `localhost`                                                      | `localhost` |
| `DB_PORT`                 | Database port                                                   | `5432`                                                           | `5432`      |
| `DB_NAME`                 | Database name                                                   | `genonaut`                                                       | `genonaut`  |
| `DB_NAME_DEMO`            | Demo database name                                              | `genonaut_demo`                                                  | `genonaut_demo` |
| `DB_NAME_TEST`            | Test database name                                              | `genonaut_test`                                                  | `genonaut_test` |
| `DB_USER_FOR_INIT`        | Legacy database username                                        | `postgres`                                                       | `postgres`  |
| `DB_PASSWORD_FOR_INIT`    | Legacy database password                                        | `your_secure_password`                                           | None        |
| `DB_ECHO`                 | Enable SQL query logging                                        | `true`                                                           | `false`     |
| `DEMO`                    | When truthy, operate against the demo database                  | `1`                                                              | `0`         |
| `GENONAUT_DB_ENVIRONMENT` | Force init/migration helpers to target a specific database (`dev`/`demo`/`test`) | `test` | None |

### Configuration Behavior

- If `DATABASE_URL` is provided and not empty, it will be used directly
- Otherwise, the system will construct the database URL from the individual DB_* variables
- For initialization, admin credentials (`DB_PASSWORD_ADMIN`) are used by default
- For production, using `DATABASE_URL` with admin credentials is recommended for database setup
- When `GENONAUT_DB_ENVIRONMENT=test` (or `APP_ENV=test`) the helpers route all initialization and session management to the dedicated test database.
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

**Automated Content Items Table (`content_items_auto`):**
- Mirrors the schema of `content_items` to support system-generated content
- Includes the same columns (`title`, `content_type`, `content_data`, `item_metadata`, `tags`, `quality_score`, `is_public`, `is_private`, timestamps)
- Maintains a foreign key to `users.id` for attribution
- Adds a dedicated full-text search index (`cia_title_fts_idx`) for PostgreSQL deployments
- Exposed through the `/api/v1/content-auto` REST endpoints for CRUD, search, analytics, and statistics

**Partitioned Parent Table (`content_items_all`):**
- PostgreSQL partitioned parent table combining `content_items` and `content_items_auto`
- Partitioned by `source_type` column: `'items'` (regular) or `'auto'` (auto-generated)
- **Benefits**:
  - Eliminates manual UNION queries for unified content access
  - Enables PostgreSQL partition pruning when filtering by `source_type`
  - MergeAppend optimization for sorted queries across partitions
  - Simplifies cursor pagination (single table instead of multi-table encoding)
- **Performance**: Sub-millisecond query times with partition pruning (< 0.2ms for single partition, < 0.4ms for both)
- **Usage**: Query `content_items_all` for unified content; INSERT/UPDATE/DELETE automatically routes to correct partition
- **Indexes**: Per-partition keyset pagination indexes (`idx_content_items_created_id_desc`, `idx_content_items_auto_created_id_desc`)
- **Implementation**: Phase 11 performance optimization (see `notes/perf-updates-2025-10-17.md`)

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

**Tags Table (`tags`):**
- `id` (Primary Key, UUID): Unique tag identifier
- `name` (Unique): Tag name/label (max 255 characters)
- `tag_metadata`: JSONB column for additional tag metadata
- `created_at`: Timestamp when tag was created
- `updated_at`: Timestamp when tag was last updated

**Tag Parents Table (`tag_parents`):**
- Composite Primary Key: (`tag_id`, `parent_id`)
- `tag_id` (Foreign Key): Reference to the child tag (CASCADE delete)
- `parent_id` (Foreign Key): Reference to the parent tag (CASCADE delete)
- Supports polyhierarchical relationships (tags can have multiple parents)

**Tag Ratings Table (`tag_ratings`):**
- `id` (Primary Key): Unique rating identifier
- `user_id` (Foreign Key): Reference to the user who rated the tag
- `tag_id` (Foreign Key): Reference to the rated tag
- `rating`: Rating value (1.0 to 5.0, allows half-star increments)
- `created_at`: Timestamp when rating was created
- `updated_at`: Timestamp when rating was last updated
- Unique constraint on (user_id, tag_id) - each user can rate a tag only once

### Database Indexes

Genonaut uses a comprehensive indexing strategy optimized for both general queries and high-performance pagination scenarios.

#### Core Indexes

**Users:**
- `ix_users_username` (unique) - User authentication and lookup
- `ix_users_email` (unique) - User authentication and profile access
- `ix_users_is_active` - Filter active/inactive users

#### Pagination-Optimized Indexes

The database includes specialized composite indexes designed to support efficient pagination across millions of rows:

**Content Items (content_items):**
- `ix_content_items_creator_id` - Basic creator queries
- `ix_content_items_content_type` - Filter by content type
- `ix_content_items_is_public` - Public/private content filtering
- `ix_content_items_created_at` - Basic temporal ordering
- `ix_content_items_quality_score` - Quality-based sorting

**Pagination-Optimized Composite Indexes:**
- `idx_content_items_creator_created` - (creator_id, created_at DESC) - Creator-specific pagination
- `idx_content_items_quality_created` - (quality_score DESC NULLS LAST, created_at DESC) - Quality-sorted pagination
- `idx_content_items_type_created` - (content_type, created_at DESC) - Type-filtered pagination
- `idx_content_items_public_created` - (created_at DESC) WHERE is_private = false - Public content optimization

**Content Items Auto (content_items_auto):**
- Mirror indexes of content_items for system-generated content
- `idx_content_items_auto_creator_created` - (creator_id, created_at DESC)
- `idx_content_items_auto_quality_created` - (quality_score DESC NULLS LAST, created_at DESC)
- `idx_content_items_auto_type_created` - (content_type, created_at DESC)
- `idx_content_items_auto_public_created` - (created_at DESC) WHERE is_private = false

**User Interactions:**
- `ix_user_interactions_user_id` - User-specific queries
- `ix_user_interactions_content_item_id` - Content-specific queries
- `ix_user_interactions_interaction_type` - Filter by interaction type
- `ix_user_interactions_created_at` - Temporal queries
- `idx_user_interactions_user_created` - (user_id, created_at DESC) - User interaction history pagination
- `idx_user_interactions_content_created` - (content_item_id, created_at DESC) - Content interaction history

**Recommendations:**
- `ix_recommendations_user_id` - User-specific recommendations
- `ix_recommendations_content_item_id` - Content-specific recommendations
- `ix_recommendations_served_at` - Track served recommendations
- `ix_recommendations_recommendation_score` - Score-based sorting
- `idx_recommendations_user_score` - (user_id, recommendation_score DESC, created_at DESC) - User recommendation pagination
- `idx_recommendations_served_created` - (served_at, created_at DESC) - Served recommendation tracking

**Generation Jobs:**
- `ix_generation_jobs_user_id` - User-specific jobs
- `ix_generation_jobs_status` - Filter by job status
- `ix_generation_jobs_job_type` - Filter by job type
- `ix_generation_jobs_created_at` - Temporal queries
- `idx_generation_jobs_user_created` - (user_id, created_at DESC) - User job history pagination
- `idx_generation_jobs_status_created` - (status, created_at DESC) - Status-filtered job queries

**Tags:**
- `ix_tags_name` - Unique index for tag name lookups and uniqueness enforcement
- `idx_tags_name` - Additional B-tree index for tag name searches
- `idx_tags_created_at_desc` - (created_at DESC) - Recently created tags

**Tag Parents:**
- `idx_tag_parents_tag` - (tag_id) - Find all parents of a tag (breadcrumbs/up-links)
- `idx_tag_parents_parent` - (parent_id) - Find all children of a tag (hot path for hierarchy traversal)
- Composite primary key on (tag_id, parent_id) ensures no duplicate relationships

**Tag Ratings:**
- `ix_tag_ratings_user_id` - User-specific ratings
- `ix_tag_ratings_tag_id` - Tag-specific ratings
- `idx_tag_ratings_tag_rating` - (tag_id, rating DESC) - Sorting tags by rating
- `idx_tag_ratings_user_created` - (user_id, created_at DESC) - User rating history
- Unique constraint on (user_id, tag_id) ensures one rating per user per tag

**Users (Tag-Related):**
- `idx_users_favorite_tags_gin` - GIN index on favorite_tag_ids array for efficient tag favorite queries (PostgreSQL only)

#### Index Design Principles

1. **Composite Indexes for Common Query Patterns**: Most indexes combine filtering columns with ordering columns
2. **DESC Ordering**: Time-based indexes use DESC ordering to optimize "recent first" queries
3. **Partial Indexes**: Some indexes include WHERE clauses for frequently filtered subsets
4. **Cursor Pagination Support**: All composite indexes support efficient cursor-based pagination
5. **Multi-Column Coverage**: Indexes cover common filter + sort combinations to avoid table lookups

#### Performance Characteristics

With these indexes, the database can efficiently handle:
- **Pagination queries**: Sub-200ms response times for any page in datasets up to 10M rows
- **Cursor-based pagination**: Consistent performance regardless of page depth
- **Complex filtering**: Multi-condition queries with maintained performance
- **Concurrent access**: High-throughput scenarios with minimal lock contention

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

## Pagination and Performance

### Pagination Architecture

Genonaut implements a dual pagination system optimized for different use cases:

#### Standard Offset-Based Pagination
```python
# Request parameters
{
  "page": 1,           # Page number (1-based)
  "page_size": 50,     # Items per page (default: 50, max: 1000)
  "sort_field": "created_at",  # Sort field
  "sort_order": "desc"         # Sort order (asc/desc)
}
```

#### Cursor-Based Pagination (High-Performance)
```python
# Request parameters
{
  "cursor": "base64...",       # Encoded cursor for navigation
  "page_size": 50,             # Items per page
  "sort_field": "created_at",  # Sort field
  "sort_order": "desc"         # Sort order
}
```

### Response Format

All paginated endpoints return a standardized response format:

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 125000,       // May be estimated for very large datasets
    "total_pages": 2500,
    "has_next": true,
    "has_previous": false,
    "next_cursor": "base64...",  // For cursor-based pagination
    "prev_cursor": null
  }
}
```

### Performance Optimizations

#### Query Optimization Techniques
1. **Window Functions for Efficient Counting**: Uses `SELECT COUNT(*) OVER()` to avoid separate count queries
2. **Index-Only Scans**: Composite indexes provide all needed data without table access
3. **Cursor Stability**: Cursors remain valid even when data changes
4. **Batch Processing**: Large operations use batched inserts/updates

#### Memory Management
- **Connection Pooling**: Optimized connection pool settings for concurrent access
- **Query Result Streaming**: Large result sets are streamed to avoid memory buildup
- **Cache-Friendly Pagination**: Page boundaries align with common access patterns

### Performance Testing

#### Stress Testing Infrastructure

The database includes comprehensive stress testing capabilities:

```bash
# Run pagination stress tests
python test/api/stress/run_stress_tests.py --config production

# Run performance benchmarks
python test/api/stress/benchmark_pagination.py --dataset-size 100000
```

#### Performance Targets

| Scenario | Target Performance | Actual Performance |
|----------|-------------------|-------------------|
| Single page query (any depth) | < 200ms | < 50ms average |
| Cursor pagination consistency | < 20% variance | < 10% variance |
| Memory usage per worker | < 300MB | ~180MB average |
| Concurrent request handling | 1000+ req/s | Validated |

#### Monitoring Queries

**Check pagination performance:**
```sql
-- Monitor slow pagination queries
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE query LIKE '%LIMIT%OFFSET%' OR query LIKE '%cursor%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check index effectiveness
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    round(idx_tup_fetch::numeric / NULLIF(idx_tup_read, 0) * 100, 2) as hit_rate
FROM pg_stat_user_indexes
WHERE idx_scan > 0
ORDER BY idx_scan DESC;
```

**Analyze table growth and performance:**
```sql
-- Check table statistics for pagination optimization
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_analyze,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_stat_user_tables
WHERE n_live_tup > 1000
ORDER BY n_live_tup DESC;

-- Identify tables needing index optimization
SELECT
    t.schemaname,
    t.tablename,
    t.seq_scan,
    t.seq_tup_read,
    t.seq_tup_read / t.seq_scan as avg_seq_read,
    'Consider adding indexes' as recommendation
FROM pg_stat_user_tables t
WHERE t.seq_scan > 100 AND t.seq_tup_read / t.seq_scan > 10000
ORDER BY t.seq_tup_read DESC;
```

## Tag System Queries

The tag system supports polyhierarchical relationships where tags can have multiple parents, enabling flexible taxonomies for content organization.

### Common Tag Queries

**Find all children of a tag:**
```sql
SELECT t.*
FROM tags AS t
JOIN tag_parents AS tp ON tp.tag_id = t.id
WHERE tp.parent_id = :parent_tag_id
ORDER BY t.name;
```

**Find all parents of a tag:**
```sql
SELECT p.*
FROM tags AS p
JOIN tag_parents AS tp ON tp.parent_id = p.id
WHERE tp.tag_id = :child_tag_id
ORDER BY p.name;
```

**Find root tags (tags with no parents):**
```sql
SELECT t.*
FROM tags t
LEFT JOIN tag_parents tp ON t.id = tp.tag_id
WHERE tp.tag_id IS NULL
ORDER BY t.name;
```

**Find all descendants recursively (using CTE):**
```sql
WITH RECURSIVE descendants AS (
  -- Base case: direct children
  SELECT tp.tag_id as descendant_id, 1 as depth
  FROM tag_parents tp
  WHERE tp.parent_id = :parent_tag_id

  UNION

  -- Recursive case: children of children
  SELECT tp.tag_id, d.depth + 1
  FROM tag_parents tp
  JOIN descendants d ON tp.parent_id = d.descendant_id
  WHERE d.depth < 10  -- Prevent infinite loops
)
SELECT DISTINCT t.*, d.depth
FROM descendants d
JOIN tags t ON t.id = d.descendant_id
ORDER BY d.depth, t.name;
```

**Find all ancestors recursively (using CTE):**
```sql
WITH RECURSIVE ancestors AS (
  -- Base case: direct parents
  SELECT tp.parent_id as ancestor_id, 1 as depth
  FROM tag_parents tp
  WHERE tp.tag_id = :child_tag_id

  UNION

  -- Recursive case: parents of parents
  SELECT tp.parent_id, a.depth + 1
  FROM tag_parents tp
  JOIN ancestors a ON tp.tag_id = a.ancestor_id
  WHERE a.depth < 10  -- Prevent infinite loops
)
SELECT DISTINCT t.*, a.depth
FROM ancestors a
JOIN tags t ON t.id = a.ancestor_id
ORDER BY a.depth, t.name;
```

**Get tag with average rating:**
```sql
SELECT
    t.*,
    COALESCE(AVG(tr.rating), 0) as avg_rating,
    COUNT(tr.id) as rating_count
FROM tags t
LEFT JOIN tag_ratings tr ON tr.tag_id = t.id
WHERE t.id = :tag_id
GROUP BY t.id;
```

**Get user's rating for a tag:**
```sql
SELECT rating, created_at, updated_at
FROM tag_ratings
WHERE user_id = :user_id AND tag_id = :tag_id;
```

**Get top-rated tags:**
```sql
SELECT
    t.*,
    AVG(tr.rating) as avg_rating,
    COUNT(tr.id) as rating_count
FROM tags t
INNER JOIN tag_ratings tr ON tr.tag_id = t.id
GROUP BY t.id
HAVING COUNT(tr.id) >= 5  -- Minimum rating threshold
ORDER BY avg_rating DESC, rating_count DESC
LIMIT 20;
```

**Get user's favorite tags:**
```sql
SELECT t.*
FROM tags t
WHERE t.id = ANY(
    SELECT jsonb_array_elements_text(favorite_tag_ids)::uuid
    FROM users
    WHERE id = :user_id
)
ORDER BY t.name;
```

**Find content with specific tags (intersection):**
```sql
-- Content with ALL specified tags
SELECT ci.*
FROM content_items ci
WHERE ci.tags @> :tag_array::jsonb;

-- Example: WHERE ci.tags @> '["digital-art", "3d"]'::jsonb
```

**Find content with any of specified tags (union):**
```sql
-- Content with ANY of specified tags
SELECT ci.*
FROM content_items ci
WHERE ci.tags ?| :tag_names_array;

-- Example: WHERE ci.tags ?| ARRAY['digital-art', '3d']
```

### Tag System Performance Notes

1. **Parent-Child Queries**: The `idx_tag_parents_parent` and `idx_tag_parents_tag` indexes make these queries very efficient (O(log n + k) where k is result size)

2. **Recursive Queries**: Ancestor/descendant queries use recursive CTEs which are generally fast for moderate-depth hierarchies (< 10 levels). The depth limit prevents infinite loops in case of circular references (which shouldn't exist but are guarded against).

3. **Rating Aggregation**: Computing average ratings requires a table scan of tag_ratings. For frequently accessed tags, consider caching these values.

4. **Favorite Tags**: The GIN index on `users.favorite_tag_ids` makes favorite tag queries efficient using the `@>` (contains) operator.

5. **Content Tag Filtering**: The GIN indexes on `content_items.tags` and `content_items_auto.tags` make tag-based content filtering very efficient.

## Database Timeout Configuration

To prevent hung queries and ensure database responsiveness, Genonaut configures several PostgreSQL timeout settings at the database level.

### Configured Timeouts

| Setting | Value | Purpose |
|---------|-------|---------|
| `idle_in_transaction_session_timeout` | 30s | Terminates sessions idle in a transaction for > 30 seconds |
| `lock_timeout` | 5s | Aborts statements waiting > 5 seconds for a lock |
| `deadlock_timeout` | 1s | Time to wait before checking for deadlock (faster detection) |
| `statement_timeout` | Configurable | Maximum query execution time (configured via application config) |

### Logging and Monitoring

The following logging settings help diagnose performance issues:

| Setting | Value | Purpose |
|---------|-------|---------|
| `log_min_duration_statement` | 1000ms | Log all queries taking > 1 second |
| `log_lock_waits` | on | Log when a query waits for a lock |

### Query Statistics

The `pg_stat_statements` extension is installed to track query performance.

**Note:** To use `pg_stat_statements`, you must add it to PostgreSQL's `shared_preload_libraries`:

1. Find your `postgresql.conf` file (usually in `/usr/local/var/postgresql@XX/` on macOS or `/etc/postgresql/XX/main/` on Linux)
2. Add or update: `shared_preload_libraries = 'pg_stat_statements'`
3. Restart PostgreSQL: `brew services restart postgresql@16` (macOS) or `sudo systemctl restart postgresql` (Linux)

Once enabled, use these queries to monitor performance:

```sql
-- Top queries by total execution time
SELECT
  query,
  calls,
  total_exec_time,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Top queries by mean execution time
SELECT
  query,
  calls,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
WHERE calls > 10
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Reset statistics (if needed)
SELECT pg_stat_statements_reset();
```

### Applying Configuration Changes

These settings are applied at the database level and persist across server restarts. To modify:

```sql
-- Change database-level setting
ALTER DATABASE genonaut SET idle_in_transaction_session_timeout = '45s';

-- Change role-level setting (for genonaut_rw role)
ALTER ROLE genonaut_rw IN DATABASE genonaut SET idle_in_transaction_session_timeout = '45s';

-- Verify settings (requires new connection)
SHOW idle_in_transaction_session_timeout;
```

Settings take effect on new connections only. Restart the application to apply changes.

For more detailed migration procedures and troubleshooting, see [Database Migrations](./db_migrations.md).

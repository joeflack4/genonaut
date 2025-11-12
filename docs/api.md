# API Documentation

Genonaut provides a complete REST API built with FastAPI, offering 77 endpoints across all core functionality.

## Running the API Server

Start the API server using the make commands for different database environments:

**Development Database:**
```bash
make api-dev
```

**Demo Database:**
```bash
make api-demo
```

**Test Database:**
```bash
make api-test
```

**Manual Start (Advanced):**
```bash
# Development database
APP_ENV=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload

# Demo database
APP_ENV=demo uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload

# Test database
APP_ENV=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload
```

## API Configuration

### Environment Variables

| Environment Variable | Description | Default | Example |
|---------------------|-------------|---------|---------|
| `API_SECRET_KEY` | Secret key for JWT tokens and cryptographic operations | `your-secret-key-change-this-in-production` | `my-super-secret-key-123` |
| `API_HOST` | Host address for the API server | `0.0.0.0` | `127.0.0.1` |
| `API_PORT` | Port for the API server | `8001` | `9000` |
| `API_DEBUG` | Enable debug mode (auto-reload, detailed errors) | `false` | `true` |
| `APP_ENV` | Which database to use by default (`dev`/`demo`/`test`) | `dev` | `test` |
| `DATABASE_URL_DEMO` | Demo database connection URL | Uses `DATABASE_URL` with demo DB name | `postgresql://user:pass@localhost:5432/genonaut_demo` |

## API Documentation & Testing

Once the server is running, you can access:

- **Interactive API Docs (Swagger):** `http://localhost:8001/docs`
- **Alternative API Docs (ReDoc):** `http://localhost:8001/redoc`
- **Health Check:** `http://localhost:8001/api/v1/health`
- **Database Info:** `http://localhost:8001/api/v1/databases`
- **Global Statistics:** `http://localhost:8001/api/v1/stats/global`

## API Endpoints Overview

The API provides **77 endpoints** across 6 main categories:

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Users** | 11 | User CRUD, preferences, authentication, search, statistics |
| **Content** | 12 | Content CRUD, search by metadata/tags, quality scoring, filtering |
| **Tags** | 14 | Hierarchy, browsing, ratings, favorites, statistics |
| **Interactions** | 13 | User behavior tracking, analytics, interaction recording |
| **Recommendations** | 15 | Recommendation generation, serving, bulk operations, analytics |
| **Generation Jobs** | 17 | Content generation job management, queue processing, status tracking |
| **System** | 9 | Health checks, database info, global statistics, monitoring |

### User Management Endpoints

**Core User Operations:**
- `POST /api/v1/users` - Create new user
- `GET /api/v1/users/{id}` - Get user profile
- `PUT /api/v1/users/{id}` - Update user profile
- `DELETE /api/v1/users/{id}` - Delete user
- `PUT /api/v1/users/{id}/preferences` - Update user preferences

**User Analytics & Search:**
- `GET /api/v1/users/search` - Search users with filters
- `GET /api/v1/users/{id}/stats` - Get user statistics
- `GET /api/v1/users/{id}/interactions` - Get user interaction history
- `GET /api/v1/users/{id}/recommendations` - Get user recommendations
- `GET /api/v1/users/{id}/generation-jobs` - Get user's generation jobs
- `PUT /api/v1/users/{id}/status` - Update user active status

### Content Management Endpoints

**Content CRUD:**
- `POST /api/v1/content` - Create new content
- `GET /api/v1/content` - List content with filtering and pagination
- `GET /api/v1/content/{id}` - Get specific content item
- `PUT /api/v1/content/{id}` - Update content
- `DELETE /api/v1/content/{id}` - Delete content

**Content Operations:**
- `POST /api/v1/content/search` - Search content with advanced filters
- `PUT /api/v1/content/{id}/quality` - Update content quality score
- `GET /api/v1/content/by-creator/{creator_id}` - Get content by creator
- `GET /api/v1/content/top-rated` - Get highest rated content
- `GET /api/v1/content/recent` - Get recently created content
- `GET /api/v1/content/public` - Get public content only
- `GET /api/v1/content/by-type/{content_type}` - Filter by content type

**Unified Content API:**
- `GET /api/v1/content/unified` - Get combined regular and auto-generated content with advanced filtering
- `GET /api/v1/content/stats/unified` - Get statistics for all content types

### Tag Management Endpoints

**Core Tag Operations:**
- `GET /api/v1/tags` - List tags with pagination, sorting (`name-asc`, `rating-desc`, etc.), and optional search/minimum ratings filter
- `GET /api/v1/tags/search` - Convenience search endpoint (delegates to tag listing)
- `GET /api/v1/tags/{tag_id}` - Retrieve a tag’s detail view (parents, children, ancestors/descendants, ratings, favorites)
- `GET /api/v1/tags/by-name/{tag_name}` - Retrieve tag detail by slug name
- `GET /api/v1/tags/hierarchy` - Fetch the hierarchy, optionally including average ratings
- `POST /api/v1/tags/hierarchy/refresh` - Refresh cached hierarchy data
- `GET /api/v1/tags/statistics` - Global hierarchy statistics
- `GET /api/v1/tags/popular` - Get most popular tags by content count (see details below)

**Hierarchy navigation:**
- `GET /api/v1/tags/roots` - Root tags
- `GET /api/v1/tags/{tag_id}/parents` - Direct parents
- `GET /api/v1/tags/{tag_id}/children` - Direct children
- `GET /api/v1/tags/{tag_id}/ancestors` - Ancestors with depth metadata
- `GET /api/v1/tags/{tag_id}/descendants` - Descendants with depth metadata

**Ratings & favorites:**
- `POST /api/v1/tags/{tag_id}/rate` / `DELETE /api/v1/tags/{tag_id}/rate` - Upsert or remove a rating
- `GET /api/v1/tags/{tag_id}/rating` - Fetch the current user's rating value
- `GET /api/v1/tags/ratings` - Fetch many ratings for the current user (query `tag_ids[]`)
- `GET /api/v1/tags/favorites` - Fetch favorites for the current user (query `user_id`)
- `POST /api/v1/tags/{tag_id}/favorite` / `DELETE /api/v1/tags/{tag_id}/favorite` - Manage favorites

#### Popular Tags Endpoint

Returns tags ordered by their content cardinality (number of associated content items), using pre-computed statistics from the `tag_cardinality_stats` table that is refreshed daily by a Celery background job.

**Endpoint:**
```
GET /api/v1/tags/popular
```

**Query Parameters:**
- `limit` (optional, integer, 1-100, default: 20) - Maximum number of tags to return
- `content_source` (optional, string: `items` | `auto`) - Filter by content source; when omitted, aggregates across all sources
- `min_cardinality` (optional, integer, default: 1) - Minimum content count required to include a tag

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "tag-name",
    "cardinality": 150
  },
  ...
]
```

**Example Requests:**
```bash
# Get top 20 popular tags (aggregated across all sources)
GET /api/v1/tags/popular

# Get top 10 popular tags from user-created content only
GET /api/v1/tags/popular?limit=10&content_source=items

# Get popular tags with at least 100 content items
GET /api/v1/tags/popular?min_cardinality=100
```

**Data Source:**
The endpoint queries the `tag_cardinality_stats` table, which is maintained by the `refresh_tag_cardinality_stats` Celery task that runs daily. This provides fast query performance without needing to scan the large `content_tags` junction table.

### Unified Content Endpoint

The unified content endpoint provides a powerful way to query both regular and auto-generated content with precise filtering capabilities.

#### Endpoint
```
GET /api/v1/content/unified
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (1-based) |
| `page_size` | integer | No | 10 | Items per page (max: 1000) |
| `content_source_types` | array[string] | No | all types | **Preferred method** - Specific content-source combinations. Values: `user-regular`, `user-auto`, `community-regular`, `community-auto` |
| `content_types` | string | No | `regular,auto` | **Legacy** - Comma-separated content types. Values: `regular`, `auto` |
| `creator_filter` | string | No | `all` | **Legacy** - Creator filter. Values: `all`, `user`, `community` |
| `user_id` | UUID | No | null | User ID for filtering user vs community content |
| `search_term` | string | No | null | Search term for title filtering |
| `sort_field` | string | No | `created_at` | Field to sort by |
| `sort_order` | string | No | `desc` | Sort order: `asc` or `desc` |
| `tag` | array[string] | No | null | Filter by tags (can specify multiple) |
| `tag_names` | array[string] | No | null | Additional filter alias for tag names (equivalent to `tag`) |
| `tag_match` | string | No | `any` | Tag logic: `any` (OR) or `all` (AND) when filtering by tags |

#### Using content_source_types (Recommended)

The `content_source_types` parameter provides precise control over which content to retrieve. It accepts an array of the following values:

- `user-regular` - Regular content created by the specified user
- `user-auto` - Auto-generated content created by the specified user
- `community-regular` - Regular content created by other users
- `community-auto` - Auto-generated content created by other users

**Examples:**

```bash
# Get only the user's regular content
GET /api/v1/content/unified?content_source_types=user-regular&user_id=<uuid>

# Get all auto-generated content (user + community)
GET /api/v1/content/unified?content_source_types=user-auto&content_source_types=community-auto&user_id=<uuid>

# Get all user content (regular + auto)
GET /api/v1/content/unified?content_source_types=user-regular&content_source_types=user-auto&user_id=<uuid>

# Get all regular content (user + community)
GET /api/v1/content/unified?content_source_types=user-regular&content_source_types=community-regular&user_id=<uuid>

# Get all content
GET /api/v1/content/unified?content_source_types=user-regular&content_source_types=user-auto&content_source_types=community-regular&content_source_types=community-auto&user_id=<uuid>

# Get no content - explicitly select zero types (returns 0 results)
# Note: Use empty string as sentinel value because HTTP doesn't transmit empty arrays
GET /api/v1/content/unified?content_source_types=&user_id=<uuid>
```

**Important:** To explicitly select "no content types" (return 0 results), send `content_source_types=` (empty string). Omitting the parameter entirely will use legacy defaults and return all content types.

#### Legacy Parameters

For backward compatibility, the endpoint also supports the legacy combination of `content_types` and `creator_filter`:

```bash
# All content (legacy method)
GET /api/v1/content/unified?content_types=regular,auto&creator_filter=all&user_id=<uuid>

# User content only (legacy method)
GET /api/v1/content/unified?content_types=regular,auto&creator_filter=user&user_id=<uuid>

# Regular content only (legacy method)
GET /api/v1/content/unified?content_types=regular&creator_filter=all&user_id=<uuid>
```

**Note:** When `content_source_types` is provided, it takes precedence over `content_types` and `creator_filter`.

#### Response Format

```json
{
  "items": [
    {
      "id": 1,
      "title": "Example Content",
      "content_type": "image",
      "source_type": "regular",
      "creator_id": "uuid",
      "creator_username": "username",
      "quality_score": 0.85,
      "tags": ["tag1", "tag2"],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "path_thumb": "/path/to/thumbnail.jpg",
      "prompt": "Content generation prompt"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_count": 150,
    "total_pages": 15,
    "has_next": true,
    "has_previous": false
  },
  "stats": {
    "user_regular_count": 25,
    "user_auto_count": 30,
    "community_regular_count": 45,
    "community_auto_count": 50
  }
}
```

#### Filter Combinations

The `content_source_types` parameter enables all 16 possible combinations of content filtering:

| Your Gens | Your Auto-Gens | Community Gens | Community Auto-Gens | Total Combinations |
|-----------|----------------|----------------|---------------------|-------------------|
| ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ | 2^4 = 16 |

This granular control is not possible with the legacy `content_types` + `creator_filter` approach, which can only express 9 combinations.

### Interaction Tracking Endpoints

**Core Interactions:**
- `POST /api/v1/interactions` - Record user interaction
- `GET /api/v1/interactions/{id}` - Get interaction details
- `PUT /api/v1/interactions/{id}` - Update interaction
- `DELETE /api/v1/interactions/{id}` - Delete interaction

**Interaction Analytics:**
- `GET /api/v1/interactions/analytics/user-behavior/{user_id}` - User behavior analytics
- `GET /api/v1/interactions/analytics/content/{content_id}` - Content interaction analytics
- `GET /api/v1/interactions/analytics/global` - Global interaction statistics
- `GET /api/v1/interactions/by-type/{interaction_type}` - Filter by interaction type
- `GET /api/v1/interactions/by-user/{user_id}` - Get user's interactions
- `GET /api/v1/interactions/by-content/{content_id}` - Get content's interactions
- `GET /api/v1/interactions/recent` - Get recent interactions
- `GET /api/v1/interactions/top-rated` - Get highest rated interactions
- `POST /api/v1/interactions/bulk` - Bulk interaction recording

### Recommendation System Endpoints

**Recommendation CRUD:**
- `POST /api/v1/recommendations` - Create recommendation
- `GET /api/v1/recommendations/{id}` - Get recommendation details
- `PUT /api/v1/recommendations/{id}` - Update recommendation
- `DELETE /api/v1/recommendations/{id}` - Delete recommendation

**Recommendation Operations:**
- `POST /api/v1/recommendations/generate` - Generate recommendations for user
- `POST /api/v1/recommendations/bulk` - Bulk create recommendations
- `POST /api/v1/recommendations/served` - Mark recommendations as served
- `GET /api/v1/recommendations/unserved/{user_id}` - Get unserved recommendations
- `GET /api/v1/recommendations/by-algorithm/{algorithm}` - Filter by algorithm
- `GET /api/v1/recommendations/analytics/user/{user_id}` - User recommendation analytics
- `GET /api/v1/recommendations/analytics/global` - Global recommendation statistics
- `PUT /api/v1/recommendations/{id}/feedback` - Record recommendation feedback
- `GET /api/v1/recommendations/top-scoring` - Get highest scoring recommendations
- `GET /api/v1/recommendations/recent` - Get recent recommendations
- `GET /api/v1/users/{user_id}/recommendations/unserved` - User's unserved recommendations

### Generation Job Endpoints

**Job Management:**
- `POST /api/v1/generation-jobs` - Create generation job
- `GET /api/v1/generation-jobs` - List jobs with filtering
- `GET /api/v1/generation-jobs/{id}` - Get job details
- `PUT /api/v1/generation-jobs/{id}` - Update job
- `DELETE /api/v1/generation-jobs/{id}` - Delete job
- `PUT /api/v1/generation-jobs/{id}/status` - Update job status

**Queue Operations:**
- `GET /api/v1/generation-jobs/queue/stats` - Get queue statistics
- `POST /api/v1/generation-jobs/queue/process` - Process job queue
- `GET /api/v1/generation-jobs/queue/next` - Get next job to process
- `PUT /api/v1/generation-jobs/{id}/start` - Start job processing
- `PUT /api/v1/generation-jobs/{id}/complete` - Mark job complete
- `PUT /api/v1/generation-jobs/{id}/fail` - Mark job failed

**Job Analytics:**
- `GET /api/v1/generation-jobs/by-status/{status}` - Filter jobs by status
- `GET /api/v1/generation-jobs/by-type/{job_type}` - Filter jobs by type
- `GET /api/v1/generation-jobs/analytics/global` - Global job statistics
- `GET /api/v1/generation-jobs/recent` - Get recent jobs
- `GET /api/v1/users/{user_id}/generation-jobs` - Get user's jobs

### System Endpoints

**Health & Monitoring:**
- `GET /` - Root endpoint with API information
- `GET /api/v1/health` - Health check with database connectivity
- `GET /api/v1/databases` - Database information and available environments
- `GET /api/v1/stats/global` - Global system statistics

**System Information:**
- `GET /api/v1/info` - API version and build information
- `GET /api/v1/config` - Current configuration settings
- `GET /api/v1/status` - Detailed system status
- `GET /api/v1/metrics` - System performance metrics
- `GET /api/v1/version` - API version information

### Bookmarks & Favorites

The bookmarks system allows users to save and organize content items into hierarchical categories with notes, privacy settings, and custom ordering.

**Core Bookmark Operations:**
- `POST /api/v1/bookmarks` - Create new bookmark
- `GET /api/v1/bookmarks` - List user's bookmarks with filtering and sorting
- `GET /api/v1/bookmarks/{id}` - Get bookmark by ID
- `PUT /api/v1/bookmarks/{id}` - Update bookmark (note, pinned, public status)
- `DELETE /api/v1/bookmarks/{id}` - Delete bookmark (soft delete)

**Bookmark Category Operations:**
- `POST /api/v1/bookmark-categories` - Create new category
- `GET /api/v1/bookmark-categories` - List user's categories with sorting
- `GET /api/v1/bookmark-categories/{id}` - Get category by ID
- `PUT /api/v1/bookmark-categories/{id}` - Update category
- `DELETE /api/v1/bookmark-categories/{id}` - Delete category with bookmark migration
- `GET /api/v1/bookmark-categories/tree` - Get hierarchical category tree
- `GET /api/v1/bookmark-categories/{id}/children` - Get child categories
- `GET /api/v1/bookmark-categories/{id}/bookmarks` - Get bookmarks in category with content data
- `GET /api/v1/bookmark-categories/share/{share_token}` - Get public category by share token

**Category Membership:**
- `POST /api/v1/bookmarks/{id}/categories` - Add bookmark to category
- `GET /api/v1/bookmarks/{id}/categories` - List categories containing bookmark
- `DELETE /api/v1/bookmarks/{id}/categories/{category_id}` - Remove bookmark from category
- `PUT /api/v1/bookmarks/{id}/categories/{category_id}/position` - Update bookmark position in category

#### List Bookmarks with Content Data

Get a user's bookmarks with joined content metadata (title, images, ratings, etc.) for display in grids.

**Endpoint:**
```
GET /api/v1/bookmarks?user_id={uuid}
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | UUID | required | User ID to list bookmarks for |
| `pinned` | boolean | null | Filter by pinned status |
| `is_public` | boolean | null | Filter by public status |
| `category_id` | UUID | null | Filter by category ID |
| `skip` | integer | 0 | Number of records to skip |
| `limit` | integer | 100 | Maximum records to return (max: 1000) |
| `sort_field` | string | `user_rating_then_created` | Field to sort by |
| `sort_order` | string | `desc` | Sort order: `asc` or `desc` |
| `include_content` | boolean | true | Include content data (images, title, etc.) |

**Sort Field Options:**
- `user_rating_then_created` - User rating DESC NULLS LAST, then content creation date DESC
- `user_rating` - User's rating of the content item
- `quality_score` - Content quality score
- `created` - Content item creation date
- `title` - Content item title (alphabetical)

**Example Request:**
```bash
# Get first 15 pinned bookmarks sorted by user rating
GET /api/v1/bookmarks?user_id=a04237b8-f14e-4fed-9427-576c780d6e2a&pinned=true&limit=15&sort_field=user_rating_then_created

# Get bookmarks in a specific category
GET /api/v1/bookmarks?user_id=a04237b8-f14e-4fed-9427-576c780d6e2a&category_id=550e8400-e29b-41d4-a716-446655440000
```

**Response Format:**
```json
{
  "items": [
    {
      "id": "bookmark-uuid",
      "user_id": "user-uuid",
      "content_id": 123,
      "content_source_type": "items",
      "note": "My favorite image",
      "pinned": true,
      "is_public": false,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z",
      "content": {
        "id": 123,
        "title": "Beautiful Landscape",
        "quality_score": 0.95,
        "created_at": "2025-01-10T08:20:00Z",
        "path_thumb_184x272": "/path/to/thumbnail.jpg",
        "path_thumb_368x544": "/path/to/thumbnail_2x.jpg"
      },
      "user_rating": 5
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 15
}
```

#### List Bookmark Categories

Get a user's bookmark categories with optional filtering and sorting.

**Endpoint:**
```
GET /api/v1/bookmark-categories?user_id={uuid}
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | UUID | required | User ID to list categories for |
| `parent_id` | UUID | null | Filter by parent category ID |
| `is_public` | boolean | null | Filter by public status |
| `skip` | integer | 0 | Number of records to skip |
| `limit` | integer | 100 | Maximum records to return (max: 1000) |
| `sort_field` | string | `sort_index` | Field to sort by |
| `sort_order` | string | `asc` | Sort order: `asc` or `desc` |

**Sort Field Options:**
- `sort_index` - User-defined sort order
- `updated_at` - Last updated timestamp
- `created_at` - Creation timestamp
- `name` - Category name (alphabetical)

**Special Behavior:**
- If a user has zero categories, an "Uncategorized" category is automatically created
- The "Uncategorized" category cannot be deleted or renamed
- The "Uncategorized" category always displays first in frontend, regardless of sort preferences

**Example Request:**
```bash
# Get all categories sorted by last updated
GET /api/v1/bookmark-categories?user_id=a04237b8-f14e-4fed-9427-576c780d6e2a&sort_field=updated_at&sort_order=desc

# Get child categories of a parent
GET /api/v1/bookmark-categories?user_id=a04237b8-f14e-4fed-9427-576c780d6e2a&parent_id=parent-uuid
```

**Response Format:**
```json
{
  "items": [
    {
      "id": "category-uuid",
      "user_id": "user-uuid",
      "name": "Nature Photography",
      "description": "My favorite nature photos",
      "color": "#4CAF50",
      "icon": "nature",
      "cover_content_id": 456,
      "cover_content_source_type": "items",
      "parent_id": null,
      "sort_index": 0,
      "is_public": false,
      "share_token": "share-token-uuid",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 8,
  "skip": 0,
  "limit": 100
}
```

#### Get Bookmarks in Category with Content Data

Get all bookmarks in a specific category with joined content metadata and sorting.

**Endpoint:**
```
GET /api/v1/bookmark-categories/{category_id}/bookmarks?user_id={uuid}
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | UUID | required | User ID (for user ratings) |
| `skip` | integer | 0 | Number of records to skip |
| `limit` | integer | 100 | Maximum records to return (max: 1000) |
| `sort_field` | string | `user_rating_then_created` | Field to sort by |
| `sort_order` | string | `desc` | Sort order: `asc` or `desc` |
| `include_content` | boolean | true | Include content data |

**Sort Field Options:** Same as List Bookmarks endpoint

**Example Request:**
```bash
# Get bookmarks in category sorted by quality score
GET /api/v1/bookmark-categories/cat-uuid/bookmarks?user_id=user-uuid&sort_field=quality_score&sort_order=desc&limit=50
```

**Response Format:**
```json
{
  "category": {
    "id": "category-uuid",
    "name": "Nature Photography",
    "description": "My favorite nature photos",
    ...
  },
  "bookmarks": [
    {
      "id": "bookmark-uuid",
      "content": {...},
      "user_rating": 5,
      ...
    }
  ],
  "total": 24
}
```

#### Create Bookmark Category

Create a new bookmark category with optional hierarchical parent.

**Endpoint:**
```
POST /api/v1/bookmark-categories?user_id={uuid}
```

**Request Body:**
```json
{
  "name": "Nature Photography",
  "description": "My favorite nature photos",
  "color": "#4CAF50",
  "icon": "nature",
  "cover_content_id": null,
  "cover_content_source_type": null,
  "parent_id": null,
  "sort_index": 0,
  "is_public": false
}
```

**Field Constraints:**
- `name` - Required, max 255 chars, unique per user (per parent level)
- `description` - Optional, max 500 chars
- `color` - Optional, hex color code
- `icon` - Optional, icon identifier
- `cover_content_id` - Optional, must exist in content_items_all if provided
- `cover_content_source_type` - Required if cover_content_id provided (either `items` or `auto`)
- `parent_id` - Optional, must be valid category owned by same user
- `sort_index` - Optional, integer for custom ordering
- `is_public` - Optional, boolean (default: false)

**Response:** `201 Created` with BookmarkCategoryResponse

#### Delete Bookmark Category

Delete a category with optional bookmark migration to another category.

**Endpoint:**
```
DELETE /api/v1/bookmark-categories/{category_id}?target_category_id={uuid}&delete_all={bool}
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_category_id` | UUID | Uncategorized | Category to move bookmarks to |
| `delete_all` | boolean | false | If true, delete all bookmarks instead of moving |

**Behavior:**
- By default, bookmarks are moved to "Uncategorized" category
- Specify `target_category_id` to move bookmarks to a different category
- Set `delete_all=true` to delete all bookmarks in the category
- Child categories will have their `parent_id` set to NULL (orphaned)
- The "Uncategorized" category cannot be deleted (returns 422 error)

**Example Requests:**
```bash
# Delete category and move bookmarks to Uncategorized
DELETE /api/v1/bookmark-categories/cat-uuid

# Delete category and move bookmarks to another category
DELETE /api/v1/bookmark-categories/cat-uuid?target_category_id=other-cat-uuid

# Delete category and all its bookmarks
DELETE /api/v1/bookmark-categories/cat-uuid?delete_all=true
```

**Response:** `200 OK` with success message

#### Technical Notes

**Partitioned Table Support:**
- The `content_items_all` table is partitioned by `source_type` with composite primary key `(id, source_type)`
- Bookmarks reference content with both `content_id` and `content_source_type` to support partitioned FK constraints
- Valid `content_source_type` values: `items` (user-created) or `auto` (auto-generated)

**Row-Level Security:**
- Composite foreign keys enforce same-user constraints between bookmarks, categories, and category memberships
- Prevents cross-user contamination (e.g., User A adding User B's bookmark to User A's category)
- Both parent tables expose `(id, user_id)` composite keys
- Join table includes `user_id` with composite FKs to both parents

**Composite Sorting:**
- `user_rating_then_created` sorts by user rating DESC NULLS LAST, then falls back to content creation date DESC
- Ensures unrated content appears after rated content but still in chronological order
- SQL: `ORDER BY user_rating DESC NULLS LAST, content.created_at DESC`

**Soft Deletes:**
- Bookmarks use soft delete (sets `deleted_at` timestamp)
- Soft-deleted bookmarks are excluded from all queries by default
- Allows recovery and maintains referential integrity

## Route Analytics & Cache Planning

Genonaut includes a comprehensive route analytics system that tracks API endpoint usage, latency, and user patterns. This data is used to identify high-priority routes for caching to optimize performance.

### How It Works

1. **Request Capture**: Middleware captures all API requests and writes to Redis (< 1ms overhead)
2. **Data Transfer**: Celery task transfers data from Redis to PostgreSQL every 10 minutes
3. **Aggregation**: Hourly aggregation task computes statistics (avg latency, p95, p99, request counts)
4. **Analysis**: CLI tools analyze the data to recommend which routes should be cached

### Cache Analysis CLI Tools

Two CLI tools are available for analyzing route analytics data:

#### System 1: Absolute Thresholds (Production-Ready)

Best for production environments with established traffic patterns.

**Command:**
```bash
make cache-analysis n=10
```

**Parameters:**
- `n` - Number of top routes to return (default: 10)
- `days` - Days of history to analyze (default: 7)
- `format` - Output format: `table` or `json` (default: table)
- `min-requests` - Minimum avg requests/hour filter (default: 10)
- `min-latency` - Minimum p95 latency in ms filter (default: 100)

**Examples:**
```bash
# Get top 10 routes to cache (human-readable table)
make cache-analysis n=10

# Get top 20 routes from last 7 days
make cache-analysis n=20 days=7

# Get routes as JSON for programmatic consumption
make cache-analysis n=10 format=json

# Apply custom thresholds
make cache-analysis n=15 min-requests=50 min-latency=200
```

**How It Works:**
- Filters routes by absolute thresholds (minimum request rate, minimum latency)
- Calculates cache priority score: `(frequency * 10) + (latency / 100) + (user_diversity)`
- Higher score = higher priority for caching
- Ranks routes by priority score

**Output (Table Format):**
```
Top 10 routes recommended for caching:

+------+--------+------------------------------+-------------------------+-----------+-------------+--------------+----------------+--------------+
| Rank | Method | Route                        | Normalized Params       | Avg Req/Hr| P95 Latency | Unique Users | Priority Score | Success Rate |
+======+========+==============================+=========================+===========+=============+==============+================+==============+
|    1 | GET    | /api/v1/content/unified      | {"page_size": "10", ... | 2,450     | 189ms       | 45           | 24,559.4       | 98.5%        |
|    2 | GET    | /api/v1/tags/hierarchy       | {}                      | 890       | 156ms       | 32           | 9,076.2        | 99.1%        |
|    3 | GET    | /api/v1/content/{id}         | {}                      | 1,200     | 95ms        | 67           | 12,156.7       | 97.8%        |
+------+--------+------------------------------+-------------------------+-----------+-------------+--------------+----------------+--------------+
```

**Output (JSON Format):**
```json
[
  {
    "route": "/api/v1/content/unified",
    "method": "GET",
    "query_params_normalized": {"page_size": "10", "sort": "created_at"},
    "avg_hourly_requests": 2450.0,
    "avg_p95_latency_ms": 189.0,
    "avg_unique_users": 45.0,
    "cache_priority_score": 24559.4,
    "success_rate": 0.985,
    "total_requests": 411600
  }
]
```

#### System 2: Relative Ranking (Development-Friendly)

Best for development environments with low or sporadic traffic.

**Command:**
```bash
make cache-analysis-relative n=10
```

**Parameters:**
- `n` - Number of top routes to return (default: 10)
- `days` - Days of history to analyze (default: 7)
- `format` - Output format: `table` or `json` (default: table)

**Examples:**
```bash
# Get top 10 routes using relative ranking
make cache-analysis-relative n=10

# Get top 20 routes from last 7 days
make cache-analysis-relative n=20 days=7

# Get routes as JSON
make cache-analysis-relative n=10 format=json
```

**How It Works:**
- No absolute thresholds - considers all routes with any traffic
- Ranks routes by percentile compared to all other routes
- Priority score = `(latency_percentile * 0.4) + (popularity_percentile * 0.4) + (user_percentile * 0.2)`
- Perfect for development where even low-traffic routes can be identified

**Output (Table Format):**
```
Top 10 routes by relative importance:

+------+--------+-----------------------------+---------------+--------+--------+-------+------+------+-------+
| Rank | Method | Route                       | Params        | Req/Hr | P95    | Score | Pop% | Lat% | User% |
+======+========+=============================+===============+========+========+=======+======+======+=======+
|    1 | GET    | /api/v1/content/unified     | {"page_si..." | 12.5   | 1850ms | 95.2  | P92  | L98  | U95   |
|    2 | GET    | /api/v1/tags/hierarchy      | {}            | 8.2    | 1560ms | 89.4  | P85  | L94  | U89   |
|    3 | POST   | /api/v1/generation/jobs     | {}            | 3.1    | 5230ms | 87.1  | P65  | L99  | U78   |
+------+--------+-----------------------------+---------------+--------+--------+-------+------+------+-------+

Columns: Pop% (popularity), Lat% (latency), User% (user diversity)
Higher percentile = more important relative to other routes
```

**Percentile Columns:**
- `Pop%` - Popularity percentile (e.g., P92 = busier than 92% of routes)
- `Lat%` - Latency percentile (e.g., L98 = slower than 98% of routes)
- `User%` - User diversity percentile (e.g., U95 = more users than 95% of routes)
- `Score` - Combined priority score (weighted average of percentiles)

**Output (JSON Format):**
```json
[
  {
    "route": "/api/v1/content/unified",
    "method": "GET",
    "query_params_normalized": {"page_size": "10"},
    "avg_hourly_requests": 12.5,
    "avg_p95_latency_ms": 1850.0,
    "priority_score": 95.2,
    "popularity_percentile": 92.0,
    "latency_percentile": 98.0,
    "user_percentile": 95.0,
    "success_rate": 0.985,
    "total_requests": 525
  }
]
```

### Query Parameter Normalization

Route analytics uses smart query parameter normalization to group similar requests:

**What Gets Normalized:**
- Pagination parameters (`page`, `offset`, `limit`, `cursor`) are excluded from normalization
- Filtering parameters (`sort`, `content_types`, `tag`) are included in normalization

**Why This Matters:**
- Groups all pages of the same query pattern together
- Identifies popular query patterns (e.g., "page_size=10 with sort=created_at")
- Enables smart cache decisions (cache first N pages of popular patterns)

**Example:**
```
Original routes:
- /api/v1/content/unified?page=1&page_size=10&sort=created_at
- /api/v1/content/unified?page=2&page_size=10&sort=created_at
- /api/v1/content/unified?page=1&page_size=50&sort=created_at

Normalized groups:
1. {"page_size": "10", "sort": "created_at"} - 2 requests
2. {"page_size": "50", "sort": "created_at"} - 1 request
```

### Database Schema

**route_analytics** - Raw request events:
- Captures every API request (route, method, user, timestamp, duration_ms, status_code)
- Query parameters stored in both raw and normalized JSONB fields
- Transferred from Redis to PostgreSQL every 10 minutes

**route_analytics_hourly** - Aggregated statistics:
- One row per hour per route pattern
- Pre-computed metrics: avg, p50, p95, p99 duration, unique users, request counts
- Enables fast cache planning queries without scanning millions of raw events
- Updated hourly by Celery background task

### Use Cases

**For Production:**
Use System 1 (absolute thresholds) to identify routes that meet specific performance criteria.

**For Development:**
Use System 2 (relative ranking) to identify slow/popular routes even with low traffic.

**For Automated Caching:**
Use JSON output format to feed results into automated cache configuration systems.

### Configuration

Cache planning settings are configured in `config/base.json`:

```json
{
  "cache-planning": {
    "top-n-routes": 20,
    "pages-to-cache-per-route": 1
  }
}
```

### Direct CLI Usage

Both tools can also be invoked directly:

```bash
# Activate virtual environment first
source env/python_venv/bin/activate

# System 1 (absolute thresholds)
ENV_TARGET=local-demo python -m genonaut.cli.cache_analysis --count=10 --days=7 --format=table

# System 2 (relative ranking)
ENV_TARGET=local-demo python -m genonaut.cli.cache_analysis_relative --count=10 --days=7 --format=json
```

### Analytics API Endpoints

The route analytics functionality is also exposed via REST API endpoints for programmatic access from other services. All endpoints return JSON responses.

#### GET /api/v1/analytics/routes/cache-priorities

Get top N routes recommended for caching, using either absolute or relative analysis systems.

**Query Parameters:**
- `n` (integer, 1-100, default: 10) - Number of top routes to return
- `days` (integer, 1-90, default: 7) - Days of history to analyze
- `system` (string: "absolute" | "relative", default: "absolute") - Analysis system to use
- `min_requests` (integer, default: 10) - Minimum avg requests/hour (absolute system only)
- `min_latency` (integer, default: 100) - Minimum p95 latency in ms (absolute system only)

**Example Requests:**
```bash
# Get top 5 routes using absolute thresholds (production)
curl "http://localhost:8001/api/v1/analytics/routes/cache-priorities?n=5&system=absolute"

# Get top 10 routes using relative ranking (development)
curl "http://localhost:8001/api/v1/analytics/routes/cache-priorities?n=10&system=relative"

# Get top 20 routes from last 30 days with custom thresholds
curl "http://localhost:8001/api/v1/analytics/routes/cache-priorities?n=20&days=30&system=absolute&min_requests=50&min_latency=200"
```

**Response (Absolute System):**
```json
{
  "system": "absolute",
  "lookback_days": 7,
  "total_routes": 5,
  "routes": [
    {
      "route": "/api/v1/content/unified",
      "method": "GET",
      "query_params_normalized": {"page_size": "10", "sort": "created_at"},
      "avg_hourly_requests": 2450.0,
      "avg_p95_latency_ms": 189.0,
      "avg_unique_users": 45.0,
      "cache_priority_score": 24559.4,
      "success_rate": 0.985,
      "total_requests": 411600
    }
  ]
}
```

**Response (Relative System):**
```json
{
  "system": "relative",
  "lookback_days": 7,
  "total_routes": 5,
  "routes": [
    {
      "route": "/api/v1/content/unified",
      "method": "GET",
      "query_params_normalized": {"page_size": "10"},
      "avg_hourly_requests": 12.5,
      "avg_p95_latency_ms": 1850.0,
      "priority_score": 95.2,
      "popularity_percentile": 92.0,
      "latency_percentile": 98.0,
      "user_percentile": 95.0,
      "success_rate": 0.985,
      "total_requests": 525
    }
  ]
}
```

#### GET /api/v1/analytics/routes/performance-trends

Get time-series performance trends for a specific route over time.

**Query Parameters:**
- `route` (string, required) - Route path to analyze (e.g., `/api/v1/content/unified`)
- `days` (integer, 1-90, default: 7) - Days of history to analyze
- `granularity` (string: "hourly" | "daily", default: "hourly") - Data granularity

**Example Requests:**
```bash
# Get hourly trends for unified content endpoint (last 7 days)
curl "http://localhost:8001/api/v1/analytics/routes/performance-trends?route=/api/v1/content/unified&days=7&granularity=hourly"

# Get daily trends for tag hierarchy endpoint (last 30 days)
curl "http://localhost:8001/api/v1/analytics/routes/performance-trends?route=/api/v1/tags/hierarchy&days=30&granularity=daily"
```

**Response:**
```json
{
  "route": "/api/v1/content/unified",
  "granularity": "hourly",
  "lookback_days": 7,
  "data_points": 168,
  "trends": [
    {
      "timestamp": "2025-01-15T00:00:00",
      "total_requests": 145,
      "successful_requests": 143,
      "client_errors": 2,
      "server_errors": 0,
      "avg_duration_ms": 156,
      "p50_duration_ms": 120,
      "p95_duration_ms": 189,
      "p99_duration_ms": 245,
      "unique_users": 23,
      "success_rate": 0.986
    }
  ]
}
```

**Use Cases:**
- Identify performance degradation over time
- Spot traffic patterns and spikes
- Monitor impact of code changes
- Track success rate trends

#### GET /api/v1/analytics/routes/peak-hours

Analyze peak traffic hours for routes to plan cache warming and scaling strategies.

**Query Parameters:**
- `route` (string, optional) - Filter by specific route (omit to analyze all routes)
- `days` (integer, 7-90, default: 30) - Days of history to analyze
- `min_requests` (integer, default: 50) - Minimum avg requests for a route to be included

**Example Requests:**
```bash
# Get peak hours for all routes
curl "http://localhost:8001/api/v1/analytics/routes/peak-hours?days=30&min_requests=10"

# Get peak hours for specific route
curl "http://localhost:8001/api/v1/analytics/routes/peak-hours?route=/api/v1/content/unified&days=30"
```

**Response:**
```json
{
  "route": "/api/v1/content/unified",
  "lookback_days": 30,
  "min_requests_threshold": 50,
  "total_patterns": 24,
  "peak_hours": [
    {
      "route": "/api/v1/content/unified",
      "hour_of_day": 14,
      "avg_requests": 2845.5,
      "avg_p95_latency_ms": 198.3,
      "avg_unique_users": 67.2,
      "data_points": 30
    },
    {
      "route": "/api/v1/content/unified",
      "hour_of_day": 15,
      "avg_requests": 2712.8,
      "avg_p95_latency_ms": 203.1,
      "avg_unique_users": 64.5,
      "data_points": 30
    }
  ]
}
```

**Use Cases:**
- Plan cache warming schedules
- Identify when to scale infrastructure
- Schedule maintenance windows
- Optimize resource allocation

### Generation Analytics API Endpoints

The generation analytics system tracks all image generation activity including requests, completions, failures, and cancellations. Data flows from MetricsService to Redis Streams, then to PostgreSQL via Celery background tasks, providing both real-time and historical analytics.

**Data Pipeline:**
1. MetricsService records events to Redis Streams (< 1ms overhead)
2. Celery transfers events to PostgreSQL `generation_events` table (every 10 minutes)
3. Celery aggregates hourly metrics into `generation_metrics_hourly` table (hourly)
4. API endpoints query aggregated data for analytics

#### GET /api/v1/analytics/generation/overview

Get high-level dashboard overview of generation activity.

**Query Parameters:**
- `days` (integer, 1-90, default: 7) - Days of history to analyze

**Example Requests:**
```bash
# Get overview for last 7 days
curl "http://localhost:8001/api/v1/analytics/generation/overview?days=7"

# Get overview for last 30 days
curl "http://localhost:8001/api/v1/analytics/generation/overview?days=30"
```

**Response:**
```json
{
  "lookback_days": 7,
  "total_requests": 1500,
  "successful_generations": 1425,
  "failed_generations": 50,
  "cancelled_generations": 25,
  "success_rate_pct": 95.0,
  "avg_duration_ms": 3500,
  "p50_duration_ms": 3200,
  "p95_duration_ms": 5800,
  "p99_duration_ms": 7200,
  "total_images_generated": 1425,
  "hours_with_data": 168,
  "latest_data_timestamp": "2025-10-23T14:30:00"
}
```

**Metrics Explained:**
- `success_rate_pct` - Percentage of successful generations (successful / total_requests * 100)
- `avg_duration_ms` - Average generation duration in milliseconds
- `p50/p95/p99_duration_ms` - Duration percentiles (50th, 95th, 99th)
- `hours_with_data` - Number of hours with recorded activity

#### GET /api/v1/analytics/generation/trends

Get time-series trends for generation metrics.

**Query Parameters:**
- `days` (integer, 1-90, default: 7) - Days of history to analyze
- `interval` (string: "hourly" | "daily", default: "hourly") - Data granularity

**Example Requests:**
```bash
# Get hourly trends for last 7 days
curl "http://localhost:8001/api/v1/analytics/generation/trends?days=7&interval=hourly"

# Get daily trends for last 30 days
curl "http://localhost:8001/api/v1/analytics/generation/trends?days=30&interval=daily"
```

**Response:**
```json
{
  "interval": "hourly",
  "lookback_days": 7,
  "total_data_points": 168,
  "data_points": [
    {
      "timestamp": "2025-10-23T00:00:00",
      "total_requests": 45,
      "successful_generations": 43,
      "failed_generations": 2,
      "cancelled_generations": 0,
      "avg_duration_ms": 3200,
      "p50_duration_ms": 3100,
      "p95_duration_ms": 5500,
      "p99_duration_ms": 7200,
      "unique_users": 12,
      "avg_queue_length": 2.5,
      "max_queue_length": 8,
      "total_images_generated": 43,
      "success_rate": 0.956
    }
  ]
}
```

**Use Cases:**
- Identify generation patterns and spikes
- Monitor performance degradation over time
- Track success rate trends
- Analyze queue behavior

#### GET /api/v1/analytics/generation/users/{user_id}

Get generation analytics for a specific user.

**Path Parameters:**
- `user_id` (UUID, required) - User ID to analyze

**Query Parameters:**
- `days` (integer, 1-90, default: 30) - Days of history to analyze

**Example Requests:**
```bash
# Get analytics for specific user (last 30 days)
curl "http://localhost:8001/api/v1/analytics/generation/users/550e8400-e29b-41d4-a716-446655440000?days=30"

# Get analytics for specific user (last 7 days)
curl "http://localhost:8001/api/v1/analytics/generation/users/550e8400-e29b-41d4-a716-446655440000?days=7"
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "lookback_days": 30,
  "total_requests": 125,
  "successful_generations": 118,
  "failed_generations": 5,
  "cancelled_generations": 2,
  "success_rate_pct": 94.4,
  "avg_duration_ms": 3450,
  "p50_duration_ms": 3300,
  "p95_duration_ms": 5200,
  "last_generation_at": "2025-10-23T14:30:00",
  "first_generation_at": "2025-09-23T10:15:00",
  "recent_activity": [
    {
      "timestamp": "2025-10-23T14:30:00",
      "event_type": "completion",
      "duration_ms": 3200,
      "success": true,
      "error_type": null,
      "generation_type": "standard"
    }
  ],
  "failure_breakdown": [
    {"error_type": "timeout", "count": 3},
    {"error_type": "oom", "count": 2}
  ]
}
```

**Use Cases:**
- User-specific generation history and performance
- Identify problematic users or usage patterns
- Debug user-specific issues
- Track user engagement with generation features

#### GET /api/v1/analytics/generation/models

Get performance comparison across different models.

**Query Parameters:**
- `days` (integer, 1-90, default: 30) - Days of history to analyze

**Example Requests:**
```bash
# Get model performance for last 30 days
curl "http://localhost:8001/api/v1/analytics/generation/models?days=30"

# Get model performance for last 7 days
curl "http://localhost:8001/api/v1/analytics/generation/models?days=7"
```

**Response:**
```json
{
  "lookback_days": 30,
  "total_models": 5,
  "models": [
    {
      "model_checkpoint": "sd_xl_base_1.0.safetensors",
      "total_generations": 850,
      "successful_generations": 825,
      "failed_generations": 25,
      "success_rate_pct": 97.06,
      "avg_duration_ms": 3200,
      "p50_duration_ms": 3100,
      "p95_duration_ms": 4800,
      "last_used_at": "2025-10-23T14:30:00"
    }
  ]
}
```

**Use Cases:**
- Compare model reliability and performance
- Identify problematic models
- Capacity planning by model
- Model selection optimization

#### GET /api/v1/analytics/generation/failures

Get detailed analysis of generation failures.

**Query Parameters:**
- `days` (integer, 1-90, default: 7) - Days of history to analyze

**Example Requests:**
```bash
# Get failure analysis for last 7 days
curl "http://localhost:8001/api/v1/analytics/generation/failures?days=7"

# Get failure analysis for last 30 days
curl "http://localhost:8001/api/v1/analytics/generation/failures?days=30"
```

**Response:**
```json
{
  "lookback_days": 7,
  "total_error_types": 4,
  "error_types": [
    {
      "error_type": "timeout",
      "count": 45,
      "avg_duration_ms": 30000,
      "sample_messages": [
        "ComfyUI request timeout after 30s",
        "Generation queue timeout"
      ]
    },
    {
      "error_type": "oom",
      "count": 12,
      "avg_duration_ms": 15000,
      "sample_messages": ["Out of memory on GPU"]
    }
  ],
  "failure_trends": [
    {
      "date": "2025-10-23",
      "total_completions": 250,
      "failures": 8,
      "failure_rate": 0.032
    }
  ]
}
```

**Use Cases:**
- Debug recurring issues
- Identify system bottlenecks
- Monitor service health
- Plan infrastructure improvements

#### GET /api/v1/analytics/generation/peak-hours

Get analysis of peak generation times by hour of day.

**Query Parameters:**
- `days` (integer, 7-90, default: 30) - Days of history to analyze

**Example Requests:**
```bash
# Get peak hours for last 30 days
curl "http://localhost:8001/api/v1/analytics/generation/peak-hours?days=30"

# Get peak hours for last 7 days
curl "http://localhost:8001/api/v1/analytics/generation/peak-hours?days=7"
```

**Response:**
```json
{
  "lookback_days": 30,
  "total_hours_analyzed": 24,
  "peak_hours": [
    {
      "hour_of_day": 14,
      "avg_requests": 85.5,
      "avg_queue_length": 3.2,
      "avg_max_queue_length": 8.5,
      "avg_p95_duration_ms": 5200,
      "avg_unique_users": 25.3,
      "data_points": 30
    },
    {
      "hour_of_day": 15,
      "avg_requests": 78.2,
      "avg_queue_length": 2.8,
      "avg_max_queue_length": 7.1,
      "avg_p95_duration_ms": 4900,
      "avg_unique_users": 22.7,
      "data_points": 30
    }
  ]
}
```

**Use Cases:**
- Capacity planning and resource allocation
- Identify bottleneck hours
- Plan maintenance windows
- Understand user behavior patterns

## Enhanced Pagination System

Genonaut provides a comprehensive pagination system optimized for performance at scale. All list endpoints support consistent pagination parameters and response formats.

### Pagination Parameters

All paginated endpoints accept these standard parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-based indexing) |
| `page_size` | integer | 50 | Items per page (max: 1000) |
| `sort_field` | string | varies | Field to sort by |
| `sort_order` | string | `desc` | Sort order: `asc` or `desc` |
| `cursor` | string | null | Base64-encoded cursor for cursor-based pagination |

### Standard Response Format

All paginated endpoints return a consistent response structure:

```json
{
  "items": [
    // Array of requested items
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 12500,
    "total_pages": 250,
    "has_next": true,
    "has_previous": false,
    "next_cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNC0xMi0wMVQxMDo...",
    "prev_cursor": null
  }
}
```

### Enhanced Endpoints

All content and list endpoints include enhanced versions optimized for large datasets:

#### Content Endpoints
- `GET /api/v1/content/enhanced` - Enhanced content listing with advanced filtering
- `GET /api/v1/content-auto/enhanced` - Enhanced auto-content listing
- Additional enhanced endpoints available for all content types

#### Advanced Filtering

Enhanced endpoints support sophisticated filtering:

```bash
# Filter by content type and creator
GET /api/v1/content/enhanced?content_type=text&creator_id=user-123

# Public content only with quality filtering
GET /api/v1/content/enhanced?public_only=true&min_quality_score=0.8

# Search with sorting
GET /api/v1/content/enhanced?search_term=python&sort_field=quality_score&sort_order=desc

# Cursor-based pagination for high performance
GET /api/v1/content/enhanced?cursor=eyJjcmVhdGVkX2F0Ijo...&page_size=100
```

### Pagination Types

#### 1. Offset-Based Pagination (Standard)

Best for: Small to medium datasets, when total count is needed

```bash
# Get page 5 with 20 items per page
GET /api/v1/content/enhanced?page=5&page_size=20
```

#### 2. Cursor-Based Pagination (High-Performance)

Best for: Large datasets, real-time feeds, when consistent performance is critical

```bash
# First request
GET /api/v1/content/enhanced?page_size=50

# Subsequent requests use cursor from previous response
GET /api/v1/content/enhanced?cursor=eyJjcmVhdGVkX2F0Ijo...&page_size=50
```

### Performance Characteristics

| Pagination Type | Dataset Size | Performance | Use Case |
|-----------------|--------------|-------------|----------|
| **Offset-based** | < 100K rows | Good | General browsing, small datasets |
| **Cursor-based** | > 100K rows | Excellent | Large datasets, real-time feeds |

#### Cursor Pagination Advantages
- **Consistent Performance**: Response time doesn't degrade with page depth
- **Real-time Stability**: Results remain consistent even when data changes
- **Memory Efficient**: No need to count total results for large datasets
- **Scalable**: Performance maintained across millions of rows

### Rate Limiting & Performance

- **Default Limits**: 1000 requests per minute per IP
- **Page Size Limits**: Maximum 1000 items per page
- **Response Time Targets**: < 200ms for any pagination query
- **Concurrent Support**: Optimized for high-concurrency scenarios

### Error Handling

Pagination-specific error responses:

```json
{
  "detail": "Page size cannot exceed 1000",
  "error_code": "INVALID_PAGE_SIZE",
  "status": 422
}

{
  "detail": "Invalid cursor format",
  "error_code": "INVALID_CURSOR",
  "status": 400
}

{
  "detail": "Page number out of range",
  "error_code": "PAGE_OUT_OF_RANGE",
  "status": 404
}
```

### Best Practices

#### For Small Datasets (< 10K items)
```bash
# Use standard pagination with page numbers
GET /api/v1/content?page=1&page_size=50&sort_field=created_at&sort_order=desc
```

#### For Large Datasets (> 10K items)
```bash
# Use cursor pagination for consistent performance
GET /api/v1/content/enhanced?cursor=...&page_size=100
```

#### For Real-time Feeds
```bash
# Always use cursor pagination to handle concurrent updates
GET /api/v1/content/enhanced?sort_field=created_at&sort_order=desc&page_size=25
```

### Implementation Example

```javascript
// JavaScript client example for cursor-based pagination
async function fetchAllItems(baseUrl, params = {}) {
  let allItems = [];
  let cursor = null;

  do {
    const url = new URL(`${baseUrl}/api/v1/content/enhanced`);
    if (cursor) url.searchParams.set('cursor', cursor);
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });

    const response = await fetch(url);
    const data = await response.json();

    allItems.push(...data.items);
    cursor = data.pagination.next_cursor;
  } while (cursor && data.pagination.has_next);

  return allItems;
}

// Usage
const items = await fetchAllItems('http://localhost:8001', {
  sort_field: 'quality_score',
  sort_order: 'desc',
  page_size: 100
});
```

## Configuration & Gotchas

### 🔧 Configuration Notes
- API configuration is loaded from `.env` file in the `env/` directory
- Database connections are managed automatically based on `APP_ENV`
- The API supports both dev and demo databases simultaneously

### ⚠️ Important Caveats
- **Database Initialization Required:** Run `make init-dev`, `make init-demo`, and (for integration tests) `make init-test` before starting the API
- **Environment Variables:** Ensure database credentials are set in `.env` file
- **Port Conflicts:** Default port 8001 - change `API_PORT` if conflicted
- **CORS Settings:** Currently set to allow all origins (`*`) - configure for production use

### 🚨 Production Gotchas
- **Secret Key:** Change `API_SECRET_KEY` to a secure random value in production
- **Debug Mode:** Set `API_DEBUG=false` in production
- **CORS Origins:** Restrict `allow_origins` in production (see `genonaut/api/main.py`)
- **Database URLs:** Use full `DATABASE_URL` with connection pooling for production
- **SSL/TLS:** Use HTTPS proxy (nginx/Apache) in front of uvicorn in production

### 🔍 Troubleshooting
- **"Database error" responses:** Check database connection and credentials
- **Import errors:** Ensure all dependencies installed: `pip install -r requirements.txt`
- **Pydantic validation errors:** Check request body format matches API docs
- **Port in use:** Change `API_PORT` or kill existing process on port 8001

## Request/Response Format

### Standard Response Format
All API responses follow a consistent format:

**Success Response:**
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "ErrorType",
  "detail": "Detailed error message",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Statement Timeout Errors

Long-running database operations are cancelled once they exceed the configured `statement_timeout`. When this happens the API returns **HTTP 504 Gateway Timeout** with a structured payload so callers can distinguish it from other failures.

```json
{
  "error_type": "statement_timeout",
  "message": "The operation took too long to complete. Please try again or refine your request.",
  "timeout_duration": "15s",
  "details": {
    "query": "SELECT ...",
    "context": {
      "path": "/api/v1/gallery",
      "method": "GET",
      "endpoint": "get_gallery_items"
    }
  }
}
```

- `error_type` is always `statement_timeout`
- `timeout_duration` mirrors the active configuration value
- `details.context` includes best-effort request metadata (route, HTTP method, user id when available)
- `details.query` is truncated to protect logs/clients from extremely long statements

Clients should surface this error to users with retry guidance instead of treating it as a generic failure.


**Paginated Response:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 100,
    "skip": 0,
    "limit": 10,
    "has_more": true
  }
}
```

### Authentication
Currently, the API does not implement authentication. This is planned for future development phases.

### Rate Limiting
Rate limiting is not currently implemented but is planned for production deployment.

## API Development

### Adding New Endpoints
1. Create request/response models in `genonaut/api/models/`
2. Add business logic to appropriate service in `genonaut/api/services/`
3. Create route handler in `genonaut/api/routes/`
4. Add endpoint to route registration in `genonaut/api/main.py`
5. Write tests in `test/api/`

### OpenAPI Documentation
The API automatically generates OpenAPI/Swagger documentation. Enhance it by:
- Adding detailed docstrings to route handlers
- Using Pydantic model descriptions and examples
- Adding response model annotations
- Including proper HTTP status codes

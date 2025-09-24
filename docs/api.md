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
API_ENVIRONMENT=dev uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8000 --reload

# Demo database
API_ENVIRONMENT=demo uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8000 --reload

# Test database
API_ENVIRONMENT=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Configuration

### Environment Variables

| Environment Variable | Description | Default | Example |
|---------------------|-------------|---------|---------|
| `API_SECRET_KEY` | Secret key for JWT tokens and cryptographic operations | `your-secret-key-change-this-in-production` | `my-super-secret-key-123` |
| `API_HOST` | Host address for the API server | `0.0.0.0` | `127.0.0.1` |
| `API_PORT` | Port for the API server | `8000` | `9000` |
| `API_DEBUG` | Enable debug mode (auto-reload, detailed errors) | `false` | `true` |
| `API_ENVIRONMENT` | Which database to use by default (`dev`/`demo`/`test`) | `dev` | `test` |
| `DATABASE_URL_DEMO` | Demo database connection URL | Uses `DATABASE_URL` with demo DB name | `postgresql://user:pass@localhost:5432/genonaut_demo` |

## API Documentation & Testing

Once the server is running, you can access:

- **Interactive API Docs (Swagger):** `http://localhost:8000/docs`
- **Alternative API Docs (ReDoc):** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/api/v1/health`
- **Database Info:** `http://localhost:8000/api/v1/databases`
- **Global Statistics:** `http://localhost:8000/api/v1/stats/global`

## API Endpoints Overview

The API provides **77 endpoints** across 6 main categories:

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Users** | 11 | User CRUD, preferences, authentication, search, statistics |
| **Content** | 12 | Content CRUD, search by metadata/tags, quality scoring, filtering |
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
const items = await fetchAllItems('http://localhost:8000', {
  sort_field: 'quality_score',
  sort_order: 'desc',
  page_size: 100
});
```

## Configuration & Gotchas

### 🔧 Configuration Notes
- API configuration is loaded from `.env` file in the `env/` directory
- Database connections are managed automatically based on `API_ENVIRONMENT`
- The API supports both dev and demo databases simultaneously

### ⚠️ Important Caveats
- **Database Initialization Required:** Run `make init-dev`, `make init-demo`, and (for integration tests) `make init-test` before starting the API
- **Environment Variables:** Ensure database credentials are set in `.env` file
- **Port Conflicts:** Default port 8000 - change `API_PORT` if conflicted
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
- **Port in use:** Change `API_PORT` or kill existing process on port 8000

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
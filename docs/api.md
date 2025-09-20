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
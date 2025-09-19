# FastAPI Implementation Design

## Architecture Overview

Adding a FastAPI layer on top of the existing Genonaut database infrastructure to create a RESTful API for the recommender system.

### Current Foundation
- Multi-schema PostgreSQL database (app/demo/test)
- SQLAlchemy models: User, ContentItem, UserInteraction, Recommendation, GenerationJob
- JSONB columns for flexible metadata storage
- Database initialization with proper user permissions (admin/rw/ro)
- Comprehensive test suite

### Proposed Architecture

```
FastAPI Routes → Services → Repositories → Database (Existing)
```

**Layered Architecture:**
- **Routes**: Handle HTTP requests, validation, authentication
- **Services**: Business logic for recommendations, content generation
- **Repositories**: Data access patterns, query optimization using existing SQLAlchemy models
- **Database**: Existing SQLAlchemy models and database setup

### Directory Structure

```
genonaut/
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── dependencies.py         # Dependency injection (DB sessions, auth)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── users.py            # User management endpoints
│   │   ├── content.py          # Content CRUD endpoints
│   │   ├── recommendations.py  # Recommendation endpoints
│   │   ├── interactions.py     # User interaction tracking
│   │   └── generation.py       # Content generation endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py         # Pydantic request models
│   │   ├── responses.py        # Pydantic response models
│   │   └── enums.py           # API enums and constants
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py     # User business logic
│   │   ├── content_service.py  # Content business logic
│   │   ├── recommendation_service.py  # Recommendation logic
│   │   └── generation_service.py     # Generation job logic
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py            # Base repository pattern
│   │   ├── user_repository.py
│   │   ├── content_repository.py
│   │   ├── interaction_repository.py
│   │   └── recommendation_repository.py
│   └── exceptions.py          # Custom API exceptions
├── db/                        # Existing database code
└── tests/
    ├── api/                   # New API tests
    │   ├── test_users.py
    │   ├── test_content.py
    │   ├── test_recommendations.py
    │   └── test_generation.py
    └── existing tests...
```

## Key Features & Patterns

### 1. Dependency Injection for Multi-Schema Support
```python
# Handle different database schemas
def get_app_session() -> Session:
    # Return session with search_path=app
    
def get_demo_session() -> Session:
    # Return session with search_path=demo
    
def get_test_session() -> Session:
    # Return session with search_path=test
```

### 2. Repository Pattern
Abstract database operations while leveraging existing SQLAlchemy models:
```python
class UserRepository:
    def __init__(self, session: Session):
        self.session = session
    
    async def get_by_preferences(self, genre_filter: Dict) -> List[User]:
        # Use existing User model with JSONB queries
```

### 3. Service Layer for Business Logic
```python
class RecommendationService:
    def __init__(self, user_repo: UserRepository, content_repo: ContentRepository):
        # Business logic using existing database models
```

### 4. Pydantic Models for API Validation
Complement existing SQLAlchemy models:
```python
class UserPreferencesUpdate(BaseModel):
    favorite_genres: List[str]
    content_types: List[ContentType]
    settings: Dict[str, Any]
```

### 5. Background Tasks for Generation Jobs
Leverage existing GenerationJob model:
```python
@app.post("/api/v1/generate-content")
async def generate_content(
    request: GenerationRequest, 
    background_tasks: BackgroundTasks
):
    # Use existing GenerationJob model
```

## API Endpoints Design

### Core RESTful Endpoints

**Users:**
- `GET /api/v1/users/{id}` - Get user profile
- `PUT /api/v1/users/{id}` - Update user profile
- `PUT /api/v1/users/{id}/preferences` - Update user preferences
- `GET /api/v1/users/{id}/interactions` - Get user interaction history

**Content:**
- `GET /api/v1/content` - List content (with filtering)
- `POST /api/v1/content` - Create new content
- `GET /api/v1/content/{id}` - Get specific content
- `PUT /api/v1/content/{id}` - Update content
- `DELETE /api/v1/content/{id}` - Delete content

**Recommendations:**
- `GET /api/v1/users/{id}/recommendations` - Get recommendations for user
- `POST /api/v1/recommendations/generate` - Generate new recommendations
- `PUT /api/v1/recommendations/{id}/feedback` - Record recommendation feedback

**Interactions:**
- `POST /api/v1/interactions` - Record user interaction
- `GET /api/v1/interactions/{id}` - Get interaction details

**Generation Jobs:**
- `POST /api/v1/generation-jobs` - Create generation job
- `GET /api/v1/generation-jobs/{id}` - Get job status
- `GET /api/v1/generation-jobs` - List jobs (with filtering)

**System:**
- `GET /health` - Health check endpoint
- `GET /api/v1/schemas` - List available schemas (app/demo/test)

### WebSocket Endpoints
- `WS /ws/generation/{job_id}` - Real-time generation status updates

## Configuration & Integration

### Settings Management
Extend existing `.env` approach:
```python
class Settings(BaseSettings):
    # Existing DB settings
    database_url: str
    db_password_admin: str
    db_password_rw: str
    db_password_ro: str
    
    # New API settings
    api_secret_key: str
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    
    class Config:
        env_file = "env/.env"
```

### Database Integration
Leverage existing database initialization:
```python
@app.on_event("startup")
async def startup():
    # Use existing DatabaseInitializer
    from genonaut.db.init import DatabaseInitializer
    initializer = DatabaseInitializer()
    initializer.create_engine_and_session()
```

### Testing Strategy
Build on existing test infrastructure:
```python
# Use existing test utilities + FastAPI TestClient
def test_recommendations_endpoint(test_client, test_session):
    from test.utils import seed_database_from_tsv
    seed_database_from_tsv(test_session)
    
    response = test_client.get("/api/v1/users/1/recommendations")
    assert response.status_code == 200
```

## Tech Stack

**Core Libraries:**
- `fastapi` - Main web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation and serialization
- `python-multipart` - File upload support

**Database & Existing Integration:**
- `sqlalchemy` (existing) - Database ORM
- `asyncpg` - Async PostgreSQL driver (for FastAPI async support)

**Development & Testing:**
- `pytest-asyncio` - Async testing support
- `httpx` - HTTP client for testing
- `pytest-mock` - Mocking support

**Additional FastAPI Features:**
- Built-in OpenAPI/Swagger documentation
- Automatic request/response validation
- Dependency injection system
- Background task support
- WebSocket support

## Future Possibilities

The following features are identified for potential future implementation but are not included in the initial scope:

- **Redis for caching recommendations** - High-performance caching layer for frequently accessed recommendations
- **Celery for heavy ML background tasks** - Distributed task queue for compute-intensive operations
- **Strawberry GraphQL for complex queries** - Alternative query language for complex, nested data requirements

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] **Setup FastAPI Application**
  - [ ] Create `genonaut/api/main.py` with basic FastAPI app
  - [ ] Add FastAPI dependencies to `requirements-unlocked.txt`
  - [ ] Create basic project structure under `genonaut/api/`
  - [ ] Setup CORS middleware and basic security headers

- [ ] **Database Integration**
  - [ ] Create `genonaut/api/dependencies.py` for database session injection
  - [ ] Implement multi-schema session providers (app/demo/test)
  - [ ] Add async PostgreSQL support (`asyncpg`)
  - [ ] Test database connectivity with existing models

- [ ] **Configuration Management**
  - [ ] Extend settings system to include API configuration
  - [ ] Update `.env.example` with new API variables
  - [ ] Create `genonaut/api/config.py` for settings management

### Phase 2: Repository Layer
- [ ] **Base Repository Pattern**
  - [ ] Create `genonaut/api/repositories/base.py` with generic repository
  - [ ] Implement common CRUD operations using existing SQLAlchemy models
  - [ ] Add proper error handling and logging

- [ ] **Specific Repositories**
  - [ ] Implement `UserRepository` with JSONB preference queries
  - [ ] Implement `ContentRepository` with metadata filtering
  - [ ] Implement `InteractionRepository` for tracking user behavior
  - [ ] Implement `RecommendationRepository` for recommendation management
  - [ ] Implement `GenerationJobRepository` for job status tracking

### Phase 3: Service Layer
- [ ] **Business Logic Services**
  - [ ] Create `UserService` for user management operations
  - [ ] Create `ContentService` for content CRUD and validation
  - [ ] Create `InteractionService` for behavior tracking
  - [ ] Create `RecommendationService` for recommendation logic
  - [ ] Create `GenerationService` for content generation workflow

- [ ] **Service Integration**
  - [ ] Add proper exception handling across services
  - [ ] Implement transaction management for multi-table operations
  - [ ] Add logging and monitoring hooks

### Phase 4: API Models (Pydantic)
- [ ] **Request Models**
  - [ ] User creation/update models
  - [ ] Content creation/update models
  - [ ] Interaction recording models
  - [ ] Recommendation request models
  - [ ] Generation job models

- [ ] **Response Models**
  - [ ] User profile response models
  - [ ] Content list/detail response models
  - [ ] Recommendation response models
  - [ ] Generation job status models
  - [ ] Error response models

- [ ] **Validation & Enums**
  - [ ] Content type enums
  - [ ] Interaction type enums
  - [ ] Job status enums
  - [ ] Custom validators for business rules

### Phase 5: API Routes
- [ ] **User Management Routes**
  - [ ] `GET /api/v1/users/{id}` - Get user profile
  - [ ] `PUT /api/v1/users/{id}` - Update user profile
  - [ ] `PUT /api/v1/users/{id}/preferences` - Update preferences
  - [ ] `GET /api/v1/users/{id}/interactions` - Get interaction history

- [ ] **Content Management Routes**
  - [ ] `GET /api/v1/content` - List content with filtering
  - [ ] `POST /api/v1/content` - Create new content
  - [ ] `GET /api/v1/content/{id}` - Get content details
  - [ ] `PUT /api/v1/content/{id}` - Update content
  - [ ] `DELETE /api/v1/content/{id}` - Delete content

- [ ] **Recommendation Routes**
  - [ ] `GET /api/v1/users/{id}/recommendations` - Get user recommendations
  - [ ] `POST /api/v1/recommendations/generate` - Generate recommendations
  - [ ] `PUT /api/v1/recommendations/{id}/feedback` - Record feedback

- [ ] **Interaction Routes**
  - [ ] `POST /api/v1/interactions` - Record interaction
  - [ ] `GET /api/v1/interactions/{id}` - Get interaction details

- [ ] **Generation Job Routes**
  - [ ] `POST /api/v1/generation-jobs` - Create generation job
  - [ ] `GET /api/v1/generation-jobs/{id}` - Get job status
  - [ ] `GET /api/v1/generation-jobs` - List jobs with filtering

### Phase 6: Advanced Features
- [ ] **WebSocket Support**
  - [ ] Implement WebSocket endpoint for generation job updates
  - [ ] Add real-time notification system
  - [ ] Handle WebSocket connection management

- [ ] **Background Tasks**
  - [ ] Implement FastAPI background tasks for generation jobs
  - [ ] Add job queue management
  - [ ] Implement job status polling and updates

- [ ] **System Endpoints**
  - [ ] `GET /health` - Health check with database connectivity
  - [ ] `GET /api/v1/schemas` - Schema information endpoint
  - [ ] Add metrics and monitoring endpoints

### Phase 7: Testing
- [ ] **Unit Tests**
  - [ ] Test all repository methods
  - [ ] Test all service layer methods
  - [ ] Test Pydantic model validation
  - [ ] Test database session management

- [ ] **Integration Tests**
  - [ ] Test API endpoints with FastAPI TestClient
  - [ ] Test multi-schema database operations
  - [ ] Test WebSocket functionality
  - [ ] Test background task execution

- [ ] **End-to-End Tests**
  - [ ] Test complete user workflows
  - [ ] Test recommendation generation pipeline
  - [ ] Test content generation workflow
  - [ ] Test error handling scenarios

### Phase 8: Documentation & Deployment
- [ ] **API Documentation**
  - [ ] Configure OpenAPI/Swagger documentation
  - [ ] Add detailed endpoint descriptions
  - [ ] Include example requests/responses
  - [ ] Document authentication requirements

- [ ] **Development Setup**
  - [ ] Create development server startup script
  - [ ] Add API server to Makefile
  - [ ] Update README with API setup instructions
  - [ ] Create API usage examples

- [ ] **Deployment Preparation**
  - [ ] Add production ASGI server configuration
  - [ ] Configure logging for production
  - [ ] Add environment-specific settings
  - [ ] Create deployment documentation

### Phase 9: Security & Production Readiness
- [ ] **Security Implementation**
  - [ ] Add API key authentication
  - [ ] Implement rate limiting
  - [ ] Add input sanitization
  - [ ] Configure security headers

- [ ] **Production Features**
  - [ ] Add comprehensive error handling
  - [ ] Implement proper logging
  - [ ] Add health check endpoints
  - [ ] Configure monitoring hooks

- [ ] **Performance Optimization**
  - [ ] Add database query optimization
  - [ ] Implement response caching where appropriate
  - [ ] Add async/await optimization
  - [ ] Performance testing and tuning

### Success Criteria
- [ ] All API endpoints functional and tested
- [ ] Full integration with existing database models
- [ ] Comprehensive test coverage (>90%)
- [ ] Production-ready with proper error handling
- [ ] Complete API documentation
- [ ] Multi-schema support working correctly
- [ ] WebSocket real-time updates functional
- [ ] Background task processing working
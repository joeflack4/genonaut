# Infrastructure

## Application overview: Major components

Genonaut is a multi-tier application consisting of several interconnected services that work together to provide content generation, recommendation, and management capabilities.

### Core Components

#### 1. PostgreSQL Database
**Purpose:** Persistent data storage for all application data

**Key responsibilities:**
- Stores users, content items (both regular and auto-generated), tags, interactions, ratings
- Maintains tag hierarchy and relationships via `tag_parents` table
- Tracks content-tag associations in the `content_tags` junction table
- Stores tag cardinality statistics for performance optimization

**Connection:** All backend services connect to PostgreSQL for data persistence

**Configuration:** See `docs/db.md` for schema details and performance optimizations

---

#### 2. Redis
**Purpose:** In-memory data store for caching and message brokering

**Key responsibilities:**
- **Cache layer:** Query result caching (planned for Proposal 2)
- **Message broker:** Celery task queue for asynchronous job processing
- **Session storage:** User session data (if implemented)

**Connection:**
- Backend API connects for caching
- Celery workers connect for task queue management

**Port:** 6379 (default)

---

#### 3. Web API (FastAPI)
**Purpose:** RESTful API server providing all backend functionality

**Key responsibilities:**
- Exposes 77+ REST endpoints for content, tags, users, interactions, recommendations
- Handles authentication and authorization
- Processes business logic and data validation
- Coordinates with Celery for async tasks (image generation, scheduled jobs)

**Technology:** FastAPI (Python), Uvicorn server

**Port:** 8001 (default for local development)

**Startup:** `make api-demo` (uses demo database)

**Documentation:** See `docs/api.md` for endpoint details and `http://localhost:8001/docs` for interactive API docs

---

#### 4. Celery Workers
**Purpose:** Asynchronous task processing and scheduled jobs

**Key responsibilities:**
- **Image generation:** Communicates with ComfyUI to generate images based on user prompts
- **Scheduled jobs:**
  - `refresh_tag_cardinality_stats` - Daily task to update tag popularity statistics
  - Other periodic maintenance tasks
- **WebSocket notifications:** Real-time updates for job status

**Technology:** Celery (Python), Redis as broker

**Startup:** `make celery-dev` (or `celery-demo`, `celery-test`)

**Monitoring:** Flower UI at `http://localhost:5555` (via `make flower-dev`)

**Tasks location:** `genonaut/worker/tasks.py`

---

#### 5. Image Generation Server
**Purpose:** Stable Diffusion image generation backend

**Options:**
- **ComfyUI** (production) - Full-featured Stable Diffusion UI with workflow support
- **ComfyUI Mock** (development/testing) - Simulated image generation for faster dev cycles
- **Future:** Automatic1111 or other Stable Diffusion backends

**Key responsibilities:**
- Receives generation requests from Celery workers via HTTP API
- Executes Stable Diffusion workflows to generate images
- Returns generated images to be stored in content database

**Port:** 8189 (ComfyUI default)

**Communication:** Celery workers make HTTP requests to ComfyUI API endpoints

**Configuration:** See `config/base.json` for ComfyUI settings

---

#### 6. Frontend (React SPA)
**Purpose:** User interface for the application

**Key responsibilities:**
- Gallery views for browsing generated and user-created content
- Tag management and hierarchical browsing
- Content creation and generation workflows
- User interactions (ratings, favorites, searches)

**Technology:** React, Vite, TypeScript, Material-UI

**Port:** 5173 (Vite dev server default)

**Startup:** `make frontend-dev` or `npm --prefix frontend run dev`

**Build:** `make frontend-build` creates production static assets

**Documentation:** See `frontend/AGENTS.md` for frontend-specific details

---

### System Architecture Diagram

```
┌─────────────────┐
│  Frontend (SPA) │  Port 5173
│   React + Vite  │
└────────┬────────┘
         │ HTTP API
         ▼
┌─────────────────┐
│   Web API       │  Port 8001
│   (FastAPI)     │
└────┬────────┬───┘
     │        │
     │        └──────────────┐
     │                       │
     ▼                       ▼
┌─────────────┐      ┌──────────────┐
│  PostgreSQL │      │    Redis     │  Port 6379
│  Database   │      │ (Cache+Queue)│
└─────────────┘      └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │Celery Workers│
                     └──────┬───────┘
                            │ HTTP
                            ▼
                     ┌──────────────┐
                     │   ComfyUI    │  Port 8189
                     │ (Image Gen)  │
                     └──────────────┘
```

### Data Flow Examples

**Content Generation Workflow:**
1. User submits generation request via Frontend
2. Frontend sends POST to `/api/v1/generation-jobs` (Web API)
3. Web API creates job record in PostgreSQL, enqueues Celery task
4. Celery worker picks up task from Redis queue
5. Celery worker sends HTTP request to ComfyUI with prompt/parameters
6. ComfyUI generates image, returns to Celery worker
7. Celery worker stores image, updates job status in PostgreSQL
8. WebSocket notification sent to Frontend about job completion

**Tag Popularity Aggregation:**
1. Celery scheduled task `refresh_tag_cardinality_stats` runs daily
2. Task queries `content_tags` table, computes cardinalities
3. Results written to `tag_cardinality_stats` table in PostgreSQL
4. Frontend/API queries `/api/v1/tags/popular` for fast results
5. API reads pre-computed stats from `tag_cardinality_stats` (no expensive joins)

### Local Development Setup

All components should be running during development:

```bash
# Terminal 1: Database (should already be running)
# PostgreSQL via Postgres.app or brew services

# Terminal 2: Redis
make redis-dev

# Terminal 3: API server
make api-demo

# Terminal 4: Celery worker
make celery-dev

# Terminal 5: (Optional) Celery monitoring
make flower-dev

# Terminal 6: Image generation (choose one)
# Option A: Mock (fast, for development)
make comfyui-mock-dev

# Option B: Real ComfyUI (slower, for testing actual generation)
# Start ComfyUI separately

# Terminal 7: Frontend
make frontend-dev
```

See `CLAUDE.md` for detailed setup instructions and `Makefile` for all available commands.

## `infra/` directory: Terraform setup

This document provides an overview of the Terraform infrastructure setup in the `infra/` directory.

### Directory Structure

The `infra/` directory is organized into two main parts: `bootstrap` and `main`.

```
infra/
├── bootstrap/
│   ├── main.tf
│   ├── outputs.tf
│   ├── variables.tf
│   └── versions.tf
└── main/
    ├── backend.hcl
    ├── provider.tf
    ├── versions.tf
    └── vpc.tf
```

#### `infra/bootstrap`

This directory contains the Terraform code to set up the backend for Terraform itself. This is a one-time setup.

- `main.tf`: Defines the AWS resources for the Terraform backend, including an S3 bucket for state storage and a DynamoDB table for state locking.
- `variables.tf`: Declares variables used in the bootstrap configuration, such as the AWS region, S3 bucket name, and DynamoDB table name.
- `outputs.tf`: Defines the outputs of the bootstrap process, such as the names of the created S3 bucket and DynamoDB table.
- `versions.tf`: Specifies the required versions of Terraform and the AWS provider.

#### `infra/main`

This directory contains the main infrastructure code for the application.

- `versions.tf`: Specifies the required versions of Terraform and the AWS provider, and configures the S3 backend.
- `backend.hcl`: Contains the configuration for the Terraform S3 backend, specifying the bucket, key, region, and DynamoDB table for state locking.
- `provider.tf`: Configures the AWS provider, specifying the region.
- `vpc.tf`: An example file for defining the VPC and other network-related resources.

### Makefile Commands

The following `make` commands are available for managing the infrastructure:

- `aws-login`: Use if you have invalid credentials error when running terraform commands.
- `tf-bootstrap-init`: Initializes the Terraform bootstrap directory.
- `tf-bootstrap-apply`: Applies the Terraform bootstrap configuration.
- `tf-bootstrap-destroy`: Destroys the Terraform bootstrap resources.
- `tf-init`: Initializes the main Terraform directory.
- `tf-plan`: Creates a plan for the main Terraform infrastructure.
- `tf-apply`: Applies the main Terraform infrastructure changes.
- `tf-destroy`: Destroys the main Terraform infrastructure.
- `tf-fmt`: Formats the Terraform code in the main directory.
- `tf-validate`: Validates the Terraform code in the main directory.
- `tf-console`: Opens the Terraform console for the main directory.

### Environment Variables

The following environment variables must be set for the Makefile commands to work correctly.

They're best put by default in `env/.env.shared`. But further customizability can be done. You can read more about that in: [./configuration.md](./configuration.md)

#### AWS
- `DEPLOY_AWS_REGION`: The AWS region to deploy the infrastructure in.
- `DEPLOY_AWS_PROFILE`: The AWS profile to use for authentication.

#### Terraform
- `DEPLOY_TF_STATE_BUCKET_NAME`: The name of the S3 bucket for Terraform state.
- `DEPLOY_TF_DYNAMO_DB_TABLE`: The name of the DynamoDB table for Terraform state locking.

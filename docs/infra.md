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


## Deployment
### How to Deploy the Frontend (Static Site to AWS)

This guide explains how to deploy the Genonaut React/Vite frontend to AWS using S3 and CloudFront.

#### Overview

The frontend deployment process:
1. Builds the React/Vite app into static files
2. Uploads files to S3 bucket
3. Serves files globally via CloudFront CDN
4. Invalidates CloudFront cache to show latest changes

#### Prerequisites

##### 1. AWS Infrastructure

The Terraform infrastructure must be applied for the target environment first:

```bash
### Example for demo environment
make tf-init-demo
make tf-apply-demo
```

This creates:
- S3 bucket: `genonaut-{env}-static-site`
- CloudFront distribution with Origin Access Control (OAC)
- Appropriate IAM policies for secure access

##### 2. AWS Credentials

Ensure AWS credentials are configured:

```bash
### Login with SSO (if using AWS SSO)
make aws-login

### Verify credentials
aws sts get-caller-identity
```

##### 3. Node.js and npm

The frontend build requires Node.js and npm:

```bash
### Check if installed
node --version
npm --version
```

#### Deployment Commands

Deploy to specific environments using Make targets:

```bash
### Deploy to demo (most common)
make frontend-deploy-demo

### Deploy to dev
make frontend-deploy-dev

### Deploy to test
make frontend-deploy-test

### Deploy to production
make frontend-deploy-prod
```

#### What Happens During Deployment

The deployment script (`infra/scripts/frontend_deploy.sh`) performs these steps:

##### 1. Build Frontend
```bash
cd frontend
npm install  # If node_modules doesn't exist
npm run build
```

Output directory: `frontend/dist/`

##### 2. Retrieve Terraform Outputs
```bash
cd infra/main
terraform output -raw static_site_bucket_name
terraform output -raw static_site_cloudfront_domain
terraform output -raw static_site_cloudfront_distribution_id
```

##### 3. Sync to S3

The script uploads files with appropriate caching headers:

- `index.html`: Short cache (5 minutes)
  - Allows quick updates to the app shell
- Assets (JS, CSS, images): Long cache (1 year)
  - Vite generates content-hashed filenames, so safe to cache forever

```bash
### Upload index.html with short cache
aws s3 cp dist/index.html s3://genonaut-{env}-static-site/index.html \
  --cache-control "public, max-age=300"

### Upload all other files with long cache
aws s3 sync dist/ s3://genonaut-{env}-static-site/ \
  --delete \
  --exclude "index.html" \
  --cache-control "public, max-age=31536000, immutable"
```

##### 4. Invalidate CloudFront Cache

```bash
aws cloudfront create-invalidation \
  --distribution-id {DISTRIBUTION_ID} \
  --paths "/*"
```

Cache invalidation typically completes within 2-5 minutes.

#### Accessing the Deployed Site

After deployment, the script outputs the CloudFront URL:

```
Deployment Summary:
  Environment: demo
  S3 Bucket: genonaut-demo-static-site
  CloudFront URL: https://d1234567890abc.cloudfront.net

Your frontend is now live at:
  https://d1234567890abc.cloudfront.net
```

You can also retrieve the URL anytime:

```bash
cd infra/main
terraform output static_site_cloudfront_domain
```

#### Troubleshooting

##### Error: "Terraform not initialized"

**Solution**: Initialize Terraform for the environment:
```bash
make tf-init-demo  # or dev/test/prod
```

##### Error: "Could not retrieve S3 bucket name"

**Solution**: Apply Terraform infrastructure first:
```bash
make tf-apply-demo  # or dev/test/prod
```

##### Error: "AWS credentials not configured"

**Solution**: Login to AWS:
```bash
make aws-login
### Or set up credentials manually
aws configure
```

##### Changes not appearing on CloudFront

**Possible causes**:

1. **Cache invalidation in progress**: Wait 2-5 minutes for invalidation to complete
2. **Browser cache**: Hard refresh in browser (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
3. **CloudFront propagation**: May take up to 15 minutes for changes to propagate globally

**Check invalidation status**:
```bash
aws cloudfront list-invalidations --distribution-id {DISTRIBUTION_ID}
```

##### Build fails with TypeScript errors

**Solution**: Fix TypeScript errors before deploying:
```bash
cd frontend
npm run type-check  # See errors
### Fix errors in code
npm run build       # Try again
```

#### Environment-Specific Notes

##### Demo Environment
- Most commonly used for testing and demonstrations
- Bucket: `genonaut-demo-static-site`
- Terraform: `make tf-apply-demo`
- Deploy: `make frontend-deploy-demo`

##### Production Environment
- Use with caution - this is the live site
- Bucket: `genonaut-prod-static-site`
- Terraform: `make tf-apply-prod`
- Deploy: `make frontend-deploy-prod`
- Consider testing in demo first

#### Manual Deployment Steps

If you need to deploy manually without the Make target:

```bash
### 1. Build
cd frontend
npm install
npm run build

### 2. Get bucket name
cd ../infra/main
BUCKET=$(terraform output -raw static_site_bucket_name)
DIST_ID=$(terraform output -raw static_site_cloudfront_distribution_id)

### 3. Upload to S3
aws s3 cp ../frontend/dist/index.html s3://$BUCKET/index.html \
  --cache-control "public, max-age=300"
aws s3 sync ../frontend/dist/ s3://$BUCKET/ \
  --delete --exclude "index.html" \
  --cache-control "public, max-age=31536000, immutable"

### 4. Invalidate cache
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

#### Architecture Details

##### S3 Bucket Configuration
- Private bucket (no public access)
- CloudFront OAC (Origin Access Control) for secure access
- No static website hosting mode needed (CloudFront handles routing)

##### CloudFront Distribution
- Uses AWS managed cache policy: "CachingOptimized"
- Enforces HTTPS (redirects HTTP to HTTPS)
- Price class: PriceClass_100 (US + Europe for cost efficiency)
- Default root object: `index.html`

##### Frontend Build Output
- Single-page application (SPA)
- All routes handled by `index.html`
- Assets have content hashes in filenames (e.g., `main.abc123.js`)
- Production optimizations: minification, tree-shaking, code splitting

#### Next Steps

After deploying the frontend, you may want to:

1. **Set up custom domain**: Configure Route 53 and ACM certificate
2. **Add monitoring**: Set up CloudWatch alarms for 4xx/5xx errors
3. **Configure CI/CD**: Automate deployments via GitHub Actions
4. **Add environment variables**: Configure API endpoints for different environments

#### Related Documentation

- [Terraform Infrastructure](../infra/main/s3_cloudfront.tf)
- [Frontend Development](../frontend/README.md)
- [API Configuration](./api.md)
- [Testing Guide](./testing.md)

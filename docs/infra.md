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

#### Related Documentation

- [Terraform Infrastructure](../infra/main/s3_cloudfront.tf)
- [Frontend Development](../frontend/README.md)
- [API Configuration](./api.md)
- [Testing Guide](./testing.md)

---

### How to Deploy the Backend (ECS Services to AWS)

This guide explains how to deploy the Genonaut backend services (API, Celery workers, Image Gen Mock) to AWS ECS using 
Docker containers.

#### Overview

The backend deployment process:
1. Builds a Docker image containing the entire `genonaut` Python package
2. Pushes the image to AWS ECR (Elastic Container Registry)
3. ECS services pull the new image and restart containers
4. Same image is used for all three services (API, Celery, Image Gen Mock)

#### Prerequisites

##### 1. AWS Infrastructure

The Terraform infrastructure must be applied for the target environment first:

```bash
# Example for demo environment
make tf-init-demo
make tf-apply-demo
```

This creates:
- ECR repositories: `genonaut-api-{env}`, `genonaut-worker-{env}`, `genonaut-imagegen-{env}`
- ECS cluster, services, task definitions
- ALB (Application Load Balancer) for API and Image Gen services
- RDS PostgreSQL and ElastiCache Redis instances
- VPC, subnets, security groups, IAM roles

##### 2. AWS Credentials

Ensure AWS credentials are configured:

```bash
# Login with SSO (if using AWS SSO)
make aws-login

# Verify credentials
aws sts get-caller-identity
```

##### 3. Docker

Docker must be installed and running:

```bash
# Check if installed
docker --version

# Verify Docker daemon is running
docker ps
```

#### Deployment Commands

Deploy backend services to specific environments using Make targets:

```bash
# Build Docker image locally (optional - mainly for testing)
make backend-build

# Deploy to demo (most common)
make backend-deploy-demo

# Deploy to dev
make backend-deploy-dev

# Deploy to test
make backend-deploy-test

# Deploy to production
make backend-deploy-prod
```

#### What Happens During Deployment

The deployment script (`infra/scripts/backend_deploy.sh`) performs these steps:

##### 1. Build Docker Image

```bash
docker build -t genonaut:latest .
```

The `Dockerfile` at project root:
- Uses Python 3.11 slim base image
- Installs system dependencies (gcc, g++, libpq-dev for psycopg2)
- Installs Python dependencies from `requirements.txt`
- Copies entire codebase
- Installs `genonaut` package: `pip install -e .`

This makes the `genonaut` package and all its modules importable, which is required for:
- `genonaut.api.main:app` (FastAPI application)
- `genonaut.worker.queue_app:celery_app` (Celery application)
- `test._infra.mock_services.comfyui.server:app` (Mock image gen API)

##### 2. Tag Image for Each ECR Repository

```bash
# Tag for API
docker tag genonaut:latest <ECR_URL>/genonaut-api-demo:latest

# Tag for Worker
docker tag genonaut:latest <ECR_URL>/genonaut-worker-demo:latest

# Tag for Image Gen Mock
docker tag genonaut:latest <ECR_URL>/genonaut-imagegen-demo:latest
```

We push the same image to all three repositories because all services use the same codebase. The service type is determined by the `command` override in the ECS task definition.

##### 3. Authenticate to ECR

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ECR_URL>
```

##### 4. Push Images to ECR

```bash
docker push <ECR_URL>/genonaut-api-demo:latest
docker push <ECR_URL>/genonaut-worker-demo:latest
docker push <ECR_URL>/genonaut-imagegen-demo:latest
```

##### 5. Force ECS Service Updates

```bash
aws ecs update-service --cluster genonaut-demo \
  --service genonaut-api-demo --force-new-deployment

aws ecs update-service --cluster genonaut-demo \
  --service genonaut-celery-demo --force-new-deployment

aws ecs update-service --cluster genonaut-demo \
  --service genonaut-image-gen-demo --force-new-deployment
```

This tells ECS to:
- Stop existing tasks
- Pull the latest image from ECR (with `:latest` tag)
- Start new tasks with the updated image

##### 6. Deployment Summary

The script outputs:
```
Deployment Summary:
  Environment: demo
  Image Tag: latest
  API Service: genonaut-api-demo
  Celery Service: genonaut-celery-demo
  Image Gen Service: genonaut-image-gen-demo

ECS services are updating. This may take 2-5 minutes.

Check service status:
  make ecs-status-demo
```

#### How ECS Task Definitions Use the Image

The same Docker image is used by all three services, but each runs a different command:

**API Service** (in `infra/main/services.tf`):
```hcl
command = [
  "uvicorn",
  "genonaut.api.main:app",
  "--host", "0.0.0.0",
  "--port", "8001"
]
```

**Celery Worker Service**:
```hcl
command = [
  "celery",
  "-A", "genonaut.worker.queue_app:celery_app",
  "worker",
  "--loglevel=info",
  "--queues=default,generation",
  "-B",
  "--scheduler", "redbeat.RedBeatScheduler"
]
```

**Image Gen Mock API Service**:
```hcl
command = [
  "uvicorn",
  "test._infra.mock_services.comfyui.server:app",
  "--host", "0.0.0.0",
  "--port", "8189"
]
```

This single-image, multiple-command approach simplifies deployment:
- One build, one push (faster CI/CD)
- Consistent dependencies across services
- Easier maintenance (update once, applies everywhere)
- Can split into separate images later if services diverge

#### CI/CD Strategy

**Current State (Manual Deployment):**

Right now, deployment is manual. You run:
```bash
make backend-deploy-demo
```

This:
1. Builds Docker image on your local machine
2. Pushes to ECR from your local machine
3. Updates ECS services from your local machine

**Future State (Automated CI/CD with GitHub Actions):**

The plan is to automate this using GitHub Actions. Drafts and finalized versions of the workflows can be found in:
`.github/`

**What happens automatically vs. manually:**

| Action | Manual (Now) | Automated (Future) |
|--------|--------------|-------------------|
| Code pushed to `main` | No action | GitHub Actions builds & deploys to demo |
| Code pushed to `production` | No action | GitHub Actions builds & deploys to prod |
| Infrastructure changes | Run `make tf-apply-demo` | Still manual (Terraform best kept manual/reviewed) |
| Emergency rollback | Run `make backend-deploy-demo` with old commit | Revert Git commit, push triggers auto-deploy |
| Check deployment status | Run `make ecs-status-demo` | Check GitHub Actions logs |

**When to use manual vs. automated:**

**Manual deployment (now):**
- During initial development and testing
- When testing infrastructure changes
- When you want full control over timing
- For hotfixes that need immediate attention

**Automated deployment (future):**
- Regular feature deployments to demo
- Scheduled releases to production
- Post-merge deployments (merge to main = deploy to demo)
- Reduces human error
- Faster deployment cycles

**Important Note:** Even with CI/CD automation, you'll still use the same deployment script (`infra/scripts/backend_deploy.sh`). The only difference is *who* runs it (you vs. GitHub Actions).

#### Deployment Workflow Summary

**Complete deployment workflow (manual, current approach):**

```bash
# 1. Make code changes
git add .
git commit -m "Add new feature"

# 2. Ensure infrastructure is up to date (if Terraform changed)
make tf-apply-demo

# 3. Deploy backend services
make backend-deploy-demo

# 4. Verify deployment
make ecs-status-demo

# 5. Check logs if issues
make ecs-logs-api-demo
```

**Time estimates:**
- Docker build: 2-5 minutes (first build), ~30 seconds (cached)
- Push to ECR: 1-2 minutes
- ECS service update: 2-5 minutes
- **Total: ~5-10 minutes for full deployment**

#### Accessing the Deployed Services

After deployment:

**API Service:**
```bash
# Get ALB URL from Terraform
cd infra/main
terraform output alb_dns_name

# Access API
curl https://<ALB_URL>/api/v1/health
```

**Celery Worker:**
- No direct HTTP access (internal only)
- Monitor via Flower UI (if deployed)
- Check CloudWatch logs: `make ecs-logs-celery-demo`

**Image Gen Mock API:**
```bash
# Access via ALB (routed to /image-gen)
curl https://<ALB_URL>/image-gen/health
```

#### Troubleshooting

##### Error: "Docker daemon not running"

**Solution**: Start Docker Desktop or Docker daemon:
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
```

##### Error: "Unable to locate credentials"

**Solution**: Login to AWS:
```bash
make aws-login
# Or set up credentials manually
aws configure
```

##### Error: "ECR repository does not exist"

**Solution**: Apply Terraform infrastructure first:
```bash
make tf-apply-demo
```

##### ECS Service Fails to Start

**Check task definition**:
```bash
# Get latest task definition
aws ecs describe-task-definition --task-definition genonaut-api-demo

# Check recent tasks
aws ecs list-tasks --cluster genonaut-demo --service genonaut-api-demo
```

**Common issues:**
1. **Environment variables missing**: Check ECS secrets configuration in `infra/main/ecs_secrets.auto.tf`
2. **Image pull error**: Verify ECR repository exists and image was pushed successfully
3. **Port conflicts**: Ensure container ports match ALB target group ports
4. **Database connection failure**: Check security group rules allow ECS to reach RDS

**View logs**:
```bash
make ecs-logs-api-demo
make ecs-logs-celery-demo
make ecs-logs-imagegen-demo
```

##### Docker Build is Slow (25GB+ image)

The image might be large due to including unnecessary files.

**Solution**: Optimize `.dockerignore`:
```bash
# Add to .dockerignore
frontend/node_modules
.git
*.log
*.pyc
__pycache__
.pytest_cache
.vscode
```

**Rebuild**:
```bash
docker build -t genonaut:test .
```

Expected final image size: ~1-2GB (not 25GB)

##### ECS Service Update Stuck

**Check service events**:
```bash
aws ecs describe-services --cluster genonaut-demo \
  --services genonaut-api-demo \
  --query 'services[0].events[0:5]'
```

**Force restart**:
```bash
aws ecs update-service --cluster genonaut-demo \
  --service genonaut-api-demo \
  --force-new-deployment
```

#### Environment-Specific Notes

##### Demo Environment
- Most commonly used for testing and demonstrations
- ECR repos: `genonaut-api-demo`, `genonaut-worker-demo`, `genonaut-imagegen-demo`
- ECS cluster: `genonaut-demo`
- Terraform: `make tf-apply-demo`
- Deploy: `make backend-deploy-demo`

##### Production Environment
- Use with caution - this is the live site
- ECR repos: `genonaut-api-prod`, `genonaut-worker-prod`, `genonaut-imagegen-prod`
- ECS cluster: `genonaut-prod`
- Terraform: `make tf-apply-prod`
- Deploy: `make backend-deploy-prod`
- **Best practice:** Test in demo first, then deploy to prod

#### Docker Image Location

After building locally, the image is stored in Docker's local image storage:

```bash
# View local images
docker images | grep genonaut

# Example output:
# genonaut     latest    7de1e6a2d37f   13 minutes ago   1.2GB
```

**Local image locations:**
- macOS: `~/Library/Containers/com.docker.docker/Data/`
- Linux: `/var/lib/docker/`
- Windows: `C:\ProgramData\Docker\`

**ECR image locations (after push):**
- `<AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/genonaut-api-demo:latest`
- `<AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/genonaut-worker-demo:latest`
- `<AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/genonaut-imagegen-demo:latest`

You can inspect images:
```bash
# Local image details
docker inspect genonaut:latest

# ECR image details
aws ecr describe-images --repository-name genonaut-api-demo
```

#### Manual Deployment Steps

If you need to deploy manually without the Make target:

```bash
# 1. Build image
docker build -t genonaut:latest .

# 2. Get ECR repository URLs
cd infra/main
ECR_API=$(terraform output -raw ecr_repo_api_url)
ECR_WORKER=$(terraform output -raw ecr_repo_worker_url)
ECR_IMAGEGEN=$(terraform output -raw ecr_repo_image_gen_url)

# 3. Tag images
docker tag genonaut:latest $ECR_API:latest
docker tag genonaut:latest $ECR_WORKER:latest
docker tag genonaut:latest $ECR_IMAGEGEN:latest

# 4. Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ECR_URL>

# 5. Push images
docker push $ECR_API:latest
docker push $ECR_WORKER:latest
docker push $ECR_IMAGEGEN:latest

# 6. Update ECS services
aws ecs update-service --cluster genonaut-demo \
  --service genonaut-api-demo --force-new-deployment
aws ecs update-service --cluster genonaut-demo \
  --service genonaut-celery-demo --force-new-deployment
aws ecs update-service --cluster genonaut-demo \
  --service genonaut-image-gen-demo --force-new-deployment
```

#### Related Documentation

- [Terraform ECS Services](../infra/main/services.tf)
- [Docker Configuration](../Dockerfile)
- [API Documentation](./api.md)
- [Celery Tasks](./queuing.md)
- [Frontend Deployment](#how-to-deploy-the-frontend-static-site-to-aws)

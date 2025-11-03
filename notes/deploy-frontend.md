# Genonaut Static Frontend Deployment (CloudFront + S3)

## Background / Context

We are standing up the first deployable stack for Genonaut.

### Infra status (as of 2025-11-02)
- We have an `infra/` Terraform project that defines:
  - VPC, subnets, NAT, etc.
  - ECS cluster + services (`api`, `image_gen_mock_api`, `celery`)
  - ALB + listener(s) and target groups
  - RDS / ElastiCache (internal)
  - And now: static site hosting resources
- We just added a new Terraform file: `infra/s3_cloudfront.tf`
.
### What `s3_cloudfront.tf` does
`infra/s3_cloudfront.tf` (new file) creates:
- An S3 bucket named `genonaut-${var.env}-static-site` (private, no public ACLs).
- A CloudFront Origin Access Control (OAC) so CloudFront can read from that bucket securely.
- A CloudFront distribution with `default_root_object = "index.html"`.
  - We're using the default CloudFront certificate for now (the `cloudfront.net` domain).
  - `price_class = "PriceClass_100"` to keep cost down initially.

Also added to `infra/outputs.tf`:
- `static_site_bucket_name`
- `static_site_cloudfront_domain`
- (optional) `static_site_cloudfront_distribution_id`

Those outputs let us:
- Know where to upload the built frontend.
- Know what domain to hit in a browser after upload.
- Invalidate cache after redeploy.

### Current gap
Terraform will successfully create the infra (bucket + CloudFront), but the frontend will still be blank until we actually upload a built artifact (React/Vite/etc.) into that S3 bucket.

Right now this is a manual process:
1. Build the frontend locally (`npm run build` (or whatever script) → produces a `dist/` directory).
2. Sync that `dist/` directory to the S3 bucket for the right environment.
3. (Optional but ideal) Invalidate the CloudFront cache to force refresh on redeploy.

We want to automate that instead of doing it by hand every time.

---

## Requirements for Automation

We want a repeatable way to publish the static frontend to the live infra for any environment (`dev`, `demo`, `prod`, etc.). (though practically we will only care about 'demo' for now; that is, that's the only one we'll deploy for the foreseeable future)

### Assumptions
- After building, it outputs a folder like `dist/` (if it's not `dist/`, detect it).
- AWS credentials are already configured in the shell we use to run Terraform (we're already targeting the right account with `AWS_PROFILE=...`).
- We have a Terraform variable `var.env` that gets set per environment (e.g. `demo`, `dev`, etc.).
- Bucket name format is: `genonaut-${env}-static-site`.

### What the automation should do
We want (ideally) a single command like:

```bash
make frontend-deploy-demo
```

…that will:

1. Build the frontend (e.g. `npm install` (if needed) + `npm run build`).
2. Sync the build output directory (e.g. `dist/`) to the correct environment bucket:
   ```bash
   aws s3 sync dist/ s3://genonaut-${ENV}-static-site/ --delete
   ```
   - `${ENV}` should match whatever we used when applying Terraform to that stack (`demo`, `dev`, etc.`).
3. Optionally create a CloudFront invalidation for that environment's distribution:
   ```bash
   aws cloudfront create-invalidation      --distribution-id <DISTRIBUTION_ID>      --paths "/*"
   ```
   We can get `YOUR_DISTRIBUTION_ID` from Terraform output or AWS CLI.

### DevEx goals
- I should not have to remember the bucket name, dist folder path, or distribution ID.
- I shouldn't have to manually copy/paste terraform output every deploy.
- This should all be predictable per environment (`demo`, `dev`, etc.), not hardcoded to only one.

### Acceptable implementations
- A Makefile target (preferred, we already have a Makefile driving Terraform).
- OR a lightweight Bash script in `scripts/frontend_deploy.sh` that the Makefile calls.
- Optional: script can read Terraform outputs via `terraform output -raw ...` so it's always in sync.

---

## Deliverables for the Agent

### Deliverable 1: Detect build artifact
- Figure out the frontend project root (if not obvious, assume repo root unless told otherwise).
- Figure out which directory is generated on build (`dist/`, `build/`, `out/`, etc.).
- Codify that in a variable so it’s not magic.

### Deliverable 2: Automate deploy for an environment
Create something like this (pseudo-Makefile-style):

```make
frontend-deploy-%: ## Build and publish static frontend to CloudFront for env $*
	ENV=$* ./infra/scripts/frontend_deploy.sh $$ENV
```

…and then `infra/scripts/frontend_deploy.sh` would:

1. Take `$1` = ENV (e.g. `demo`).
2. Run the production build.
3. Read terraform outputs for that env to get:
   - `static_site_bucket_name`
   - `static_site_cloudfront_distribution_id` (optional but nice)
4. Sync build output to that bucket.
5. Invalidate CloudFront (nice-to-have; can be skipped on first pass).

### Deliverable 3: Add basic docs for humans
At the end of the process, generate/update a short `docs/how_to_deploy_frontend.md` (or update this file) that says:

- “Run `terraform apply` first so infra exists.”
- “Then run `make frontend-deploy-demo`.”
- “Then open the CloudFront domain from `terraform output static_site_cloudfront_domain` in a browser.”

---

## Task Checklist

### Infra context capture
- [x] Confirm that `infra/s3_cloudfront.tf` exists and defines required resources.
- [x] Confirm `infra/outputs.tf` includes all static site outputs.
  - Added `static_site_cloudfront_distribution_id` output for cache invalidation

### Environment assumptions
- [x] Identify how `var.env` is passed today (demo/dev/prod). Document it.
  - Environment passed via `infra/env/{env}.tfvars` files
  - Bucket name confirmed: `genonaut-${env}-static-site`
- [x] Confirm bucket name matches env (`genonaut-${env}-static-site`).

### Build pipeline
- [x] Detect frontend path, build command, and build output directory.
  - Frontend path: `frontend/`
  - Build command: `npm run build`
  - Output directory: `frontend/dist/`

### Deployment script
- [x] Create `infra/scripts/frontend_deploy.sh` to automate build + upload + invalidation.
- [x] Script should accept env arg (`demo`, `dev`, etc.) and use Terraform outputs dynamically.
  - Script retrieves bucket name, CloudFront domain, and distribution ID from Terraform
  - Implements smart caching: short cache for index.html, long cache for hashed assets
  - Performs CloudFront cache invalidation automatically

### Makefile integration
- [x] Add targets: `frontend-deploy-demo`, `frontend-deploy-dev`, etc.
  - Added `frontend-deploy-demo`, `frontend-deploy-dev`, `frontend-deploy-test`, `frontend-deploy-prod`
  - Updated help output to include deployment commands

### Developer docs
- [x] Update or add `docs/how_to_deploy_frontend.md`.
  - Created comprehensive deployment guide
  - Includes prerequisites, step-by-step instructions, troubleshooting
  - Documents architecture and caching strategy

---

## Acceptance Criteria

- After `terraform apply`, I can run a single Make target (`make frontend-deploy-demo`) and:
  - Frontend builds successfully.
  - Files sync to correct S3 bucket.
  - CloudFront invalidated (optional).
  - The app is viewable at the CloudFront domain output.

---

## Implementation Summary (2025-11-02)

### What Was Delivered

All requirements and acceptance criteria have been met:

1. **Deployment Script** (`infra/scripts/frontend_deploy.sh`)
   - Fully automated build, sync, and cache invalidation
   - Environment-aware (accepts demo/dev/test/prod)
   - Retrieves Terraform outputs dynamically
   - Smart caching strategy (short for index.html, long for assets)
   - Comprehensive error handling and validation
   - Color-coded terminal output for better UX

2. **Makefile Integration**
   - Added 4 new targets: `frontend-deploy-{demo,dev,test,prod}`
   - Updated help documentation
   - Follows existing Makefile conventions

3. **Infrastructure Updates**
   - Added `static_site_cloudfront_distribution_id` output to `infra/main/outputs.tf`
   - Enables automated CloudFront cache invalidation

4. **Documentation**
   - Created comprehensive `docs/how_to_deploy_frontend.md`
   - Covers prerequisites, usage, troubleshooting, architecture
   - Documents caching strategy and manual deployment fallback

### Usage

```bash
# Deploy to demo (most common)
make frontend-deploy-demo

# Deploy to other environments
make frontend-deploy-dev
make frontend-deploy-test
make frontend-deploy-prod
```

### Prerequisites

Before first deployment:
1. Apply Terraform infrastructure: `make tf-apply-demo`
2. Configure AWS credentials: `make aws-login`

### Features

- Automatic dependency installation if needed
- Production build with TypeScript compilation
- S3 sync with `--delete` flag (removes stale files)
- Optimized cache headers:
  - `index.html`: 5 minutes (allows quick updates)
  - Assets: 1 year (content-hashed filenames)
- CloudFront cache invalidation
- Clear output with deployment summary and CloudFront URL

### Next Steps

The deployment automation is complete and ready to use. Future enhancements could include:

1. **CI/CD Integration**: GitHub Actions workflow for automatic deployment
2. **Custom Domain**: Route 53 + ACM certificate setup
3. **Environment-specific builds**: Different API endpoints per environment
4. **Deployment previews**: Deploy to unique URLs for PR reviews
5. **Rollback capability**: Keep versioned builds in S3

### Files Modified/Created

- **Created**: `infra/scripts/frontend_deploy.sh` - Main deployment script
- **Created**: `docs/how_to_deploy_frontend.md` - Deployment guide
- **Modified**: `infra/main/outputs.tf` - Added CloudFront distribution ID output
- **Modified**: `Makefile` - Added deployment targets and help documentation
- **Modified**: `notes/frontend_deploy.md` - Updated with completion status

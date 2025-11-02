#!/usr/bin/env bash

# Frontend Static Site Deployment Script
# Builds and deploys the React/Vite frontend to AWS S3 + CloudFront
#
# Usage:
#   ./scripts/frontend_deploy.sh <env>
#   where <env> is: demo, dev, test, or prod
#
# Prerequisites:
#   - Terraform infrastructure must be applied for the target environment
#   - AWS credentials must be configured (via AWS_PROFILE or default credentials)
#   - Node.js and npm must be installed

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BUILD_OUTPUT_DIR="$FRONTEND_DIR/dist"
TF_DIR="$PROJECT_ROOT/infra/main"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment argument
if [ $# -eq 0 ]; then
    log_error "Environment argument required"
    echo "Usage: $0 <env>"
    echo "  where <env> is: demo, dev, test, or prod"
    exit 1
fi

ENV="$1"

# Validate environment name
case "$ENV" in
    demo|dev|test|prod)
        log_info "Deploying to environment: $ENV"
        ;;
    *)
        log_error "Invalid environment: $ENV"
        echo "Valid environments: demo, dev, test, prod"
        exit 1
        ;;
esac

# Step 1: Build the frontend
log_info "Building frontend for production..."
cd "$FRONTEND_DIR"

if [ ! -f "package.json" ]; then
    log_error "package.json not found in $FRONTEND_DIR"
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies..."
    npm install
fi

# Run production build
log_info "Running npm build..."
npm run build

if [ ! -d "$BUILD_OUTPUT_DIR" ]; then
    log_error "Build output directory not found: $BUILD_OUTPUT_DIR"
    exit 1
fi

log_success "Frontend build completed"

# Step 2: Get Terraform outputs
log_info "Retrieving Terraform outputs for environment: $ENV..."
cd "$TF_DIR"

# Check if terraform is initialized for this environment
if [ ! -d ".terraform" ]; then
    log_error "Terraform not initialized in $TF_DIR"
    log_info "Run: make tf-init-$ENV"
    exit 1
fi

# Get bucket name from Terraform output
BUCKET_NAME=$(terraform output -raw static_site_bucket_name 2>/dev/null || echo "")
if [ -z "$BUCKET_NAME" ]; then
    log_error "Could not retrieve S3 bucket name from Terraform output"
    log_info "Make sure Terraform has been applied for environment: $ENV"
    log_info "Run: make tf-apply-$ENV"
    exit 1
fi

# Get CloudFront distribution domain
CLOUDFRONT_DOMAIN=$(terraform output -raw static_site_cloudfront_domain 2>/dev/null || echo "")
if [ -z "$CLOUDFRONT_DOMAIN" ]; then
    log_warning "Could not retrieve CloudFront domain (non-fatal)"
fi

# Try to get CloudFront distribution ID (for cache invalidation)
# Note: This output doesn't exist yet in outputs.tf, so we'll handle it gracefully
DISTRIBUTION_ID=$(terraform output -raw static_site_cloudfront_distribution_id 2>/dev/null || echo "")

log_success "Retrieved Terraform outputs:"
log_info "  Bucket: $BUCKET_NAME"
if [ -n "$CLOUDFRONT_DOMAIN" ]; then
    log_info "  CloudFront Domain: https://$CLOUDFRONT_DOMAIN"
fi
if [ -n "$DISTRIBUTION_ID" ]; then
    log_info "  Distribution ID: $DISTRIBUTION_ID"
fi

# Step 3: Sync build to S3
log_info "Syncing build output to S3 bucket: $BUCKET_NAME..."

# Verify AWS credentials are working
if ! aws sts get-caller-identity &>/dev/null; then
    log_error "AWS credentials not configured or invalid"
    log_info "Configure credentials or run: make aws-login"
    exit 1
fi

# Sync files to S3 with appropriate settings
# --delete: Remove files in S3 that don't exist in local build
# --cache-control: Set caching headers (short cache for index.html, long cache for assets)
log_info "Uploading files to S3..."

# Upload index.html with short cache (it contains references to hashed assets)
aws s3 cp "$BUILD_OUTPUT_DIR/index.html" "s3://$BUCKET_NAME/index.html" \
    --cache-control "public, max-age=300" \
    --content-type "text/html"

# Upload all other files with longer cache (they have content hashes in filenames)
aws s3 sync "$BUILD_OUTPUT_DIR/" "s3://$BUCKET_NAME/" \
    --delete \
    --exclude "index.html" \
    --cache-control "public, max-age=31536000, immutable"

log_success "Files synced to S3"

# Step 4: Invalidate CloudFront cache (optional but recommended)
if [ -n "$DISTRIBUTION_ID" ]; then
    log_info "Creating CloudFront cache invalidation..."
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "$DISTRIBUTION_ID" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text 2>/dev/null || echo "")

    if [ -n "$INVALIDATION_ID" ]; then
        log_success "CloudFront invalidation created: $INVALIDATION_ID"
        log_info "Cache invalidation may take a few minutes to complete"
    else
        log_warning "Could not create CloudFront invalidation (non-fatal)"
    fi
else
    log_warning "CloudFront distribution ID not available, skipping cache invalidation"
    log_info "Add 'static_site_cloudfront_distribution_id' output to infra/main/outputs.tf to enable invalidation"
fi

# Step 5: Summary
echo ""
log_success "Deployment completed successfully!"
echo ""
log_info "Deployment Summary:"
log_info "  Environment: $ENV"
log_info "  S3 Bucket: $BUCKET_NAME"
if [ -n "$CLOUDFRONT_DOMAIN" ]; then
    log_info "  CloudFront URL: https://$CLOUDFRONT_DOMAIN"
    echo ""
    log_info "Your frontend is now live at:"
    echo -e "  ${GREEN}https://$CLOUDFRONT_DOMAIN${NC}"
else
    log_info "  CloudFront URL: (not available)"
fi
echo ""

if [ -n "$DISTRIBUTION_ID" ]; then
    log_info "Note: CloudFront cache invalidation is in progress"
    log_info "Changes may take a few minutes to appear globally"
else
    log_info "Note: CloudFront cache was not invalidated"
    log_info "You may need to wait for cache expiration or invalidate manually"
fi

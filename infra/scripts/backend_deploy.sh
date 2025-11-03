#!/usr/bin/env bash
#
# Backend Deployment Script
# Builds Docker image, pushes to ECR, and updates ECS services
#
# Usage: ./backend_deploy.sh <environment>
# Example: ./backend_deploy.sh demo

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INFRA_DIR="$PROJECT_ROOT/infra/main"

# Function to print colored messages
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Validate environment argument
if [ $# -ne 1 ]; then
    error "Usage: $0 <environment>"
    echo "  environment: demo, dev, test, or prod"
    exit 1
fi

ENV="$1"

# Validate environment value
case "$ENV" in
    demo|dev|test|prod)
        info "Deploying to environment: $ENV"
        ;;
    *)
        error "Invalid environment: $ENV"
        echo "  Valid environments: demo, dev, test, prod"
        exit 1
        ;;
esac

# Image tag (using latest for now, could use git SHA later)
IMAGE_TAG="latest"

info "Starting backend deployment for environment: $ENV"
echo ""

# Step 1: Build Docker image
info "Step 1/6: Building Docker image..."
cd "$PROJECT_ROOT"

if ! docker build -t "genonaut:$IMAGE_TAG" .; then
    error "Docker build failed"
    exit 1
fi

success "Docker image built successfully"
echo ""

# Step 2: Retrieve Terraform outputs
info "Step 2/6: Retrieving ECR repository URLs from Terraform..."
cd "$INFRA_DIR"

# Check if Terraform is initialized
if [ ! -d ".terraform" ]; then
    error "Terraform not initialized. Run 'make tf-init-$ENV' first"
    exit 1
fi

# Get ECR repository URLs
ECR_API=$(terraform output -raw ecr_repo_api_url 2>/dev/null || echo "")
ECR_WORKER=$(terraform output -raw ecr_repo_worker_url 2>/dev/null || echo "")
ECR_IMAGEGEN=$(terraform output -raw ecr_repo_image_gen_url 2>/dev/null || echo "")

if [ -z "$ECR_API" ] || [ -z "$ECR_WORKER" ] || [ -z "$ECR_IMAGEGEN" ]; then
    error "Could not retrieve ECR repository URLs from Terraform"
    error "Make sure you have applied Terraform: make tf-apply-$ENV"
    exit 1
fi

info "ECR API Repository: $ECR_API"
info "ECR Worker Repository: $ECR_WORKER"
info "ECR ImageGen Repository: $ECR_IMAGEGEN"
echo ""

# Step 3: Tag images for each ECR repository
info "Step 3/6: Tagging Docker images for ECR..."

docker tag "genonaut:$IMAGE_TAG" "$ECR_API:$IMAGE_TAG"
docker tag "genonaut:$IMAGE_TAG" "$ECR_WORKER:$IMAGE_TAG"
docker tag "genonaut:$IMAGE_TAG" "$ECR_IMAGEGEN:$IMAGE_TAG"

success "Images tagged successfully"
echo ""

# Step 4: Authenticate to ECR
info "Step 4/6: Authenticating to AWS ECR..."

# Extract AWS region from ECR URL
AWS_REGION=$(echo "$ECR_API" | cut -d'.' -f4)
info "Using AWS region: $AWS_REGION"

# Login to ECR
if ! aws ecr get-login-password --region "$AWS_REGION" | \
     docker login --username AWS --password-stdin "$(echo "$ECR_API" | cut -d'/' -f1)"; then
    error "Failed to authenticate to ECR"
    error "Make sure AWS credentials are configured: make aws-login"
    exit 1
fi

success "Authenticated to ECR successfully"
echo ""

# Step 5: Push images to ECR
info "Step 5/6: Pushing images to ECR..."

info "Pushing API image..."
if ! docker push "$ECR_API:$IMAGE_TAG"; then
    error "Failed to push API image"
    exit 1
fi

info "Pushing Worker image..."
if ! docker push "$ECR_WORKER:$IMAGE_TAG"; then
    error "Failed to push Worker image"
    exit 1
fi

info "Pushing ImageGen image..."
if ! docker push "$ECR_IMAGEGEN:$IMAGE_TAG"; then
    error "Failed to push ImageGen image"
    exit 1
fi

success "All images pushed successfully"
echo ""

# Step 6: Force ECS service updates
info "Step 6/6: Updating ECS services..."

ECS_CLUSTER="genonaut-$ENV"
API_SERVICE="genonaut-api-$ENV"
CELERY_SERVICE="genonaut-celery-$ENV"
IMAGEGEN_SERVICE="genonaut-image-gen-$ENV"

info "Updating API service..."
if ! aws ecs update-service \
    --cluster "$ECS_CLUSTER" \
    --service "$API_SERVICE" \
    --force-new-deployment \
    --region "$AWS_REGION" \
    --output text > /dev/null; then
    warn "Failed to update API service (may not exist yet)"
else
    success "API service update initiated"
fi

info "Updating Celery service..."
if ! aws ecs update-service \
    --cluster "$ECS_CLUSTER" \
    --service "$CELERY_SERVICE" \
    --force-new-deployment \
    --region "$AWS_REGION" \
    --output text > /dev/null; then
    warn "Failed to update Celery service (may not exist yet)"
else
    success "Celery service update initiated"
fi

info "Updating ImageGen service..."
if ! aws ecs update-service \
    --cluster "$ECS_CLUSTER" \
    --service "$IMAGEGEN_SERVICE" \
    --force-new-deployment \
    --region "$AWS_REGION" \
    --output text > /dev/null; then
    warn "Failed to update ImageGen service (may not exist yet)"
else
    success "ImageGen service update initiated"
fi

echo ""
success "Deployment completed successfully!"
echo ""

# Print deployment summary
echo "======================================"
echo "Deployment Summary"
echo "======================================"
echo "Environment:       $ENV"
echo "Image Tag:         $IMAGE_TAG"
echo "API Service:       $API_SERVICE"
echo "Celery Service:    $CELERY_SERVICE"
echo "ImageGen Service:  $IMAGEGEN_SERVICE"
echo ""
echo "ECS services are updating. This may take 2-5 minutes."
echo ""
echo "Check service status:"
echo "  aws ecs describe-services --cluster $ECS_CLUSTER --services $API_SERVICE --region $AWS_REGION"
echo ""
echo "View logs:"
echo "  aws logs tail /ecs/$API_SERVICE --follow --region $AWS_REGION"
echo "======================================"

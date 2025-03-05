#!/bin/bash

# SEC Insights Deployment Script
# ----------------------------

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"sec-insights-project"}
REGION=${REGION:-"us-central1"}
ARTIFACT_REPO="sec-insights"
IMAGE_NAME="sec-insights-api"
IMAGE_TAG=$(date +%Y%m%d-%H%M%S)
BUCKET_PREFIX=${BUCKET_PREFIX:-"sec-insights"}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: docker is not installed"
    exit 1
fi

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "Error: terraform is not installed"
    exit 1
fi

echo "🚀 Starting deployment to project: $PROJECT_ID"

# Set Google Cloud project
echo "Setting Google Cloud project..."
gcloud config set project "$PROJECT_ID"

# Ensure Artifact Registry repository exists
echo "Ensuring Artifact Registry repository exists..."
gcloud artifacts repositories create "$ARTIFACT_REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --description="SEC Insights container repository" \
    --quiet || true

# Build and push Docker image
echo "Building and pushing Docker image..."
IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO/$IMAGE_NAME:$IMAGE_TAG"

docker build -t "$IMAGE_URL" .
docker push "$IMAGE_URL"
echo "Image pushed to: $IMAGE_URL"

# Deploy infrastructure with Terraform
echo "Deploying infrastructure with Terraform..."
cd infra/terraform

# Initialize Terraform
terraform init

# Apply Terraform configuration
terraform apply \
    -var="project_id=$PROJECT_ID" \
    -var="region=$REGION" \
    -var="bucket_prefix=$BUCKET_PREFIX" \
    -var="api_image_url=$IMAGE_URL" \
    -auto-approve

# Get output values
API_URL=$(terraform output -raw api_url)

echo "✅ Deployment completed successfully!"
echo "API URL: $API_URL"
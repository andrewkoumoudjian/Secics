#!/bin/bash

# SEC Insights Deployment Script
set -e

# Configuration
PROJECT_ID="halogen-rampart-452816-r2"
REGION="us-central1"
SERVICE_NAME="sec-insights-api"
IMAGE_NAME="sec-insights-api"
IMAGE_TAG=$(date +%Y%m%d-%H%M%S)
IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/sec-insights/$IMAGE_NAME:$IMAGE_TAG"

echo "🚀 Starting deployment of SEC Insights..."

# Build and push Docker image
echo "Building and pushing Docker image..."
gcloud builds submit --tag $IMAGE_URL

# Deploy to Cloud Run with extended timeout and increased memory
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URL \
  --platform managed \
  --region $REGION \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300s \
  --concurrency 80 \
  --allow-unauthenticated

echo "✅ Deployment completed!"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
echo "Service URL: $SERVICE_URL"

# Set up Cloud Scheduler (optional)
read -p "Would you like to set up a daily processing job with Cloud Scheduler? (y/n) " setup_scheduler
if [[ $setup_scheduler == "y" ]]; then
  echo "Setting up Cloud Scheduler job..."
  gcloud scheduler jobs create http sec-insights-daily-processing \
    --schedule="0 4 * * *" \
    --uri="${SERVICE_URL}/admin/process_daily" \
    --http-method=POST \
    --attempt-deadline=300s \
    --time-zone="America/New_York"
  echo "Cloud Scheduler job created!"
fi

echo "Deployment complete! Your SEC Insights API is now available at: $SERVICE_URL"
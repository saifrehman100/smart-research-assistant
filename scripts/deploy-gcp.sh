#!/bin/bash

# GCP Cloud Run deployment script

set -e

# Configuration
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="smart-research-assistant"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Deploying Smart Research Assistant to GCP Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    echo "   Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "Setting GCP project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required GCP APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    cloudscheduler.googleapis.com

# Build and push Docker image
echo "Building Docker image..."
cd backend
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "APP_ENV=production" \
    --set-env-vars "DATABASE_URL=\${DATABASE_URL}" \
    --set-env-vars "REDIS_URL=\${REDIS_URL}" \
    --set-env-vars "GOOGLE_API_KEY=\${GOOGLE_API_KEY}"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Service URL: $SERVICE_URL"
echo "API Docs: $SERVICE_URL/docs"
echo ""
echo "Next steps:"
echo "1. Set up Cloud SQL PostgreSQL database"
echo "2. Set up Cloud Memorystore for Redis"
echo "3. Update environment variables with connection strings"
echo "4. Set up Cloud Scheduler for Celery workers (if needed)"
echo ""

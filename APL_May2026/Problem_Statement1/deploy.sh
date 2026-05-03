#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
# deploy.sh – Deploy CricketLens AI to Google Cloud Run
# Usage: bash deploy.sh
# Prerequisites: gcloud CLI installed & authenticated
# ─────────────────────────────────────────────────────────────────────

set -e

PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="cricketlens-ai"
REGION="us-central1"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🏏 Deploying CricketLens AI to Google Cloud Run"
echo "   Project : $PROJECT_ID"
echo "   Service : $SERVICE_NAME"
echo "   Region  : $REGION"
echo ""

# Build and push the Docker image
echo "📦 Building Docker image..."
gcloud builds submit --tag "$IMAGE" .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 5 \
  --port 8080

echo ""
echo "✅ Deployment complete!"
gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)"

#!/bin/bash

# SCONIA Google Cloud Deployment Script
# This script deploys both backend and frontend to Google Cloud

set -e

# Configuration
PROJECT_ID="day-one-465214"
REGION="us-central1"
SERVICE_NAME_API="sconia-api"
SERVICE_NAME_FRONTEND="sconia-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 SCONIA Google Cloud Deployment${NC}"
echo "=================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  Not logged in to gcloud. Please run: gcloud auth login${NC}"
    exit 1
fi

# Set project
echo -e "${BLUE}📋 Setting up project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Build and deploy backend
echo -e "${BLUE}🏗️  Building backend Docker image...${NC}"
gcloud builds submit . --tag gcr.io/$PROJECT_ID/$SERVICE_NAME_API:latest

echo -e "${BLUE}🚀 Deploying backend to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME_API \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_API:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 1 \
    --port 8000 \
    --timeout 300 \
    --set-env-vars="DATABASE_URL=postgresql://sconia_user:SconiaApp2024Pass@/sconia?host=/cloudsql/day-one-465214:us-central1:sconia-postgres,DATABASE_URL_ASYNC=postgresql+asyncpg://sconia_user:SconiaApp2024Pass@/sconia?host=/cloudsql/day-one-465214:us-central1:sconia-postgres,QDRANT_URL=https://6b71346c-f2c7-4515-a743-6adf2e81ea31.us-east4-0.gcp.cloud.qdrant.io:6333,QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.0b5XGbJR1rGa2uIQmf2sL9BuJjz_6E8vhrEQTLEWcxE,REDIS_URL=memory://,SECRET_KEY=sconia-production-secret-key-2024,ENVIRONMENT=production" \
    --set-secrets="OPENAI_API_KEY=openai-api-key:latest" \
    --add-cloudsql-instances="day-one-465214:us-central1:sconia-postgres"

# Get backend URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME_API --region=$REGION --format="value(status.url)")
echo -e "${GREEN}✅ Backend deployed at: $BACKEND_URL${NC}"

# Build frontend with backend URL
echo -e "${BLUE}🏗️  Building frontend Docker image...${NC}"
cd frontend
docker build -f Dockerfile.prod --build-arg VITE_API_URL=$BACKEND_URL -t gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest .
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest

echo -e "${BLUE}🚀 Deploying frontend to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME_FRONTEND \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 0.5 \
    --port 80

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $SERVICE_NAME_FRONTEND --region=$REGION --format="value(status.url)")
echo -e "${GREEN}✅ Frontend deployed at: $FRONTEND_URL${NC}"

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}📱 Frontend: $FRONTEND_URL${NC}"
echo -e "${BLUE}🔧 Backend API: $BACKEND_URL${NC}"
echo ""
echo -e "${YELLOW}⚠️  Next steps:${NC}"
echo "1. Set up Cloud SQL PostgreSQL database"
echo "2. Configure Qdrant vector database"
echo "3. Set up Redis cache"
echo "4. Add secrets to Secret Manager"
echo "5. Update environment variables"

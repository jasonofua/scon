#!/bin/bash

# SCONIA Quick Deployment Script for Google Cloud
# Deploys the application with minimal infrastructure setup

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

echo -e "${BLUE}🚀 SCONIA Quick Deployment to Google Cloud${NC}"
echo "============================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Set project
echo -e "${BLUE}📋 Setting up project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# Create a temporary environment file for the backend
echo -e "${BLUE}📝 Creating temporary environment configuration...${NC}"
cat > .env.production << EOF
# Temporary configuration for initial deployment
DATABASE_URL=sqlite:///tmp/sconia.db
QDRANT_URL=memory://
REDIS_URL=memory://
OPENAI_API_KEY=your-openai-key-here
ENVIRONMENT=production
EOF

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
    --min-instances 0 \
    --port 8000 \
    --timeout 300 \
    --set-env-vars="DATABASE_URL=sqlite:///tmp/sconia.db,QDRANT_URL=memory://,REDIS_URL=memory://,ENVIRONMENT=production"

# Get backend URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME_API --region=$REGION --format="value(status.url)")
echo -e "${GREEN}✅ Backend deployed at: $BACKEND_URL${NC}"

# Test backend health
echo -e "${BLUE}🔍 Testing backend health...${NC}"
if curl -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Backend health check failed, but continuing...${NC}"
fi

# Build frontend
echo -e "${BLUE}🏗️  Building frontend Docker image...${NC}"
cd frontend

# Create production Dockerfile if it doesn't exist
if [ ! -f "Dockerfile.prod" ]; then
    echo -e "${YELLOW}⚠️  Creating production Dockerfile...${NC}"
    cat > Dockerfile.prod << 'EOF'
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf 2>/dev/null || echo "server { listen 80; root /usr/share/nginx/html; index index.html; location / { try_files \$uri \$uri/ /index.html; } }" > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF
fi

docker build -f Dockerfile.prod \
    --build-arg VITE_API_URL=$BACKEND_URL \
    -t gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest .

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

cd ..

# Cleanup
rm -f .env.production

echo ""
echo -e "${GREEN}🎉 Quick Deployment completed successfully!${NC}"
echo -e "${BLUE}📱 Frontend: $FRONTEND_URL${NC}"
echo -e "${BLUE}🔧 Backend API: $BACKEND_URL${NC}"
echo ""
echo -e "${YELLOW}⚠️  Note: This is a basic deployment with in-memory storage.${NC}"
echo -e "${YELLOW}   For production, you'll need to set up proper databases.${NC}"
echo ""
echo -e "${BLUE}🧪 Test your deployment:${NC}"
echo "curl $BACKEND_URL/health"
echo "curl -X POST '$BACKEND_URL/api/v1/chat/' -H 'Content-Type: application/json' -d '{\"query\": \"hello\", \"session_id\": \"test\"}'"

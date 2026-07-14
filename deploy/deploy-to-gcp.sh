#!/bin/bash

# SCONIA Complete Google Cloud Deployment Script
# This script handles the full deployment of SCONIA to Google Cloud

set -e

# Configuration
PROJECT_ID="day-one-465214"
REGION="us-central1"
DB_INSTANCE_NAME="sconia-postgres"
DB_NAME="sconia"
DB_USER="sconia_user"
REDIS_INSTANCE_NAME="sconia-redis"
SERVICE_NAME_API="sconia-api"
SERVICE_NAME_FRONTEND="sconia-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 SCONIA Complete Google Cloud Deployment${NC}"
echo "============================================="

# Function to check if a resource exists
check_resource_exists() {
    local resource_type=$1
    local resource_name=$2
    local extra_params=$3
    
    if gcloud $resource_type describe $resource_name $extra_params &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Phase 1: Infrastructure Setup
echo -e "${BLUE}📋 Phase 1: Setting up infrastructure...${NC}"

# Generate random password for database
if [[ ! -f ".db_password" ]]; then
    DB_PASSWORD=$(openssl rand -base64 32)
    echo "$DB_PASSWORD" > .db_password
    chmod 600 .db_password
    echo -e "${GREEN}✅ Generated database password${NC}"
else
    DB_PASSWORD=$(cat .db_password)
    echo -e "${YELLOW}ℹ️  Using existing database password${NC}"
fi

# Create Cloud SQL instance
echo -e "${BLUE}🗄️  Setting up Cloud SQL PostgreSQL...${NC}"
if check_resource_exists "sql instances" "$DB_INSTANCE_NAME"; then
    echo -e "${YELLOW}ℹ️  Cloud SQL instance '$DB_INSTANCE_NAME' already exists${NC}"
else
    gcloud sql instances create $DB_INSTANCE_NAME \
        --database-version=POSTGRES_14 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup-start-time=03:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04
    echo -e "${GREEN}✅ Cloud SQL instance created${NC}"
fi

# Create database
if gcloud sql databases describe $DB_NAME --instance=$DB_INSTANCE_NAME &>/dev/null; then
    echo -e "${YELLOW}ℹ️  Database '$DB_NAME' already exists${NC}"
else
    gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE_NAME
    echo -e "${GREEN}✅ Database created${NC}"
fi

# Create database user
if gcloud sql users describe $DB_USER --instance=$DB_INSTANCE_NAME &>/dev/null; then
    echo -e "${YELLOW}ℹ️  Database user '$DB_USER' already exists${NC}"
else
    gcloud sql users create $DB_USER \
        --instance=$DB_INSTANCE_NAME \
        --password=$DB_PASSWORD
    echo -e "${GREEN}✅ Database user created${NC}"
fi

# Create Redis instance
echo -e "${BLUE}🔴 Setting up Redis...${NC}"
if check_resource_exists "redis instances" "$REDIS_INSTANCE_NAME" "--region=$REGION"; then
    echo -e "${YELLOW}ℹ️  Redis instance '$REDIS_INSTANCE_NAME' already exists${NC}"
else
    gcloud redis instances create $REDIS_INSTANCE_NAME \
        --size=1 \
        --region=$REGION \
        --redis-version=redis_6_x
    echo -e "${GREEN}✅ Redis instance created${NC}"
fi

# Get Redis IP
REDIS_IP=$(gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION --format="value(host)")
echo -e "${GREEN}✅ Redis IP: $REDIS_IP${NC}"

# Phase 2: Secrets Management
echo -e "${BLUE}🔐 Phase 2: Setting up secrets...${NC}"

# Create database password secret
if gcloud secrets describe db-password &>/dev/null; then
    echo -e "${YELLOW}ℹ️  Secret 'db-password' already exists${NC}"
else
    echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=-
    echo -e "${GREEN}✅ Database password secret created${NC}"
fi

# Create placeholder secrets for API keys (user will need to update these)
if ! gcloud secrets describe openai-api-key &>/dev/null; then
    echo -n "PLEASE_UPDATE_THIS_WITH_YOUR_OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=-
    echo -e "${YELLOW}⚠️  Created placeholder OpenAI API key secret${NC}"
fi

if ! gcloud secrets describe secret-key &>/dev/null; then
    SECRET_KEY=$(openssl rand -base64 32)
    echo -n "$SECRET_KEY" | gcloud secrets create secret-key --data-file=-
    echo -e "${GREEN}✅ Application secret key created${NC}"
fi

# Phase 3: Build and Deploy Backend
echo -e "${BLUE}🏗️  Phase 3: Building and deploying backend...${NC}"

# Build backend Docker image
echo -e "${BLUE}📦 Building backend Docker image...${NC}"
gcloud builds submit . --tag gcr.io/$PROJECT_ID/$SERVICE_NAME_API:latest

# Deploy backend to Cloud Run
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
    --set-env-vars="ENVIRONMENT=production,DEBUG=False" \
    --set-env-vars="DATABASE_URL=postgresql://$DB_USER@/$DB_NAME?host=/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE_NAME" \
    --set-env-vars="REDIS_URL=redis://$REDIS_IP:6379/0" \
    --set-secrets="OPENAI_API_KEY=openai-api-key:latest,SECRET_KEY=secret-key:latest" \
    --add-cloudsql-instances=$PROJECT_ID:$REGION:$DB_INSTANCE_NAME

# Get backend URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME_API --region=$REGION --format="value(status.url)")
echo -e "${GREEN}✅ Backend deployed at: $BACKEND_URL${NC}"

# Phase 4: Build and Deploy Frontend
echo -e "${BLUE}🏗️  Phase 4: Building and deploying frontend...${NC}"

# Create frontend Dockerfile for production
cat > frontend/Dockerfile.prod << EOF
# Build stage
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=\$VITE_API_URL
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# Build and push frontend
echo -e "${BLUE}📦 Building frontend Docker image...${NC}"
cd frontend
gcloud builds submit . --tag gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest \
    --substitutions=_VITE_API_URL=$BACKEND_URL \
    --config=- << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '--build-arg', 'VITE_API_URL=$BACKEND_URL', '-t', 'gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest', '.', '-f', 'Dockerfile.prod']
images:
- 'gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest'
EOF

cd ..

# Deploy frontend
echo -e "${BLUE}🚀 Deploying frontend to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME_FRONTEND \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 0.5 \
    --max-instances 5 \
    --min-instances 0 \
    --port 80

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $SERVICE_NAME_FRONTEND --region=$REGION --format="value(status.url)")
echo -e "${GREEN}✅ Frontend deployed at: $FRONTEND_URL${NC}"

# Phase 5: Database Initialization
echo -e "${BLUE}🗄️  Phase 5: Initializing database...${NC}"

# Install Cloud SQL Proxy for local connection
if ! command -v cloud_sql_proxy &> /dev/null; then
    echo -e "${BLUE}📥 Installing Cloud SQL Proxy...${NC}"
    curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
    chmod +x cloud_sql_proxy
fi

# Start Cloud SQL Proxy in background
echo -e "${BLUE}🔌 Starting Cloud SQL Proxy...${NC}"
./cloud_sql_proxy -instances=$PROJECT_ID:$REGION:$DB_INSTANCE_NAME=tcp:5432 &
PROXY_PID=$!
sleep 5

# Run database migrations
echo -e "${BLUE}📊 Running database migrations...${NC}"
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
export DATABASE_URL_ASYNC="postgresql+asyncpg://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"

python -m alembic upgrade head

# Initialize with sample data
echo -e "${BLUE}📝 Initializing sample data...${NC}"
python scripts/init_data.py

# Stop Cloud SQL Proxy
kill $PROXY_PID 2>/dev/null || true

echo ""
echo -e "${GREEN}🎉 SCONIA Deployment completed successfully!${NC}"
echo "============================================="
echo -e "${BLUE}📱 Frontend URL: $FRONTEND_URL${NC}"
echo -e "${BLUE}🔧 Backend API: $BACKEND_URL${NC}"
echo -e "${BLUE}🗄️  Database: $PROJECT_ID:$REGION:$DB_INSTANCE_NAME${NC}"
echo -e "${BLUE}🔴 Redis: $REDIS_IP:6379${NC}"
echo ""
echo -e "${YELLOW}⚠️  Important next steps:${NC}"
echo "1. Update your OpenAI API key:"
echo "   echo 'your-actual-openai-key' | gcloud secrets versions add openai-api-key --data-file=-"
echo ""
echo "2. For Qdrant vector database, you have two options:"
echo "   Option A: Use Qdrant Cloud (recommended):"
echo "   - Sign up at https://cloud.qdrant.io"
echo "   - Create a cluster and get your API key"
echo "   - Update backend environment: gcloud run services update $SERVICE_NAME_API --set-env-vars='QDRANT_URL=your-qdrant-url' --set-secrets='QDRANT_API_KEY=qdrant-api-key:latest'"
echo ""
echo "   Option B: Deploy Qdrant on GKE (advanced):"
echo "   - Create a GKE cluster"
echo "   - Deploy Qdrant using Helm"
echo ""
echo "3. Test your deployment:"
echo "   curl $BACKEND_URL/health"
echo "   curl $BACKEND_URL/docs"
echo ""
echo "4. Access the application at: $FRONTEND_URL"

# SCONIA Google Cloud Deployment Guide

This guide will help you deploy SCONIA (both backend and frontend) to Google Cloud Platform.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and configured
3. **Docker** installed locally
4. **OpenAI API Key** for embeddings
5. **Qdrant Cloud account** (or self-hosted Qdrant)

## Quick Deployment

### Step 1: Configure Project

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Update configuration files
sed -i "s/your-gcp-project-id/$PROJECT_ID/g" deploy/*.sh
sed -i "s/PROJECT_ID/$PROJECT_ID/g" deploy/gcp-deployment.yaml
```

### Step 2: Set up Infrastructure

```bash
# Make scripts executable
chmod +x deploy/*.sh

# Set up databases and infrastructure
./deploy/setup-infrastructure.sh
```

### Step 3: Configure Secrets

```bash
# Add your actual API keys
echo "your-actual-openai-api-key" | gcloud secrets versions add openai-api-key --data-file=-
echo "your-actual-qdrant-api-key" | gcloud secrets versions add qdrant-api-key --data-file=-
```

### Step 4: Deploy Application

```bash
# Deploy both backend and frontend
./deploy/deploy.sh
```

## Manual Deployment Steps

### 1. Infrastructure Setup

#### Cloud SQL PostgreSQL
```bash
gcloud sql instances create sconia-postgres \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1

gcloud sql databases create sconia --instance=sconia-postgres
gcloud sql users create sconia_user --instance=sconia-postgres --password=your-password
```

#### Redis
```bash
gcloud redis instances create sconia-redis \
    --size=1 \
    --region=us-central1
```

### 2. Backend Deployment

```bash
# Build and push Docker image
gcloud builds submit . --tag gcr.io/$PROJECT_ID/sconia-api:latest

# Deploy to Cloud Run
gcloud run deploy sconia-api \
    --image gcr.io/$PROJECT_ID/sconia-api:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --port 8000
```

### 3. Frontend Deployment

```bash
cd frontend

# Build with production Dockerfile
docker build -f Dockerfile.prod \
    --build-arg VITE_API_URL=https://your-backend-url \
    -t gcr.io/$PROJECT_ID/sconia-frontend:latest .

docker push gcr.io/$PROJECT_ID/sconia-frontend:latest

# Deploy to Cloud Run
gcloud run deploy sconia-frontend \
    --image gcr.io/$PROJECT_ID/sconia-frontend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 80
```

## Environment Variables

### Backend Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `QDRANT_URL`: Qdrant vector database URL
- `QDRANT_API_KEY`: Qdrant API key
- `OPENAI_API_KEY`: OpenAI API key
- `REDIS_URL`: Redis connection string
- `ENVIRONMENT`: Set to "production"

### Frontend Environment Variables
- `VITE_API_URL`: Backend API URL

## Post-Deployment

### 1. Initialize Database
```bash
# Run database migrations
gcloud run jobs create sconia-migrate \
    --image gcr.io/$PROJECT_ID/sconia-api:latest \
    --command python \
    --args "scripts/init_data.py"

gcloud run jobs execute sconia-migrate
```

### 2. Import Constitution
```bash
# Import constitution to vector database
gcloud run jobs create sconia-constitution \
    --image gcr.io/$PROJECT_ID/sconia-api:latest \
    --command python \
    --args "scripts/add_constitution.py"

gcloud run jobs execute sconia-constitution
```

## Monitoring and Maintenance

### View Logs
```bash
# Backend logs
gcloud run services logs read sconia-api --region=us-central1

# Frontend logs
gcloud run services logs read sconia-frontend --region=us-central1
```

### Update Deployment
```bash
# Rebuild and redeploy
gcloud builds submit . --tag gcr.io/$PROJECT_ID/sconia-api:latest
gcloud run services update sconia-api --image gcr.io/$PROJECT_ID/sconia-api:latest
```

## Cost Optimization

1. **Cloud Run**: Scales to zero when not in use
2. **Cloud SQL**: Use smallest instance size for development
3. **Redis**: Use basic tier for development
4. **Storage**: Regular cleanup of old logs and data

## Security Considerations

1. **IAM**: Use least privilege access
2. **Secrets**: Store all sensitive data in Secret Manager
3. **VPC**: Consider using VPC for production
4. **SSL**: Cloud Run provides HTTPS by default
5. **Authentication**: Add authentication for admin endpoints

## Troubleshooting

### Common Issues

1. **Build Failures**: Check Dockerfile and dependencies
2. **Database Connection**: Verify Cloud SQL proxy setup
3. **Memory Issues**: Increase Cloud Run memory allocation
4. **Timeout Issues**: Increase Cloud Run timeout settings

### Health Checks
- Backend: `https://your-backend-url/health`
- Frontend: `https://your-frontend-url/health`

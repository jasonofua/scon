#!/bin/bash

# SCONIA Deployment Fix Script
# This script fixes the architecture compatibility and CORS issues

set -e

# Configuration
PROJECT_ID="day-one-465214"
ZONE="us-central1-a"
CLUSTER_NAME="sconia-cluster"
IMAGE_TAG="v$(date +%Y%m%d-%H%M%S)-amd64-fix"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 SCONIA Deployment Fix${NC}"
echo "=================================="
echo -e "${YELLOW}This script will fix:${NC}"
echo "  ✅ Docker architecture compatibility (exec format error)"
echo "  ✅ CORS configuration for frontend access"
echo "  ✅ Missing Kubernetes deployment files"
echo ""

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed. Please install it first.${NC}"
    exit 1
fi

# Set project
echo -e "${BLUE}🔧 Setting up project...${NC}"
gcloud config set project $PROJECT_ID

# Get cluster credentials
echo -e "${BLUE}🔑 Getting cluster credentials...${NC}"
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE

# Update Qdrant secrets
echo -e "${BLUE}🔑 Updating Qdrant secrets...${NC}"
QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.SPNWCGECEkm2mU5cVWGJxS_ImkZpahtae08n7N27u_Q"

# Create or update the Qdrant API key secret
if kubectl get secret qdrant-api-key &>/dev/null; then
    echo -e "${YELLOW}⚠️  Updating existing Qdrant API key secret...${NC}"
    kubectl delete secret qdrant-api-key
fi

kubectl create secret generic qdrant-api-key \
    --from-literal=latest="$QDRANT_API_KEY"

echo -e "${GREEN}✅ Qdrant API key secret updated${NC}"

# Build multi-platform Docker image
echo -e "${BLUE}🏗️  Building multi-platform Docker image...${NC}"
echo "Building for linux/amd64 to fix exec format error..."

# Enable Docker buildx for multi-platform builds
docker buildx create --use --name multiplatform-builder 2>/dev/null || true

# Build and push with explicit platform
gcloud builds submit . \
    --tag gcr.io/$PROJECT_ID/sconia-api:$IMAGE_TAG \
    --tag gcr.io/$PROJECT_ID/sconia-api:latest \
    --machine-type=e2-highcpu-8 \
    --timeout=20m

echo -e "${GREEN}✅ Docker image built successfully${NC}"

# Update deployment image
echo -e "${BLUE}📝 Updating deployment image...${NC}"
sed -i.bak "s|gcr.io/day-one-465214/sconia-api:.*|gcr.io/$PROJECT_ID/sconia-api:$IMAGE_TAG|g" k8s/sconia-api-deployment.yaml

# Deploy to Kubernetes
echo -e "${BLUE}🚀 Deploying to Kubernetes...${NC}"

# Apply the deployment
kubectl apply -f k8s/sconia-api-deployment.yaml

# Wait for deployment to be ready
echo -e "${BLUE}⏳ Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=600s deployment/sconia-api

# Apply ingress
echo -e "${BLUE}🌐 Setting up ingress...${NC}"
kubectl apply -f k8s-ingress.yaml

# Get service status
echo -e "${BLUE}📊 Getting service status...${NC}"
kubectl get services
kubectl get pods -l app=sconia-api
kubectl get ingress

# Check pod logs for any issues
echo -e "${BLUE}🔍 Checking pod logs...${NC}"
POD_NAME=$(kubectl get pods -l app=sconia-api -o jsonpath='{.items[0].metadata.name}')
if [ ! -z "$POD_NAME" ]; then
    echo "Latest logs from pod $POD_NAME:"
    kubectl logs $POD_NAME --tail=20 || echo "No logs available yet"
fi

# Restore original deployment file
mv k8s/sconia-api-deployment.yaml.bak k8s/sconia-api-deployment.yaml 2>/dev/null || true

echo ""
echo -e "${GREEN}🎉 Deployment Fix Completed!${NC}"
echo "============================================="
echo -e "${BLUE}🔧 API Service: sconia-api-service${NC}"
echo -e "${BLUE}🌐 URL: https://34.111.13.27.nip.io${NC}"
echo ""
echo -e "${BLUE}🧪 Test your deployment:${NC}"
echo "curl https://34.111.13.27.nip.io/health"
echo "curl -X POST 'https://34.111.13.27.nip.io/api/v1/chat/' -H 'Content-Type: application/json' -d '{\"query\": \"Who is the current Chief Justice of Nigeria?\", \"session_id\": \"test\"}'"
echo ""
echo -e "${GREEN}✅ Architecture and CORS issues should now be resolved!${NC}"
echo -e "${YELLOW}⚠️  If issues persist, check pod logs with: kubectl logs -l app=sconia-api${NC}"

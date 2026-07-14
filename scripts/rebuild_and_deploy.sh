#!/bin/bash

# SCONIA Rebuild and Redeploy Script
# This script rebuilds the Docker image with updated documents and redeploys to Kubernetes

set -e  # Exit on any error

# Configuration
PROJECT_ID="day-one-465214"
IMAGE_NAME="sconia-api"
NEW_VERSION="v5-rag-scoring-fix-amd64"
REGION="us-central1"
CLUSTER_NAME="sconia-cluster"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏛️  SCONIA Rebuild and Redeploy Script${NC}"
echo "=================================================="
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "   Project ID: $PROJECT_ID"
echo "   Image: $IMAGE_NAME"
echo "   New Version: $NEW_VERSION"
echo "   Region: $REGION"
echo ""

# Step 1: Force rebuild - skip all checks
echo -e "${BLUE}🔍 Step 1: Force rebuild mode - skipping checks...${NC}"
echo -e "${YELLOW}⚠️  Force rebuilding image from scratch${NC}"
echo -e "${GREEN}✅ Proceeding with force rebuild${NC}"
echo ""

# Step 2: Configure gcloud
echo -e "${BLUE}🔧 Step 2: Configuring gcloud...${NC}"
gcloud config set project $PROJECT_ID
gcloud auth configure-docker gcr.io --quiet

echo -e "${GREEN}✅ gcloud configured${NC}"
echo ""

# Step 3: Build new Docker image using Google Cloud Build (ensures AMD64 architecture)
echo -e "${BLUE}🐳 Step 3: Building Docker image using Google Cloud Build...${NC}"
echo -e "${YELLOW}Building image: gcr.io/$PROJECT_ID/$IMAGE_NAME:$NEW_VERSION${NC}"

# Use Google Cloud Build to ensure correct architecture (AMD64)
gcloud builds submit . --tag gcr.io/$PROJECT_ID/$IMAGE_NAME:$NEW_VERSION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built and pushed successfully (Google Cloud Build)${NC}"
else
    echo -e "${RED}❌ Google Cloud Build failed${NC}"
    exit 1
fi
echo ""

# Step 5: Update Kubernetes deployment
echo -e "${BLUE}🚀 Step 5: Updating Kubernetes deployment...${NC}"

# Update the deployment with new image
kubectl set image deployment/sconia-api sconia-api=gcr.io/$PROJECT_ID/$IMAGE_NAME:$NEW_VERSION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment updated with new image${NC}"
else
    echo -e "${RED}❌ Failed to update deployment${NC}"
    exit 1
fi

# Wait for rollout to complete
echo -e "${YELLOW}⏳ Waiting for rollout to complete...${NC}"
kubectl rollout status deployment/sconia-api --timeout=300s

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Rollout completed successfully${NC}"
else
    echo -e "${RED}❌ Rollout failed or timed out${NC}"
    echo -e "${YELLOW}💡 You can check the status with: kubectl get pods -l app=sconia-api${NC}"
    exit 1
fi
echo ""

# Step 6: Verify deployment
echo -e "${BLUE}🔍 Step 6: Verifying deployment...${NC}"

# Get pod status
echo -e "${YELLOW}📊 Pod Status:${NC}"
kubectl get pods -l app=sconia-api

# Get service status
echo -e "${YELLOW}🌐 Service Status:${NC}"
kubectl get services -l app=sconia-api

# Test health endpoint
echo -e "${YELLOW}🏥 Testing health endpoint...${NC}"
EXTERNAL_IP=$(kubectl get service sconia-api-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -n "$EXTERNAL_IP" ]; then
    echo "   External IP: $EXTERNAL_IP"
    
    # Wait a moment for the service to be ready
    sleep 10
    
    # Test health endpoint
    if curl -f -s "http://$EXTERNAL_IP/health" > /dev/null; then
        echo -e "${GREEN}   ✅ Health check passed${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Health check failed (service might still be starting)${NC}"
    fi
else
    echo -e "${YELLOW}   ⚠️  External IP not yet assigned${NC}"
fi

echo ""

# Step 7: Summary
echo -e "${BLUE}📋 Step 7: Deployment Summary${NC}"
echo "=================================================="
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📊 Deployment Details:${NC}"
echo "   Image: gcr.io/$PROJECT_ID/$IMAGE_NAME:$NEW_VERSION"
echo "   Status: $(kubectl get deployment sconia-api -o jsonpath='{.status.conditions[?(@.type=="Available")].status}')"
echo "   Replicas: $(kubectl get deployment sconia-api -o jsonpath='{.status.readyReplicas}')/$(kubectl get deployment sconia-api -o jsonpath='{.spec.replicas}')"
echo ""
echo -e "${YELLOW}🌐 Access URLs:${NC}"
if [ -n "$EXTERNAL_IP" ]; then
    echo "   API: http://$EXTERNAL_IP"
    echo "   Health: http://$EXTERNAL_IP/health"
    echo "   Docs: http://$EXTERNAL_IP/docs"
else
    echo "   External IP: Pending (check with 'kubectl get services')"
fi
echo ""
echo -e "${YELLOW}🔧 Useful Commands:${NC}"
echo "   Check pods: kubectl get pods -l app=sconia-api"
echo "   View logs: kubectl logs -l app=sconia-api --tail=50"
echo "   Check services: kubectl get services"
echo "   Scale deployment: kubectl scale deployment sconia-api --replicas=2"
echo ""
echo -e "${GREEN}✅ Your updated SCONIA application with new documents is now live!${NC}"

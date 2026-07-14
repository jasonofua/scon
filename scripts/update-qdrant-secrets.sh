#!/bin/bash

# Update Qdrant Secrets Script
# This script creates or updates Kubernetes secrets with the new Qdrant API key

set -e

# Configuration
PROJECT_ID="day-one-465214"
ZONE="us-central1-a"
CLUSTER_NAME="sconia-cluster"
QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.SPNWCGECEkm2mU5cVWGJxS_ImkZpahtae08n7N27u_Q"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔑 Updating Qdrant Secrets${NC}"
echo "=================================="

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed. Please install it first.${NC}"
    exit 1
fi

# Set project and get cluster credentials
echo -e "${BLUE}🔧 Setting up project and cluster access...${NC}"
gcloud config set project $PROJECT_ID
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE

# Create or update the Qdrant API key secret
echo -e "${BLUE}🔑 Creating/updating Qdrant API key secret...${NC}"

# Check if secret exists
if kubectl get secret qdrant-api-key &>/dev/null; then
    echo -e "${YELLOW}⚠️  Secret 'qdrant-api-key' already exists. Updating...${NC}"
    kubectl delete secret qdrant-api-key
fi

# Create the secret
kubectl create secret generic qdrant-api-key \
    --from-literal=latest="$QDRANT_API_KEY"

echo -e "${GREEN}✅ Qdrant API key secret created/updated successfully${NC}"

# Verify the secret
echo -e "${BLUE}🔍 Verifying secret...${NC}"
kubectl get secret qdrant-api-key -o yaml | grep -A 1 "data:"

echo ""
echo -e "${GREEN}🎉 Qdrant secrets updated successfully!${NC}"
echo "============================================="
echo -e "${BLUE}📝 Next steps:${NC}"
echo "1. Run the deployment script to apply changes:"
echo "   ./scripts/fix-deployment.sh"
echo ""
echo "2. Or manually restart the deployment:"
echo "   kubectl rollout restart deployment/sconia-api"
echo ""
echo -e "${YELLOW}⚠️  The pods will automatically restart to pick up the new configuration.${NC}"

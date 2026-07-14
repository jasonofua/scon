#!/bin/bash

# SCONIA HTTPS Backend Setup Script
# Sets up Google Cloud Load Balancer with SSL for the backend API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="day-one-465214"
REGION="us-central1"
DOMAIN="sconia-api.nip.io"  # Using nip.io for automatic DNS
STATIC_IP_NAME="sconia-api-ip"
SSL_CERT_NAME="sconia-api-ssl"
BACKEND_SERVICE_NAME="sconia-api-backend"
URL_MAP_NAME="sconia-api-urlmap"
TARGET_PROXY_NAME="sconia-api-proxy"
FORWARDING_RULE_NAME="sconia-api-forwarding"

echo -e "${BLUE}🔒 SCONIA HTTPS Backend Setup${NC}"
echo "=================================================="
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Domain: $DOMAIN"
echo ""

# Step 1: Reserve a static IP
echo -e "${BLUE}🌐 Step 1: Reserving static IP address...${NC}"
if gcloud compute addresses describe $STATIC_IP_NAME --global --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Static IP already exists${NC}"
else
    gcloud compute addresses create $STATIC_IP_NAME --global
    echo -e "${GREEN}✅ Static IP created${NC}"
fi

# Get the static IP
STATIC_IP=$(gcloud compute addresses describe $STATIC_IP_NAME --global --format="value(address)")
echo -e "${YELLOW}📍 Static IP: $STATIC_IP${NC}"
echo -e "${YELLOW}🌐 Your API will be available at: https://$STATIC_IP.nip.io${NC}"

# Step 2: Create managed SSL certificate
echo -e "${BLUE}🔐 Step 2: Creating managed SSL certificate...${NC}"
FULL_DOMAIN="$STATIC_IP.nip.io"

if gcloud compute ssl-certificates describe $SSL_CERT_NAME --global --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  SSL certificate already exists${NC}"
else
    gcloud compute ssl-certificates create $SSL_CERT_NAME \
        --domains=$FULL_DOMAIN \
        --global
    echo -e "${GREEN}✅ SSL certificate created${NC}"
fi

# Step 3: Create backend service
echo -e "${BLUE}🔧 Step 3: Creating backend service...${NC}"

# First, create a health check
HEALTH_CHECK_NAME="sconia-api-health-check"
if gcloud compute health-checks describe $HEALTH_CHECK_NAME --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Health check already exists${NC}"
else
    gcloud compute health-checks create http $HEALTH_CHECK_NAME \
        --port=80 \
        --request-path=/health \
        --check-interval=30s \
        --timeout=10s \
        --healthy-threshold=2 \
        --unhealthy-threshold=3
    echo -e "${GREEN}✅ Health check created${NC}"
fi

# Create backend service
if gcloud compute backend-services describe $BACKEND_SERVICE_NAME --global --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Backend service already exists${NC}"
else
    gcloud compute backend-services create $BACKEND_SERVICE_NAME \
        --protocol=HTTP \
        --health-checks=$HEALTH_CHECK_NAME \
        --global
    echo -e "${GREEN}✅ Backend service created${NC}"
fi

# Step 4: Create Network Endpoint Group (NEG) for the Kubernetes service
echo -e "${BLUE}🔗 Step 4: Creating Network Endpoint Group...${NC}"
NEG_NAME="sconia-api-neg"

# Get the current service IP
SERVICE_IP=$(kubectl get service sconia-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
SERVICE_PORT=$(kubectl get service sconia-api -o jsonpath='{.spec.ports[0].port}')

if gcloud compute network-endpoint-groups describe $NEG_NAME --global --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  NEG already exists${NC}"
else
    # Create global NEG for internet endpoints
    gcloud compute network-endpoint-groups create $NEG_NAME \
        --network-endpoint-type=INTERNET_IP_PORT \
        --global

    # Add the Kubernetes service as an endpoint
    gcloud compute network-endpoint-groups update $NEG_NAME \
        --add-endpoint="ip=$SERVICE_IP,port=$SERVICE_PORT" \
        --global

    echo -e "${GREEN}✅ NEG created and endpoint added${NC}"
fi

# Add NEG to backend service
echo -e "${BLUE}🔗 Adding NEG to backend service...${NC}"
gcloud compute backend-services add-backend $BACKEND_SERVICE_NAME \
    --network-endpoint-group=$NEG_NAME \
    --global || echo -e "${YELLOW}⚠️  Backend might already be added${NC}"

# Step 5: Create URL map
echo -e "${BLUE}🗺️  Step 5: Creating URL map...${NC}"
if gcloud compute url-maps describe $URL_MAP_NAME --global --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  URL map already exists${NC}"
else
    gcloud compute url-maps create $URL_MAP_NAME \
        --default-service=$BACKEND_SERVICE_NAME \
        --global
    echo -e "${GREEN}✅ URL map created${NC}"
fi

# Step 6: Create HTTPS target proxy
echo -e "${BLUE}🎯 Step 6: Creating HTTPS target proxy...${NC}"
if gcloud compute target-https-proxies describe $TARGET_PROXY_NAME --global --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Target proxy already exists${NC}"
else
    gcloud compute target-https-proxies create $TARGET_PROXY_NAME \
        --ssl-certificates=$SSL_CERT_NAME \
        --url-map=$URL_MAP_NAME \
        --global
    echo -e "${GREEN}✅ Target proxy created${NC}"
fi

# Step 7: Create forwarding rule
echo -e "${BLUE}📡 Step 7: Creating forwarding rule...${NC}"
if gcloud compute forwarding-rules describe $FORWARDING_RULE_NAME --global --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Forwarding rule already exists${NC}"
else
    gcloud compute forwarding-rules create $FORWARDING_RULE_NAME \
        --address=$STATIC_IP_NAME \
        --target-https-proxy=$TARGET_PROXY_NAME \
        --global \
        --ports=443
    echo -e "${GREEN}✅ Forwarding rule created${NC}"
fi

# Step 8: Wait for SSL certificate to be provisioned
echo -e "${BLUE}⏳ Step 8: Waiting for SSL certificate provisioning...${NC}"
echo -e "${YELLOW}This may take 10-15 minutes for the certificate to be fully provisioned.${NC}"

# Check certificate status
CERT_STATUS=$(gcloud compute ssl-certificates describe $SSL_CERT_NAME --global --format="value(managed.status)")
echo -e "${YELLOW}Certificate status: $CERT_STATUS${NC}"

if [ "$CERT_STATUS" = "ACTIVE" ]; then
    echo -e "${GREEN}✅ SSL certificate is active${NC}"
else
    echo -e "${YELLOW}⏳ SSL certificate is still provisioning...${NC}"
    echo -e "${YELLOW}You can check status with: gcloud compute ssl-certificates describe $SSL_CERT_NAME --global${NC}"
fi

# Step 9: Summary
echo ""
echo -e "${BLUE}📋 Setup Summary${NC}"
echo "=================================================="
echo -e "${GREEN}🎉 HTTPS backend setup completed!${NC}"
echo ""
echo -e "${YELLOW}📊 Configuration Details:${NC}"
echo "   Static IP: $STATIC_IP"
echo "   HTTPS URL: https://$STATIC_IP.nip.io"
echo "   SSL Certificate: $SSL_CERT_NAME"
echo "   Backend Service: $BACKEND_SERVICE_NAME"
echo ""
echo -e "${YELLOW}⏳ Next Steps:${NC}"
echo "1. Wait for SSL certificate to be fully provisioned (10-15 minutes)"
echo "2. Test the HTTPS endpoint: https://$STATIC_IP.nip.io/health"
echo "3. Update frontend environment to use HTTPS URL"
echo "4. Redeploy frontend to Vercel"
echo ""
echo -e "${YELLOW}🔧 Useful Commands:${NC}"
echo "   Check SSL status: gcloud compute ssl-certificates describe $SSL_CERT_NAME --global"
echo "   Test endpoint: curl https://$STATIC_IP.nip.io/health"
echo "   View load balancer: gcloud compute forwarding-rules list"
echo ""
echo -e "${YELLOW}🌐 Your new HTTPS API URL:${NC}"
echo -e "${GREEN}https://$STATIC_IP.nip.io${NC}"

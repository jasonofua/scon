#!/bin/bash

# SCONIA Quick Document Update Script
# This script updates documents directly in the running container as a quick fix

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏛️  SCONIA Quick Document Update${NC}"
echo "=================================================="
echo -e "${YELLOW}⚡ This is a quick fix that updates documents directly in the running container${NC}"
echo -e "${YELLOW}⚠️  Changes will be lost if the container restarts${NC}"
echo ""

# Step 1: Get the running pod
echo -e "${BLUE}🔍 Step 1: Finding running pod...${NC}"
POD_NAME=$(kubectl get pods -l app=sconia-api -o jsonpath='{.items[0].metadata.name}')

if [ -z "$POD_NAME" ]; then
    echo -e "${RED}❌ No running SCONIA pod found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found pod: $POD_NAME${NC}"
echo ""

# Step 2: Check pod status
echo -e "${BLUE}🔍 Step 2: Checking pod status...${NC}"
POD_STATUS=$(kubectl get pod $POD_NAME -o jsonpath='{.status.phase}')

if [ "$POD_STATUS" != "Running" ]; then
    echo -e "${RED}❌ Pod is not running (status: $POD_STATUS)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pod is running${NC}"
echo ""

# Step 3: List available documents
echo -e "${BLUE}📄 Step 3: Available documents to copy...${NC}"
DOCUMENTS=(
    "nigeria_electoral_act_2022.txt"
    "nigeria_constitution_provisions.txt"
    "nigeria_court_hierarchy_and_judges.txt"
    "nigeria_criminal_code_provisions.txt"
    "nigeria_current_judges_profiles.txt"
    "nigeria_supreme_court_landmark_cases.txt"
)

for doc in "${DOCUMENTS[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "   ✅ $doc ($(du -h "$doc" | cut -f1))"
    else
        echo -e "   ❌ $doc (not found)"
    fi
done
echo ""

# Step 4: Copy documents to container
echo -e "${BLUE}📤 Step 4: Copying documents to container...${NC}"

for doc in "${DOCUMENTS[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${YELLOW}   Copying $doc...${NC}"
        kubectl cp "$doc" "$POD_NAME:/app/$doc"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}   ✅ $doc copied successfully${NC}"
        else
            echo -e "${RED}   ❌ Failed to copy $doc${NC}"
        fi
    else
        echo -e "${YELLOW}   ⚠️  Skipping $doc (not found locally)${NC}"
    fi
done
echo ""

# Step 5: Verify documents in container
echo -e "${BLUE}🔍 Step 5: Verifying documents in container...${NC}"
echo -e "${YELLOW}Documents in container:${NC}"
kubectl exec $POD_NAME -- ls -la /app/*.txt 2>/dev/null || echo "No .txt files found"
echo ""

# Step 6: Restart the application process (optional)
echo -e "${BLUE}🔄 Step 6: Restarting application process...${NC}"
echo -e "${YELLOW}Sending SIGHUP to reload documents (if supported)...${NC}"

# Try to restart the uvicorn process gracefully
kubectl exec $POD_NAME -- pkill -HUP python 2>/dev/null || echo "Could not send SIGHUP (process might not support it)"

# Alternative: restart the main process
echo -e "${YELLOW}Alternatively, you can restart the pod for a clean reload:${NC}"
echo -e "${YELLOW}   kubectl delete pod $POD_NAME${NC}"
echo ""

# Step 7: Test the update
echo -e "${BLUE}🧪 Step 7: Testing document availability...${NC}"

# Get service external IP
EXTERNAL_IP=$(kubectl get service sconia-api-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -n "$EXTERNAL_IP" ]; then
    echo -e "${YELLOW}Testing document endpoint...${NC}"
    
    # Test if documents endpoint is available
    if curl -f -s "http://$EXTERNAL_IP/documents" > /dev/null; then
        echo -e "${GREEN}✅ Documents endpoint is accessible${NC}"
        
        # Show available documents
        echo -e "${YELLOW}Available documents:${NC}"
        curl -s "http://$EXTERNAL_IP/documents" | head -20
    else
        echo -e "${YELLOW}⚠️  Documents endpoint test failed (might need application restart)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  External IP not available for testing${NC}"
fi

echo ""

# Step 8: Summary
echo -e "${BLUE}📋 Summary${NC}"
echo "=================================================="
echo -e "${GREEN}🎉 Quick document update completed!${NC}"
echo ""
echo -e "${YELLOW}📊 What was done:${NC}"
echo "   • Documents copied directly to running container"
echo "   • No Docker rebuild required"
echo "   • Changes are immediately available"
echo ""
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo "   • This is a TEMPORARY fix"
echo "   • Changes will be LOST if the container restarts"
echo "   • For permanent changes, rebuild and redeploy the image"
echo ""
echo -e "${YELLOW}🔧 Next Steps:${NC}"
echo "   • Test your application with the new documents"
echo "   • If everything works, do a proper rebuild and deployment"
echo "   • Use: ./scripts/rebuild_and_deploy.sh for permanent deployment"
echo ""
echo -e "${YELLOW}🚨 To make changes permanent:${NC}"
echo "   1. Test thoroughly with this quick fix"
echo "   2. Run: ./scripts/rebuild_and_deploy.sh"
echo "   3. This will create a new image with documents baked in"
echo ""
echo -e "${GREEN}✅ Your SCONIA application now has updated documents (temporarily)!${NC}"

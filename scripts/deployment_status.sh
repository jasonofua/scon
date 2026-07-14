#!/bin/bash

# SCONIA Deployment Status Script
# Shows current deployment status and URLs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏛️  SCONIA Deployment Status${NC}"
echo "=================================================="
echo ""

# Backend Status (Kubernetes)
echo -e "${BLUE}🔧 Backend API (Kubernetes/GKE)${NC}"
echo "-------------------------------------------"

# Get backend service info
BACKEND_IP=$(kubectl get service sconia-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Not available")
BACKEND_PORT=$(kubectl get service sconia-api -o jsonpath='{.spec.ports[0].port}' 2>/dev/null || echo "80")

if [ "$BACKEND_IP" != "Not available" ]; then
    BACKEND_URL="http://$BACKEND_IP:$BACKEND_PORT"
    echo -e "${GREEN}✅ Status: Running${NC}"
    echo -e "${YELLOW}📍 External IP: $BACKEND_IP${NC}"
    echo -e "${YELLOW}🌐 API URL: $BACKEND_URL${NC}"
    
    # Test health endpoint
    echo -e "${YELLOW}🏥 Testing health endpoint...${NC}"
    if curl -f -s "$BACKEND_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Health check: PASSED${NC}"
    else
        echo -e "${RED}   ❌ Health check: FAILED${NC}"
    fi
    
    # Test API endpoints
    echo -e "${YELLOW}🔍 Testing API endpoints...${NC}"
    if curl -f -s "$BACKEND_URL/docs" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ API docs: Available${NC}"
    else
        echo -e "${RED}   ❌ API docs: Not available${NC}"
    fi
    
    # Test search endpoint
    if curl -f -s "$BACKEND_URL/api/v1/search/semantic?query=test&limit=1" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Search API: Working${NC}"
    else
        echo -e "${RED}   ❌ Search API: Not working${NC}"
    fi
else
    echo -e "${RED}❌ Status: Not running or not accessible${NC}"
fi

echo ""

# Frontend Status (Vercel)
echo -e "${BLUE}🌐 Frontend (Vercel)${NC}"
echo "-------------------------------------------"

# Check if .vercel directory exists
if [ -d "frontend/.vercel" ]; then
    # Get project info from Vercel config
    PROJECT_NAME=$(cat frontend/.vercel/project.json 2>/dev/null | grep -o '"projectName":"[^"]*"' | cut -d'"' -f4 || echo "sconia")
    
    echo -e "${GREEN}✅ Status: Deployed${NC}"
    echo -e "${YELLOW}📦 Project: $PROJECT_NAME${NC}"
    echo -e "${YELLOW}🌐 Latest URL: https://sconia-f7pwt7zjv-codeforgexs-projects.vercel.app${NC}"
    
    # Test frontend
    echo -e "${YELLOW}🧪 Testing frontend...${NC}"
    if curl -f -s "https://sconia-f7pwt7zjv-codeforgexs-projects.vercel.app" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Frontend: Accessible${NC}"
    else
        echo -e "${RED}   ❌ Frontend: Not accessible${NC}"
    fi
else
    echo -e "${RED}❌ Status: Not deployed or configuration missing${NC}"
fi

echo ""

# Environment Configuration
echo -e "${BLUE}⚙️  Environment Configuration${NC}"
echo "-------------------------------------------"

# Check frontend environment
if [ -f "frontend/.env.production" ]; then
    FRONTEND_API_URL=$(grep VITE_API_URL frontend/.env.production | cut -d'=' -f2)
    echo -e "${YELLOW}🔗 Frontend API URL: $FRONTEND_API_URL${NC}"
    
    if [ "$FRONTEND_API_URL" = "$BACKEND_URL" ]; then
        echo -e "${GREEN}   ✅ Frontend-Backend connection: Configured correctly${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Frontend-Backend connection: URLs don't match${NC}"
        echo -e "${YELLOW}      Frontend expects: $FRONTEND_API_URL${NC}"
        echo -e "${YELLOW}      Backend available at: $BACKEND_URL${NC}"
    fi
else
    echo -e "${RED}❌ Frontend environment file not found${NC}"
fi

echo ""

# Database Status
echo -e "${BLUE}🗄️  Database Status${NC}"
echo "-------------------------------------------"

if [ "$BACKEND_IP" != "Not available" ]; then
    # Test document sync endpoint
    echo -e "${YELLOW}📄 Testing document database...${NC}"
    SYNC_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/documents/sync" 2>/dev/null || echo "error")
    
    if [[ "$SYNC_RESPONSE" == *"documents"* ]]; then
        echo -e "${GREEN}   ✅ Document database: Connected${NC}"
        
        # Extract document count if available
        if [[ "$SYNC_RESPONSE" == *"qdrant_documents"* ]]; then
            DOC_COUNT=$(echo "$SYNC_RESPONSE" | grep -o '"qdrant_documents":[0-9]*' | cut -d':' -f2 || echo "unknown")
            echo -e "${YELLOW}   📊 Documents in vector DB: $DOC_COUNT${NC}"
        fi
    else
        echo -e "${RED}   ❌ Document database: Connection failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Cannot test database - backend not accessible${NC}"
fi

echo ""

# Quick Actions
echo -e "${BLUE}🚀 Quick Actions${NC}"
echo "-------------------------------------------"
echo -e "${YELLOW}Backend Management:${NC}"
echo "  • View pods: kubectl get pods -l app=sconia-api"
echo "  • View logs: kubectl logs -l app=sconia-api --tail=50"
echo "  • Scale up: kubectl scale deployment sconia-api --replicas=2"
echo "  • Update documents: ./scripts/quick_update_documents.sh"
echo ""
echo -e "${YELLOW}Frontend Management:${NC}"
echo "  • Redeploy: cd frontend && npx vercel --prod"
echo "  • View logs: npx vercel logs"
echo "  • Set custom domain: npx vercel domains add yourdomain.com"
echo ""
echo -e "${YELLOW}Full Rebuild:${NC}"
echo "  • Rebuild & redeploy: ./scripts/rebuild_and_deploy.sh"
echo ""

# Summary
echo -e "${BLUE}📋 Summary${NC}"
echo "=================================================="
if [ "$BACKEND_IP" != "Not available" ]; then
    echo -e "${GREEN}🎉 SCONIA is running successfully!${NC}"
    echo ""
    echo -e "${YELLOW}🔗 Access URLs:${NC}"
    echo -e "   Frontend: https://sconia-f7pwt7zjv-codeforgexs-projects.vercel.app"
    echo -e "   Backend API: $BACKEND_URL"
    echo -e "   API Documentation: $BACKEND_URL/docs"
    echo ""
    echo -e "${YELLOW}💡 Next Steps:${NC}"
    echo "   • Test the application functionality"
    echo "   • Set up custom domain for frontend"
    echo "   • Configure SSL/HTTPS for backend"
    echo "   • Set up monitoring and alerts"
else
    echo -e "${RED}⚠️  SCONIA backend is not accessible${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Troubleshooting:${NC}"
    echo "   • Check if Kubernetes cluster is running"
    echo "   • Verify deployment status: kubectl get deployments"
    echo "   • Check service status: kubectl get services"
    echo "   • View pod logs: kubectl logs -l app=sconia-api"
fi

echo ""
echo -e "${GREEN}✅ Deployment status check complete!${NC}"

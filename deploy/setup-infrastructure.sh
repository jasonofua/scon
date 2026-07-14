#!/bin/bash

# SCONIA Infrastructure Setup Script for Google Cloud
# Sets up databases and required services

set -e

# Configuration
PROJECT_ID="day-one-465214"
REGION="us-central1"
DB_INSTANCE_NAME="sconia-postgres"
DB_NAME="sconia"
DB_USER="sconia_user"
REDIS_INSTANCE_NAME="sconia-redis"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🏗️  SCONIA Infrastructure Setup${NC}"
echo "================================="

# Generate random password
DB_PASSWORD=$(openssl rand -base64 32)

echo -e "${BLUE}📊 Setting up Cloud SQL PostgreSQL...${NC}"

# Create Cloud SQL instance
gcloud sql instances create $DB_INSTANCE_NAME \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase

# Create database
gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE_NAME

# Create user
gcloud sql users create $DB_USER \
    --instance=$DB_INSTANCE_NAME \
    --password=$DB_PASSWORD

echo -e "${GREEN}✅ PostgreSQL database created${NC}"

echo -e "${BLUE}🔴 Setting up Redis...${NC}"

# Create Redis instance
gcloud redis instances create $REDIS_INSTANCE_NAME \
    --size=1 \
    --region=$REGION \
    --redis-version=redis_6_x

echo -e "${GREEN}✅ Redis instance created${NC}"

echo -e "${BLUE}🔐 Setting up secrets...${NC}"

# Create secrets in Secret Manager
echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=-
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-
echo -n "your-qdrant-api-key" | gcloud secrets create qdrant-api-key --data-file=-

echo -e "${GREEN}✅ Secrets created${NC}"

echo -e "${BLUE}📋 Infrastructure Summary:${NC}"
echo "=========================="
echo "Database Instance: $DB_INSTANCE_NAME"
echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"
echo "Redis Instance: $REDIS_INSTANCE_NAME"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "1. Update your secrets with actual API keys:"
echo "   gcloud secrets versions add openai-api-key --data-file=<(echo 'your-actual-openai-key')"
echo "   gcloud secrets versions add qdrant-api-key --data-file=<(echo 'your-actual-qdrant-key')"
echo ""
echo "2. Database connection string:"
echo "   postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE_NAME"
echo ""
echo "3. Get Redis IP:"
echo "   gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION"

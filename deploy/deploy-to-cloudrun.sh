#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy-to-cloudrun.sh — SCONIA Production Cloud Run Deployment Script
# ─────────────────────────────────────────────────────────────────────────────

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 SCONIA Google Cloud Run Deployment Setup${NC}"
echo "============================================="

# ── 1. Check prerequisites ────────────────────────────────────────────────────
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK (gcloud) is not installed. Please install it first.${NC}"
    exit 1
fi

# Fetch active project or prompt
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
fi
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo -e "${YELLOW}⚠️  No active project set in gcloud config.${NC}"
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    gcloud config set project "$PROJECT_ID"
else
    echo -e "${GREEN}✅ Using active GCP Project: $PROJECT_ID${NC}"
fi

# Set deployment region
if [ -z "$REGION" ]; then
    REGION="us-central1"
    read -p "Enter region [$REGION]: " input_region
    REGION="${input_region:-$REGION}"
fi

# Set configuration names
REPOSITORY="sconia"
DB_INSTANCE_NAME="sconia-postgres"
DB_NAME="sconia"
DB_USER="sconia_user"
REDIS_INSTANCE_NAME="sconia-redis"

# ── 2. Enable Google Cloud APIs ──────────────────────────────────────────────
echo -e "${BLUE}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    redis.googleapis.com \
    --quiet

echo -e "${GREEN}✅ GCP APIs enabled.${NC}"

# ── 3. Create Artifact Registry Repository ───────────────────────────────────
echo -e "${BLUE}📦 Configuring Artifact Registry...${NC}"
if gcloud artifacts repositories describe "$REPOSITORY" --location="$REGION" &>/dev/null; then
    echo -e "${YELLOW}ℹ️  Artifact repository '$REPOSITORY' already exists in $REGION${NC}"
else
    gcloud artifacts repositories create "$REPOSITORY" \
        --repository-format=docker \
        --location="$REGION" \
        --description="SCONIA Docker Images" \
        --quiet
    echo -e "${GREEN}✅ Created Artifact Registry repository: $REPOSITORY${NC}"
fi

# ── 4. Set Up Cloud SQL PostgreSQL ──────────────────────────────────────────
echo -e "${BLUE}🗄️  Setting up Cloud SQL (PostgreSQL)...${NC}"
if gcloud sql instances describe "$DB_INSTANCE_NAME" &>/dev/null; then
    echo -e "${YELLOW}ℹ️  Cloud SQL instance '$DB_INSTANCE_NAME' already exists.${NC}"
else
    echo -e "${YELLOW}Creating Cloud SQL PostgreSQL instance '$DB_INSTANCE_NAME' (db-f1-micro)...${NC}"
    gcloud sql instances create "$DB_INSTANCE_NAME" \
        --database-version=POSTGRES_14 \
        --tier=db-f1-micro \
        --region="$REGION" \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --quiet
    echo -e "${GREEN}✅ Cloud SQL instance created.${NC}"
fi

# Set up Database
if gcloud sql databases describe "$DB_NAME" --instance="$DB_INSTANCE_NAME" &>/dev/null; then
    echo -e "${YELLOW}ℹ️  Database '$DB_NAME' already exists.${NC}"
else
    gcloud sql databases create "$DB_NAME" --instance="$DB_INSTANCE_NAME"
    echo -e "${GREEN}✅ Database '$DB_NAME' created.${NC}"
fi

# Create SQL User
# Create SQL User
if [ -z "$DB_PASSWORD" ]; then
    if gcloud sql users describe "$DB_USER" --instance="$DB_INSTANCE_NAME" &>/dev/null; then
        echo -e "${YELLOW}ℹ️  Database user '$DB_USER' already exists.${NC}"
        if gcloud secrets describe "db-url" &>/dev/null; then
            DB_CONNECTION_URL=$(gcloud secrets versions access latest --secret="db-url" 2>/dev/null || echo "")
            if [ -n "$DB_CONNECTION_URL" ]; then
                DB_PASSWORD=$(echo "$DB_CONNECTION_URL" | sed -E 's/.*:\/\/[^:]+:([^@]+)@.*/\1/')
                echo -e "${GREEN}✅ Retrieved existing database password from Secret Manager.${NC}"
            fi
        fi
        
        if [ -z "$DB_PASSWORD" ]; then
            if [ "$NON_INTERACTIVE" = "true" ]; then
                DB_PASSWORD=$(openssl rand -base64 24)
                echo -e "${YELLOW}NON_INTERACTIVE=true: Generating new database password.${NC}"
            else
                read -sp "Enter database password for user '$DB_USER': " DB_PASSWORD
                echo ""
            fi
        fi
    else
        DB_PASSWORD=$(openssl rand -base64 24)
        echo -e "${YELLOW}Creating user '$DB_USER' with generated password...${NC}"
        gcloud sql users create "$DB_USER" \
            --instance="$DB_INSTANCE_NAME" \
            --password="$DB_PASSWORD"
        echo -e "${GREEN}✅ Database user '$DB_USER' created.${NC}"
    fi
else
    if gcloud sql users describe "$DB_USER" --instance="$DB_INSTANCE_NAME" &>/dev/null; then
        echo -e "${YELLOW}ℹ️  Database user '$DB_USER' already exists, using provided password.${NC}"
    else
        echo -e "${YELLOW}Creating user '$DB_USER' with provided password...${NC}"
        gcloud sql users create "$DB_USER" \
            --instance="$DB_INSTANCE_NAME" \
            --password="$DB_PASSWORD"
        echo -e "${GREEN}✅ Database user '$DB_USER' created.${NC}"
    fi
fi

# ── 5. Set Up Cloud Memorystore Redis (Optional) ─────────────────────────────
if [ -z "$USE_REDIS" ]; then
    USE_REDIS="no"
    read -p "Do you want to provision Cloud Memorystore Redis? (yes/no) [no]: " use_redis_input
    USE_REDIS="${use_redis_input:-$USE_REDIS}"
fi

REDIS_URL="memory://"
if [ "$USE_REDIS" = "yes" ] || [ "$USE_REDIS" = "y" ]; then
    echo -e "${BLUE}🔴 Setting up Redis...${NC}"
    if gcloud redis instances describe "$REDIS_INSTANCE_NAME" --region="$REGION" &>/dev/null; then
        echo -e "${YELLOW}ℹ️  Redis instance '$REDIS_INSTANCE_NAME' already exists.${NC}"
    else
        gcloud redis instances create "$REDIS_INSTANCE_NAME" \
            --size=1 \
            --region="$REGION" \
            --redis-version=redis_6_x \
            --quiet
        echo -e "${GREEN}✅ Redis instance created.${NC}"
    fi
    REDIS_IP=$(gcloud redis instances describe "$REDIS_INSTANCE_NAME" --region="$REGION" --format="value(host)")
    REDIS_URL="redis://$REDIS_IP:6379/0"
fi

# ── 6. Configure Secret Manager ──────────────────────────────────────────────
echo -e "${BLUE}🔐 Configuring Secrets in Secret Manager...${NC}"

create_or_update_secret() {
    local secret_name=$1
    local secret_val=$2
    
    if gcloud secrets describe "$secret_name" &>/dev/null; then
        echo -e "${YELLOW}Updating secret: $secret_name...${NC}"
        echo -n "$secret_val" | gcloud secrets versions add "$secret_name" --data-file=- --quiet
    else
        echo -e "${GREEN}Creating secret: $secret_name...${NC}"
        gcloud secrets create "$secret_name" --replication-policy="automatic" --quiet
        echo -n "$secret_val" | gcloud secrets versions add "$secret_name" --data-file=- --quiet
    fi
}

# DB Connection string format:
# postgresql://sconia_user:password@/sconia?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
DB_CONNECTION_URL="postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE_NAME"
create_or_update_secret "db-url" "$DB_CONNECTION_URL"

# Secret Key for security signing
APP_SECRET_KEY=$(openssl rand -base64 32)
create_or_update_secret "secret-key" "$APP_SECRET_KEY"

# External API Keys (Prompt user)
if [ -z "$GEMINI_API_KEY" ]; then
    read -p "Enter Gemini API Key (Required for model and embeddings): " GEMINI_API_KEY
fi
create_or_update_secret "gemini-key" "$GEMINI_API_KEY"

if [ -z "$QDRANT_URL" ]; then
    read -p "Enter Qdrant Cluster URL (e.g. https://xxxx.gcp.cloud.qdrant.io:6333): " QDRANT_URL
fi
create_or_update_secret "qdrant-url" "$QDRANT_URL"

if [ -z "$QDRANT_API_KEY" ]; then
    read -p "Enter Qdrant API Key: " QDRANT_API_KEY
fi
create_or_update_secret "qdrant-key" "$QDRANT_API_KEY"

# Optional OpenAI fallback
if [ -z "$OPENAI_API_KEY" ]; then
    # Check if we should prompt or default to empty
    if [ "$NON_INTERACTIVE" != "true" ]; then
        read -p "Enter OpenAI API Key (Optional, press Enter to skip): " OPENAI_API_KEY
    fi
fi
if [ -n "$OPENAI_API_KEY" ]; then
    create_or_update_secret "openai-api-key" "$OPENAI_API_KEY"
fi

# ── 7. Build Docker Images via Cloud Build ───────────────────────────────────
echo -e "${BLUE}🐳 Building backend and frontend containers...${NC}"
gcloud builds submit . \
    --config=cloudbuild.yaml \
    --substitutions=_REGION="$REGION",_REPOSITORY="$REPOSITORY",_DB_INSTANCE="$DB_INSTANCE_NAME"

# ── 8. Run Alembic Database Migrations using a Cloud Run Job ─────────────────
echo -e "${BLUE}📊 Executing Database Migrations via Cloud Run Job...${NC}"
MIGRATE_JOB="sconia-migrate-job"

# Clean up existing job if any
gcloud run jobs delete "$MIGRATE_JOB" --region="$REGION" --quiet &>/dev/null || true

gcloud run jobs create "$MIGRATE_JOB" \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/sconia-api:latest" \
    --region="$REGION" \
    --tasks=1 \
    --max-retries=0 \
    --add-cloudsql-instances="$PROJECT_ID:$REGION:$DB_INSTANCE_NAME" \
    --set-env-vars="RUN_MIGRATIONS=true,ENVIRONMENT=production" \
    --set-secrets="DATABASE_URL=db-url:latest" \
    --quiet

echo -e "${YELLOW}Executing migration job...${NC}"
gcloud run jobs execute "$MIGRATE_JOB" --region="$REGION" --wait

# ── 9. Deploy SCONIA Services to Cloud Run ──────────────────────────────────
echo -e "${BLUE}🚀 Deploying sconia-api to Cloud Run...${NC}"
gcloud run deploy sconia-api \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/sconia-api:latest" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=1 \
    --port=8080 \
    --add-cloudsql-instances="$PROJECT_ID:$REGION:$DB_INSTANCE_NAME" \
    --set-env-vars="ENVIRONMENT=production,DEBUG=False,VECTOR_DB_TYPE=qdrant,RUN_MIGRATIONS=false,REDIS_URL=$REDIS_URL" \
    --set-secrets="DATABASE_URL=db-url:latest,QDRANT_URL=qdrant-url:latest,QDRANT_API_KEY=qdrant-key:latest,GEMINI_API_KEY=gemini-key:latest,SECRET_KEY=secret-key:latest" \
    --quiet

BACKEND_URL=$(gcloud run services describe sconia-api --region="$REGION" --format="value(status.url)")
echo -e "${GREEN}✅ Backend API deployed at: $BACKEND_URL${NC}"

# Deploy Frontend proxying to Backend API
echo -e "${BLUE}🚀 Deploying sconia-frontend to Cloud Run...${NC}"
gcloud run deploy sconia-frontend \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/sconia-frontend:latest" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=0.5 \
    --port=80 \
    --set-env-vars="BACKEND_URL=$BACKEND_URL" \
    --quiet

FRONTEND_URL=$(gcloud run services describe sconia-frontend --region="$REGION" --format="value(status.url)")

# ── 10. Update CORS in Backend with Deployed Frontend URL ───────────────────
echo -e "${BLUE}🔄 Updating Backend CORS with deployed Frontend URL...${NC}"
gcloud run services update sconia-api \
    --region="$REGION" \
    --update-env-vars="ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://sconia-frontend.onrender.com,$FRONTEND_URL" \
    --quiet

echo ""
echo -e "${GREEN}🎉 SCONIA Cloud Run Deployment completed successfully!${NC}"
echo "=========================================================="
echo -e "${BLUE}📱 Frontend Web App:  $FRONTEND_URL${NC}"
echo -e "${BLUE}🔧 Backend API:       $BACKEND_URL${NC}"
echo -e "${BLUE}🏥 Health Check:      $BACKEND_URL/health${NC}"
echo "=========================================================="
echo -e "${YELLOW}Make sure to upload legal documents & initialize Qdrant vectors.${NC}"

# SCONIA System Architecture & Setup Guide

## 🏗️ **System Overview**

SCONIA (Supreme Court of Nigeria Information Assistant) is a comprehensive AI-powered legal information system designed to provide accessible information about Nigerian constitutional law, Supreme Court procedures, and legal resources through interactive kiosks and web interfaces.

## 📋 **Table of Contents**

1. [System Architecture](#system-architecture)
2. [Backend Services](#backend-services)
3. [Frontend Application](#frontend-application)
4. [Infrastructure Requirements](#infrastructure-requirements)
5. [Setup Instructions](#setup-instructions)
6. [Deployment Guide](#deployment-guide)
7. [Configuration](#configuration)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## 🏗️ **System Architecture**

### **High-Level Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Vector DB     │
│   (React/Vite)  │────│   (FastAPI)     │────│   (Qdrant)      │
│                 │    │                 │    │                 │
│ - Kiosk Mode    │    │ - Chat API      │    │ - Embeddings    │
│ - Multi-lang    │    │ - Legal APIs    │    │ - Semantic      │
│ - Responsive    │    │ - Admin APIs    │    │   Search        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   PostgreSQL    │              │
         │              │   Database      │              │
         │              │                 │              │
         │              │ - User Data     │              │
         │              │ - Sessions      │              │
         │              │ - Analytics     │              │
         │              └─────────────────┘              │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │     Redis       │    │   OpenAI API    │
│   (Nginx/GCP)   │    │     Cache       │    │                 │
│                 │    │                 │    │ - GPT-4         │
│ - SSL/TLS       │    │ - Sessions      │    │ - Embeddings    │
│ - Rate Limiting │    │ - Query Cache   │    │ - Chat          │
│ - Health Checks │    │ - Rate Limits   │    │   Completion    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Component Responsibilities**

| Component | Purpose | Technology Stack |
|-----------|---------|------------------|
| **Frontend** | User interface, kiosk mode, multi-language support | React, TypeScript, Tailwind CSS, Vite |
| **Backend API** | Business logic, AI integration, data management | Python, FastAPI, Pydantic, SQLAlchemy |
| **Vector Database** | Semantic search, document embeddings | Qdrant Cloud |
| **Primary Database** | Structured data, user sessions, analytics | PostgreSQL with pgvector |
| **Cache Layer** | Session management, query caching | Redis |
| **AI Services** | Natural language processing, embeddings | OpenAI GPT-4 & Ada-002 |
| **Load Balancer** | Traffic distribution, SSL termination | Google Cloud Load Balancer |

---

## 🔧 **Backend Services**

### **Core Service Architecture**

```
app/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── database.py            # Database connection & models
├── middleware.py          # Custom middleware (CORS, security, monitoring)
├── api/                   # API route handlers
│   ├── chat.py           # Chat and AI endpoints
│   ├── legal.py          # Legal information endpoints
│   ├── admin.py          # Administrative endpoints
│   └── search.py         # Search and discovery endpoints
├── models/               # SQLAlchemy database models
│   ├── base.py          # Base model class
│   ├── legal.py         # Legal document models
│   ├── admin.py         # User and admin models
│   └── embeddings.py    # Vector embedding models
├── schemas/             # Pydantic request/response schemas
│   ├── chat.py         # Chat API schemas
│   └── legal.py        # Legal API schemas
├── services/           # Business logic services
│   ├── chat.py        # Chat orchestration
│   ├── rag.py         # Retrieval-Augmented Generation
│   ├── vector_db.py   # Vector database operations
│   ├── embeddings.py  # Embedding generation
│   ├── query_processor.py    # Query analysis & routing
│   ├── document_processor.py # Document ingestion
│   ├── auth.py        # Authentication & authorization
│   ├── cache.py       # Caching layer
│   └── monitoring.py  # Performance monitoring
└── middleware/        # Additional middleware
    └── monitoring.py  # Request/response monitoring
```

### **Key Backend APIs**

#### **Chat & AI APIs**
- `POST /api/v1/chat/` - Main chat endpoint with AI responses
- `GET /api/v1/chat/history/{session_id}` - Retrieve chat history
- `POST /api/v1/chat/feedback` - Submit user feedback
- `WS /api/v1/chat/ws/{session_id}` - WebSocket real-time chat

#### **Legal Information APIs**
- `GET /api/v1/constitution/` - Nigerian constitution provisions
- `GET /api/v1/cases/` - Supreme Court cases
- `GET /api/v1/judges/` - Judge information
- `GET /api/v1/procedures/` - Court procedures
- `GET /api/v1/fees/` - Fee calculations

#### **Search APIs**
- `GET /api/v1/search/semantic` - Semantic document search
- `GET /api/v1/search/faceted` - Faceted search with filters
- `GET /api/v1/search/suggestions` - Search suggestions

#### **Administrative APIs**
- `POST /api/v1/admin/documents/upload` - Document upload
- `GET /api/v1/admin/system/status` - System health
- `GET /api/v1/admin/analytics/` - Usage analytics

### **Database Schema**

#### **Core Tables**
- `chat_sessions` - User chat sessions
- `queries` - Individual queries and responses
- `documents` - Legal document metadata
- `document_chunks` - Document text chunks for RAG
- `embeddings` - Vector embeddings for semantic search
- `feedback` - User feedback and ratings
- `system_metrics` - Performance and usage metrics

---

## 🎨 **Frontend Application**

### **Frontend Architecture**

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Chat/           # Chat interface components
│   │   ├── Kiosk/          # Kiosk mode components
│   │   ├── Search/         # Search interface
│   │   ├── Legal/          # Legal information displays
│   │   └── Common/         # Shared components
│   ├── services/           # API communication
│   │   └── api.ts         # Backend API integration
│   ├── types/             # TypeScript type definitions
│   │   └── index.ts       # API response types
│   ├── assets/            # Static assets
│   └── main.tsx           # Application entry point
├── public/                # Public static files
├── Dockerfile             # Development container
├── Dockerfile.prod        # Production container
└── nginx.conf            # Production web server config
```

### **Key Frontend Features**

#### **Kiosk Mode**
- **Touch-optimized interface** for public kiosks
- **Multi-language support** (English, Hausa, Yoruba, Igbo)
- **Accessibility features** (font size, contrast, voice)
- **Auto-reset** after inactivity
- **Voice input/output** capabilities

#### **Responsive Design**
- **Mobile-first** approach
- **Progressive Web App** features
- **Offline capability** for cached content
- **High contrast mode** for accessibility

#### **Multi-language System**
- **Dynamic translation** system with localStorage persistence
- **RTL/LTR** text direction support
- **Localized number/date** formatting
- **Cultural adaptation** for different regions

---

## 🏗️ **Infrastructure Requirements**

### **Production Environment**

#### **Google Cloud Platform Services**
- **Google Cloud Run** - Container hosting (auto-scaling)
- **Cloud SQL (PostgreSQL)** - Primary database
- **Cloud Memorystore (Redis)** - Caching layer
- **Cloud Storage** - Document and asset storage
- **Cloud Load Balancing** - Traffic distribution
- **Cloud Build** - CI/CD pipeline
- **Secret Manager** - Credential management
- **Cloud Monitoring** - Observability

#### **External Services**
- **Qdrant Cloud** - Vector database for embeddings
- **OpenAI API** - GPT-4 and embedding services
- **Google Cloud DNS** - Domain management

### **Resource Requirements**

#### **Backend (Cloud Run)**
```yaml
Production:
  CPU: 2 vCPU
  Memory: 4GB RAM
  Max Instances: 10
  Min Instances: 1
  Timeout: 300s

Development:
  CPU: 1 vCPU  
  Memory: 2GB RAM
  Max Instances: 3
  Min Instances: 0
```

#### **Database (Cloud SQL)**
```yaml
Production:
  Instance: db-standard-2 (2 vCPU, 7.5GB RAM)
  Storage: 100GB SSD
  Backups: Daily automated
  High Availability: Yes

Development:
  Instance: db-f1-micro (1 vCPU, 0.6GB RAM)
  Storage: 10GB SSD
```

#### **Cache (Memorystore Redis)**
```yaml
Production:
  Tier: Standard
  Memory: 1GB
  High Availability: Yes

Development:
  Tier: Basic
  Memory: 256MB
```

---

## ⚙️ **Setup Instructions**

### **Prerequisites**

#### **Development Tools**
```bash
# Required tools
- Node.js 18+ and npm
- Python 3.11+
- Docker and Docker Compose
- Google Cloud SDK (gcloud)

# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

#### **API Keys & Accounts**
- OpenAI API key with GPT-4 access
- Google Cloud account with billing enabled
- Qdrant Cloud account (or local Qdrant setup)

### **Local Development Setup**

#### **1. Clone and Setup Repository**
```bash
# Clone repository
git clone <repository-url>
cd sconia

# Copy environment configuration
cp .env.example .env
# Edit .env with your actual API keys
```

#### **2. Backend Setup**
```bash
# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up database
docker-compose up -d postgres redis qdrant

# Run database migrations
alembic upgrade head

# Initialize sample data
python scripts/init_data.py
```

#### **3. Frontend Setup**
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### **4. Start Complete System**
```bash
# Start all services
docker-compose up -d

# Verify all services are running
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:5173
```

### **Configuration Files**

#### **Environment Variables (.env)**
```bash
# Database
DATABASE_URL=postgresql://sconia_user:password@localhost:5432/sconia_db
DATABASE_URL_ASYNC=postgresql+asyncpg://sconia_user:password@localhost:5432/sconia_db

# AI Services
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-ada-002

# Vector Database
QDRANT_URL=https://your-qdrant-cluster.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key

# Cache
REDIS_URL=redis://localhost:6379/0

# Application
SECRET_KEY=your-secret-key-for-jwt
DEBUG=True
ENVIRONMENT=development
```

---

## 🚀 **Deployment Guide**

### **Production Deployment to Google Cloud**

#### **1. Setup Google Cloud Project**
```bash
# Set your project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com
```

#### **2. Setup Infrastructure**
```bash
# Run infrastructure setup
./deploy/setup-infrastructure.sh

# This creates:
# - Cloud SQL PostgreSQL instance
# - Redis instance  
# - Required secrets in Secret Manager
```

#### **3. Configure Secrets**
```bash
# Add your API keys to Secret Manager
echo "your-openai-api-key" | \
  gcloud secrets versions add openai-api-key --data-file=-

echo "your-qdrant-api-key" | \
  gcloud secrets versions add qdrant-api-key --data-file=-
```

#### **4. Deploy Application**
```bash
# Deploy both backend and frontend
./deploy/deploy.sh

# This will:
# 1. Build backend Docker image
# 2. Deploy backend to Cloud Run
# 3. Build frontend with backend URL
# 4. Deploy frontend to Cloud Run
# 5. Output both URLs
```

#### **5. Initialize Data**
```bash
# Initialize database schema
gcloud run jobs create sconia-migrate \
    --image gcr.io/$PROJECT_ID/sconia-api:latest \
    --command python \
    --args "alembic upgrade head"

gcloud run jobs execute sconia-migrate

# Load legal documents
gcloud run jobs create sconia-documents \
    --image gcr.io/$PROJECT_ID/sconia-api:latest \
    --command python \
    --args "scripts/init_data.py"

gcloud run jobs execute sconia-documents
```

### **Quick Deployment (Development)**

For a quick development deployment with minimal infrastructure:

```bash
# Use the quick-deploy script
./deploy/quick-deploy.sh

# This deploys with:
# - In-memory databases (not persistent)
# - Basic configuration
# - No external dependencies
```

---

## 📊 **Monitoring & Maintenance**

### **Health Checks**

#### **Backend Health**
```bash
# Basic health check
curl https://your-backend-url/health

# Detailed system status
curl https://your-backend-url/api/v1/admin/system/status

# Performance metrics
curl https://your-backend-url/api/v1/monitoring/metrics/system
```

#### **Database Health**
```bash
# Check database connectivity
gcloud sql instances describe sconia-postgres

# View database logs
gcloud sql operations list --instance=sconia-postgres
```

### **Logs and Debugging**

```bash
# View backend logs
gcloud run services logs read sconia-api --region=us-central1

# View frontend logs
gcloud run services logs read sconia-frontend --region=us-central1

# Stream live logs
gcloud run services logs tail sconia-api --region=us-central1
```

### **Performance Monitoring**

#### **Key Metrics to Monitor**
- **Response times** (P50, P90, P95, P99)
- **Error rates** (<1% for critical APIs)
- **Database connections** and query performance
- **Memory usage** and CPU utilization
- **Cache hit rates** (>80% for frequently accessed data)
- **AI API costs** and usage patterns

#### **Alerts Setup**
```bash
# CPU usage alert
gcloud monitoring policies create cpu-alert.yaml

# Error rate alert  
gcloud monitoring policies create error-rate-alert.yaml

# Database connection alert
gcloud monitoring policies create db-connection-alert.yaml
```

### **Backup and Recovery**

#### **Database Backups**
```bash
# Manual backup
gcloud sql backups create --instance=sconia-postgres

# Automated backups are enabled by default
# Point-in-time recovery available for 7 days
```

#### **Application Backup**
```bash
# Backup vector database
curl -X POST "https://your-qdrant-cluster.qdrant.io:6333/collections/sconia/snapshots"

# Download configuration
gcloud secrets versions access latest --secret="sconia-config" > backup-config.json
```

---

## 🔒 **Security Considerations**

### **Authentication & Authorization**
- **JWT-based authentication** for admin APIs
- **Rate limiting** (60 requests/minute per IP)
- **Input validation** and sanitization
- **SQL injection protection** via SQLAlchemy ORM

### **Data Protection**
- **Encryption at rest** for databases
- **Encryption in transit** (TLS 1.2+)
- **API key management** via Secret Manager
- **No sensitive data logging**

### **Network Security**
- **VPC networking** for internal communication
- **Firewall rules** restricting access
- **DDoS protection** via Google Cloud
- **Security headers** (CSP, HSTS, etc.)

---

## 📈 **Scaling Considerations**

### **Horizontal Scaling**
- **Auto-scaling Cloud Run** instances (0-10)
- **Load balancing** across multiple regions
- **Database read replicas** for read-heavy workloads
- **CDN integration** for static assets

### **Performance Optimization**
- **Connection pooling** for database
- **Query result caching** in Redis
- **Embedding caching** to reduce AI API costs
- **Async processing** for heavy operations

---

## 🆘 **Troubleshooting Guide**

### **Common Issues**

#### **"API Timeouts"**
```bash
# Check backend health
curl https://your-backend-url/health

# Increase timeout in frontend .env
VITE_API_TIMEOUT=60000

# Check database connections
gcloud sql instances describe sconia-postgres
```

#### **"Language Selection Not Working"**
```bash
# Verify translation files exist
ls frontend/src/components/Kiosk/KioskMode.tsx

# Check browser localStorage
# localStorage.getItem('sconia-language')

# Rebuild frontend
cd frontend && npm run build
```

#### **"Vector Search Not Working"**
```bash
# Check Qdrant connection
curl https://your-qdrant-cluster.qdrant.io:6333/collections

# Verify embeddings exist
curl "https://your-backend-url/api/v1/search/stats"

# Re-initialize vector database
python scripts/init_vector_db.py
```

---

## 📞 **Support & Resources**

### **Documentation**
- `README.md` - Quick start guide
- `frontend/FIXES_DOCUMENTATION.md` - Recent fixes and updates
- API documentation at `/docs` endpoint

### **Development Resources**
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **React Documentation**: https://reactjs.org
- **Google Cloud Documentation**: https://cloud.google.com/docs

### **Getting Help**
1. Check the troubleshooting guide above
2. Review application logs
3. Test individual components
4. Verify configuration settings

---

**This documentation provides a complete overview of the SCONIA system architecture and setup procedures. The system is designed to be scalable, maintainable, and accessible to users across Nigeria.**
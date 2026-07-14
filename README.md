# SCONIA - Supreme Court of Nigeria Information Assistant

An AI-powered digital information system deployed on touchscreen kiosks across Nigerian courts nationwide. SCONIA provides accurate, accessible legal information to citizens, legal practitioners, students, and court visitors through an intuitive touchscreen interface with natural language processing capabilities.

## Features

- **AI-Powered Chat Interface**: Natural language processing for legal queries
- **Comprehensive Legal Database**: Nigerian Constitution, Supreme Court cases, procedures
- **Real-time Information**: Court schedules, judge profiles, fee calculations
- **Multi-modal Search**: Semantic search, keyword search, and structured queries
- **Touchscreen Optimized**: Designed for kiosk deployment across Nigerian courts
- **Content Management**: Admin dashboard for updating legal information
- **Analytics & Monitoring**: Usage tracking and performance monitoring

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Primary database for structured data
- **Qdrant**: Vector database for semantic search
- **Redis**: Caching and session management
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migrations

### AI/ML
- **OpenAI GPT-4**: Large language model for responses
- **LangChain**: AI application framework
- **Sentence Transformers**: Text embeddings
- **RAG Pipeline**: Retrieval-Augmented Generation

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration
- **Uvicorn**: ASGI server

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key

### 1. Clone the Repository
```bash
git clone <repository-url>
cd sconia
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# Especially set your OPENAI_API_KEY
```

### 3. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Initialize Database
```bash
# Run database migrations
docker-compose exec api alembic upgrade head

# Initialize with sample data
docker-compose exec api python scripts/init_data.py
```

### 5. Access the Application
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Chat Endpoint**: http://localhost:8000/api/v1/chat

## Development Setup

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Start database services only
docker-compose up -d postgres qdrant redis

# Run migrations
alembic upgrade head

# Initialize data
python scripts/init_data.py

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Reset database (development only)
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
python scripts/init_data.py
```

## API Usage

### Chat Endpoint
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the fundamental rights in the Nigerian Constitution?",
    "session_id": "test-session-123"
  }'
```

### WebSocket Chat
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws/session-123');

ws.onopen = function() {
    ws.send(JSON.stringify({
        type: 'query',
        query: 'Tell me about the Supreme Court of Nigeria'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Response:', data);
};
```

## Project Structure

```
sconia/
├── app/
│   ├── api/                 # API routes
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   └── main.py              # FastAPI application
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
├── tests/                   # Test files
├── docker-compose.yml       # Docker services
├── Dockerfile               # Container definition
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Configuration

Key environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `QDRANT_URL`: Qdrant vector database URL
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key
- `DEBUG`: Enable debug mode

## Default Credentials

**Admin User** (Change in production):
- Username: `admin`
- Password: `admin123`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation at `/docs` endpoint

## Roadmap

- [ ] Complete RAG pipeline implementation
- [ ] Frontend React application
- [ ] Mobile app development
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Voice interface integration
- [ ] Offline capability for kiosks

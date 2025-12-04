# Smart Research Assistant

> AI-Powered Research Tool with RAG (Retrieval Augmented Generation) using Google Gemini 2.0

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready AI research assistant that ingests documents from multiple sources, processes them using intelligent chunking, generates embeddings with Google Gemini, and provides accurate answers with proper citations using RAG.

## Features

- **Multi-Source Document Ingestion**
  - Web articles (BeautifulSoup4 scraping)
  - PDF files (pdfplumber)
  - YouTube videos (transcript extraction)
  - Plain text (Markdown support)

- **Intelligent Text Processing**
  - Semantic chunking with paragraph awareness
  - Configurable chunk sizes and overlap
  - Metadata preservation for citations

- **AI-Powered RAG System**
  - Google Gemini 2.0 Flash for responses
  - Gemini text-embedding-004 for embeddings
  - ChromaDB vector storage
  - Context-aware question answering
  - Streaming responses

- **Production Features**
  - Async FastAPI backend
  - PostgreSQL database with Alembic migrations
  - Celery task queue for async processing
  - Redis caching
  - Docker containerization
  - Comprehensive error handling
  - Structured logging
  - Type safety with Pydantic

## Architecture

```
┌─────────────────┐
│  Client/User    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ Document │  │   Chat   │  │ Health ││
│  │ Routers  │  │ Routers  │  │ Check  ││
│  └──────────┘  └──────────┘  └────────┘│
└───────┬─────────────┬───────────────────┘
        │             │
        ▼             ▼
┌──────────────┐  ┌──────────────┐
│   Celery     │  │  RAG Service │
│   Workers    │  │  (Gemini)    │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │   ChromaDB   │
│   Database   │  │  (Vectors)   │
└──────────────┘  └──────────────┘
```

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI (async web framework)
- SQLAlchemy 2.0 (async ORM)
- Pydantic v2 (validation)
- PostgreSQL 15+ (database)
- Redis 7+ (caching/queue)
- Celery (async tasks)

**AI/ML:**
- Google Gemini 2.0 Flash (generation)
- Google text-embedding-004 (embeddings)
- ChromaDB (vector store)

**Document Processing:**
- BeautifulSoup4 (web scraping)
- pdfplumber (PDF parsing)
- youtube-transcript-api (YouTube)

**Deployment:**
- Docker + Docker Compose
- GCP Cloud Run ready
- Alembic (migrations)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Gemini API Key ([Get it here](https://makersuite.google.com/app/apikey))

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/smart-research-assistant.git
cd smart-research-assistant
```

### 2. Setup with Docker Compose (Recommended)

```bash
# Copy environment file
cp backend/.env.example backend/.env

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your_api_key_here

# Start all services
cd backend
docker-compose up -d

# Check logs
docker-compose logs -f api
```

The API will be available at `http://localhost:8000`

### 3. Manual Setup (Alternative)

```bash
# Run setup script
chmod +x scripts/setup-local.sh
./scripts/setup-local.sh

# Activate virtual environment
cd backend
source venv/bin/activate

# Update .env with your API key

# Start databases
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload

# In another terminal, start Celery worker
celery -A app.tasks worker --loglevel=info
```

## Usage Examples

### 1. Upload a Document

**Upload URL (Web Article):**
```bash
curl -X POST http://localhost:8000/api/documents/upload-url \
  -H "Content-Type: application/json" \
  -d '{
    "type": "url",
    "url": "https://en.wikipedia.org/wiki/Machine_learning"
  }'
```

**Upload PDF:**
```bash
curl -X POST http://localhost:8000/api/documents/upload-pdf \
  -F "file=@/path/to/your/document.pdf"
```

**Upload YouTube Video:**
```bash
curl -X POST http://localhost:8000/api/documents/upload-url \
  -H "Content-Type: application/json" \
  -d '{
    "type": "youtube",
    "url": "https://www.youtube.com/watch?v=aircAruvnKk"
  }'
```

**Upload Text:**
```bash
curl -X POST http://localhost:8000/api/documents/upload-text \
  -H "Content-Type: application/json" \
  -d '{
    "type": "text",
    "text": "Your text content here...",
    "title": "My Research Notes",
    "author": "Your Name"
  }'
```

### 2. Ask Questions

**Non-Streaming:**
```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?",
    "include_sources": true
  }'
```

**Streaming Response:**
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain neural networks",
    "conversation_id": null
  }'
```

### 3. Manage Conversations

**List Conversations:**
```bash
curl http://localhost:8000/api/conversations
```

**Get Conversation Details:**
```bash
curl http://localhost:8000/api/conversations/{conversation_id}
```

**Delete Conversation:**
```bash
curl -X DELETE http://localhost:8000/api/conversations/{conversation_id}
```

### 4. Manage Documents

**List All Documents:**
```bash
curl http://localhost:8000/api/documents
```

**Get Document Details:**
```bash
curl http://localhost:8000/api/documents/{document_id}
```

**Delete Document:**
```bash
curl -X DELETE http://localhost:8000/api/documents/{document_id}
```

## API Documentation

Once the server is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Configuration

Key environment variables in `backend/.env`:

```bash
# Required
GOOGLE_API_KEY=your_google_gemini_api_key

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/research_assistant

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# RAG Configuration
CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K_RETRIEVAL=10
TOP_K_CONTEXT=5
RELEVANCE_THRESHOLD=0.3

# Gemini Models
GEMINI_CHAT_MODEL=gemini-2.0-flash-exp
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

## Project Structure

```
smart-research-assistant/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   │   ├── ingestion/   # Document processors
│   │   │   ├── chunker.py
│   │   │   ├── embedding_service.py
│   │   │   ├── vector_store.py
│   │   │   ├── rag_service.py
│   │   │   └── gemini_client.py
│   │   ├── routers/         # API endpoints
│   │   ├── tasks/           # Celery tasks
│   │   ├── utils/           # Utilities
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── alembic/             # Database migrations
│   ├── tests/               # Unit tests
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── scripts/                 # Deployment scripts
├── sample_data/             # Sample documents
└── README.md
```

## Testing

Run the test suite:

```bash
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_api.py -v
```

Run API integration tests:

```bash
chmod +x ../scripts/test-api.sh
../scripts/test-api.sh
```

## Deployment

### GCP Cloud Run

1. **Setup GCP Project:**
   ```bash
   gcloud init
   gcloud config set project your-project-id
   ```

2. **Configure Services:**
   - Create Cloud SQL PostgreSQL instance
   - Create Cloud Memorystore Redis instance
   - Set up Cloud Storage bucket for PDFs

3. **Deploy:**
   ```bash
   chmod +x scripts/deploy-gcp.sh
   # Edit script with your project details
   ./scripts/deploy-gcp.sh
   ```

### Docker Deployment

```bash
# Build image
docker build -t smart-research-assistant:latest backend/

# Run with docker-compose
docker-compose up -d

# Scale workers
docker-compose up -d --scale celery_worker=3
```

## Performance Considerations

- **Async Processing:** All I/O operations are async for better performance
- **Batch Embeddings:** Embeddings are generated in batches
- **Connection Pooling:** Database connections are pooled
- **Caching:** Redis caching for frequently accessed data
- **Streaming:** Large responses are streamed to reduce memory usage

## Security Features

- Input validation with Pydantic
- URL validation (blocks localhost/private IPs)
- File type and size validation
- SQL injection prevention (ORM)
- Environment-based configuration
- Rate limiting ready

## Monitoring

Access Flower (Celery monitoring):
```bash
http://localhost:5555
```

View logs:
```bash
# API logs
docker-compose logs -f api

# Celery logs
docker-compose logs -f celery_worker

# All logs
docker-compose logs -f
```

## Troubleshooting

**Database connection issues:**
```bash
# Check PostgreSQL
docker-compose ps postgres
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

**Celery not processing:**
```bash
# Check Redis
docker-compose ps redis
docker-compose logs redis

# Restart worker
docker-compose restart celery_worker
```

**API errors:**
```bash
# Check API logs
docker-compose logs api

# Verify environment variables
docker-compose exec api env | grep GOOGLE_API_KEY
```

## Future Enhancements

- [ ] Frontend UI (React/Next.js)
- [ ] User authentication & authorization
- [ ] Multi-user support with workspaces
- [ ] Advanced search filters
- [ ] Document summarization
- [ ] Export conversations to PDF/Markdown
- [ ] Integration with more sources (Google Drive, Notion, etc.)
- [ ] Fine-tuning support for domain-specific use cases
- [ ] Hybrid search (keyword + semantic)
- [ ] Citation graph visualization

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Gemini API for powerful AI capabilities
- FastAPI for the excellent async framework
- ChromaDB for vector storage
- The open-source community

---

# Quick Start Guide

Get your Smart Research Assistant up and running in 5 minutes!

## Step 1: Prerequisites

Make sure you have:
- Docker and Docker Compose installed
- A Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))

## Step 2: Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/smart-research-assistant.git
cd smart-research-assistant

# Copy environment file
cp backend/.env.example backend/.env

# Edit .env and add your Google API key
nano backend/.env  # or use your favorite editor
# Set: GOOGLE_API_KEY=your_actual_api_key_here
```

## Step 3: Start the Application

```bash
cd backend
docker-compose up -d
```

Wait about 30 seconds for all services to start.

## Step 4: Verify Installation

Check if everything is running:

```bash
docker-compose ps
```

You should see:
- postgres (healthy)
- redis (healthy)
- api (running)
- celery_worker (running)
- flower (running)

## Step 5: Test the API

Visit http://localhost:8000/docs in your browser to see the interactive API documentation.

Or use curl:

```bash
curl http://localhost:8000/health | jq
```

## Step 6: Upload Your First Document

```bash
curl -X POST http://localhost:8000/api/documents/upload-text \
  -H "Content-Type: application/json" \
  -d '{
    "type": "text",
    "text": "Artificial Intelligence (AI) is transforming various industries including healthcare, finance, and transportation. Machine learning, a subset of AI, enables systems to learn from data without explicit programming.",
    "title": "Introduction to AI"
  }'
```

Save the `id` from the response.

## Step 7: Ask a Question

Wait 10-15 seconds for the document to be processed, then:

```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What industries is AI transforming?",
    "include_sources": true
  }' | jq
```

You should get an answer with citations!

## Next Steps

- **Explore the API**: Visit http://localhost:8000/docs
- **Monitor Tasks**: Visit http://localhost:5555 (Flower dashboard)
- **Upload More Documents**: Try PDFs, URLs, and YouTube videos
- **Read the Full README**: See README.md for complete documentation

## Common Commands

```bash
# View logs
docker-compose logs -f api

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Stop and remove all data
docker-compose down -v

# Run tests
docker-compose exec api pytest
```

## Troubleshooting

**Services won't start?**
```bash
docker-compose down -v
docker-compose up -d
```

**Can't connect to database?**
```bash
docker-compose logs postgres
# Make sure it shows "database system is ready to accept connections"
```

**Gemini API errors?**
- Check your API key in backend/.env
- Verify your Google Cloud billing is enabled
- Check API quotas in Google Cloud Console

## Need Help?

- Check the main [README.md](README.md)
- Open an issue on GitHub
- Check logs: `docker-compose logs -f`

---

Happy researching! 🚀

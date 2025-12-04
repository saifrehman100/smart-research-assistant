#!/bin/bash

# Local development setup script for Smart Research Assistant

set -e

echo "🚀 Setting up Smart Research Assistant for local development..."

# Check if Python 3.11+ is installed
echo "Checking Python version..."
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$python_version < 3.11" | bc -l) )); then
    echo "❌ Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python version: $(python3 --version)"

# Create virtual environment
echo "Creating virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy .env.example to .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your Google API key and other settings"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p uploads chroma_data logs

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker is not installed. Please install Docker to run PostgreSQL and Redis."
    echo "   You can also install them locally if preferred."
else
    echo "✅ Docker is installed"

    # Start databases with docker-compose
    echo "Starting PostgreSQL and Redis with Docker Compose..."
    docker-compose up -d postgres redis

    echo "Waiting for databases to be ready..."
    sleep 5
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your GOOGLE_API_KEY"
echo "2. Activate virtual environment: cd backend && source venv/bin/activate"
echo "3. Start the API server: uvicorn app.main:app --reload"
echo "4. Start Celery worker: celery -A app.tasks worker --loglevel=info"
echo "5. Visit http://localhost:8000/docs for API documentation"
echo ""

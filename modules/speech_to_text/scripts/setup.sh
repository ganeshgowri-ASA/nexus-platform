#!/bin/bash
# Setup script for NEXUS Speech-to-Text module

set -e

echo "🚀 Setting up NEXUS Speech-to-Text Module"

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.9+ is required. Found: $python_version"
    exit 1
fi
echo "✅ Python version OK: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check FFmpeg
echo "🎵 Checking FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg is installed"
else
    echo "⚠️  Warning: FFmpeg is not installed"
    echo "   Install it with:"
    echo "   - Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "   - macOS: brew install ffmpeg"
    echo "   - Windows: Download from https://ffmpeg.org/download.html"
fi

# Create .env file if it doesn't exist
echo "⚙️  Setting up configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env with your configuration"
else
    echo "ℹ️  .env file already exists"
fi

# Create upload directory
echo "📁 Creating upload directory..."
mkdir -p uploads/audio
echo "✅ Upload directory created"

# Check PostgreSQL
echo "🐘 Checking PostgreSQL connection..."
if [ -n "$DATABASE_URL" ]; then
    echo "ℹ️  DATABASE_URL is set"
else
    echo "⚠️  Warning: DATABASE_URL not set in environment"
    echo "   Please configure PostgreSQL connection in .env"
fi

# Check Redis
echo "🔴 Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Warning: Redis is not running"
        echo "   Start it with: redis-server"
    fi
else
    echo "ℹ️  redis-cli not found. Install Redis if needed."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Start PostgreSQL and Redis"
echo "3. Initialize database: python -c 'from config.database import init_db; init_db()'"
echo "4. Start API: uvicorn api.app:app --reload"
echo "5. Start Celery: celery -A tasks.celery_app worker --loglevel=info"
echo "6. Start UI: streamlit run ui/app.py"
echo ""
echo "Or use Docker: docker-compose up"

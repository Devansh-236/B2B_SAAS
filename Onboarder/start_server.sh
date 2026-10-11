#!/bin/bash

# Onboarder API Server Startup Script

# Run from the directory containing this script
cd "$(dirname "$0")" || exit 1

echo "🚀 Starting Onboarder API Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is available for this Python
if ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip is required but not available for python3 (try: python3 -m ensurepip)."
    exit 1
fi

# Check .env before installing anything
if [ ! -f ".env" ]; then
    echo "❌ .env file not found."
    echo "   Create it from the example and set your Gemini API key:"
    echo "     cp env.example .env"
    echo "     # then edit .env and set GEMINI_API_KEY"
    exit 1
fi

if ! grep -Eq '^GEMINI_API_KEY=.+' .env || grep -q '^GEMINI_API_KEY=your_gemini_api_key_here' .env; then
    echo "❌ GEMINI_API_KEY is missing or still set to the placeholder in .env."
    echo "   Edit .env and set GEMINI_API_KEY to your real key."
    exit 1
fi

# Install runtime dependencies
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    if ! python3 -m pip install -r requirements.txt; then
        echo "❌ Failed to install dependencies."
        exit 1
    fi
else
    echo "⚠️  requirements.txt not found. Make sure dependencies are installed."
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "
import sys
from onboarder.database_manager import DatabaseManager
try:
    db = DatabaseManager()
    print('✅ Database initialized successfully')
    print(f'   - Database file: {db.db_path}')
    print('   - Employee IDs will be auto-generated')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Start the server (host/port come from ONBOARDER_HOST / ONBOARDER_PORT in .env)
echo "🌐 Starting FastAPI server (default http://127.0.0.1:8050)"
echo "📖 API documentation available at /docs and /redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 main.py

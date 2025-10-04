#!/bin/bash

# Onboarder API Server Startup Script

echo "🚀 Starting Onboarder API Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies."
        exit 1
    fi
else
    echo "⚠️  requirements.txt not found. Make sure dependencies are installed."
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from example..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "📝 Please edit .env file with your API keys before starting the server."
    else
        echo "❌ No .env file or env.example found. Please create .env with required environment variables."
        exit 1
    fi
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "
from onboarder.database_manager import DatabaseManager
try:
    db = DatabaseManager()
    print('✅ Database initialized successfully')
    print('   - Schema created/verified')
    print('   - Employee IDs will be auto-generated')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8050"
echo "📖 API documentation available at http://localhost:8050/docs"
echo "🔧 Admin interface available at http://localhost:8050/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 main.py

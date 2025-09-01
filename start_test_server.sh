#!/bin/bash

# 🚀 GitHub Background Processing Test Server
# This script starts the test server and runs the background processing tests

echo "🚀 Starting LinkedIn Recommendation Writer Test Server"
echo "======================================================"

# Check if we're in the right directory
if [ ! -f "backend/app/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   cd /home/day/ProgrammingProjects/github_repo_linkedin_recommendation_writer_app"
    exit 1
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis is not running. Starting Redis..."
    if command -v docker &> /dev/null; then
        docker run -d -p 6379:6379 --name redis-test redis:7-alpine
        sleep 3
    else
        echo "❌ Docker not found. Please start Redis manually:"
        echo "   redis-server"
        exit 1
    fi
fi

# Set environment variables
export ENVIRONMENT=development
export API_HOST=0.0.0.0
export API_PORT=8000
export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/github_recommender

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp backend/.env.example backend/.env
    echo "✅ .env file created. Please edit it with your API keys:"
    echo "   GITHUB_TOKEN=your_github_token"
    echo "   GEMINI_API_KEY=your_gemini_api_key"
fi

# Start the server
echo "🚀 Starting FastAPI server..."
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 5

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Server failed to start. Check the logs above."
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo "✅ Server started successfully!"
echo ""
echo "🌐 API available at: http://localhost:8000"
echo "📚 API documentation: http://localhost:8000/docs"
echo "🏥 Health check: http://localhost:8000/health"
echo ""
echo "🧪 Running background processing tests..."
echo ""

# Run the tests
cd ..
python test_background_processing.py

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $SERVER_PID 2>/dev/null

# Stop Redis if we started it
if docker ps | grep -q redis-test; then
    docker stop redis-test
    docker rm redis-test
fi

echo "✅ Test completed!"
echo ""
echo "📖 For more information, see: BACKGROUND_PROCESSING_README.md"

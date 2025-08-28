#!/bin/bash

# 🚀 LinkedIn Recommendation Writer - Docker Deployment
# Uses custom Dockerfile for reliable single-project deployment

echo "🚀 LinkedIn Recommendation Writer - Docker Deployment"
echo "===================================================="
echo ""
echo "This uses a custom Dockerfile - most reliable approach!"
echo ""

# Check if user has API keys ready
echo "🔑 API Keys Required"
echo "==================="
echo ""
echo "You'll need:"
echo "- GitHub Token: https://github.com/settings/tokens"
echo "- Gemini API Key: https://makersuite.google.com/app/apikey"
echo ""

read -p "Do you have your API keys ready? (y/n): " KEYS_READY
if [[ ! "$KEYS_READY" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please get your API keys first, then run this script again."
    echo "GitHub: https://github.com/settings/tokens"
    echo "Gemini: https://makersuite.google.com/app/apikey"
    exit 1
fi

echo ""
echo "📋 Docker Deployment Steps"
echo "=========================="

echo ""
echo "Step 1: Create Railway Project"
echo "------------------------------"
echo "1. Open: https://railway.app/dashboard"
echo "2. Click 'New Project'"
echo "3. Choose 'Deploy from GitHub repo'"
echo "4. Select your GitHub repository"
echo "5. ⚠️  IMPORTANT: Railway will detect the Dockerfile automatically!"
echo "6. Name: linkedin-recommendation-writer"
echo "7. Click 'Deploy'"
echo ""

read -p "✅ Have you created the project? (y/n): " PROJECT_CREATED
if [[ ! "$PROJECT_CREATED" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please create the project first."
    xdg-open https://railway.app/dashboard 2>/dev/null || echo "Visit: https://railway.app/dashboard"
    exit 1
fi

echo ""
echo "Step 2: Railway Auto-Detects Dockerfile"
echo "---------------------------------------"
echo "Railway should automatically:"
echo "✅ Detect your custom Dockerfile"
echo "✅ Build using Docker instead of Nixpacks"
echo "✅ Install Python dependencies"
echo "✅ Install Node.js dependencies"
echo "✅ Build your React frontend"
echo "✅ Copy frontend to backend"
echo "✅ Start FastAPI server"
echo ""

read -p "✅ Did Railway detect and start building with Docker? (y/n): " DOCKER_DETECTED
if [[ ! "$DOCKER_DETECTED" =~ ^[Yy]$ ]]; then
    echo ""
    echo "If Railway didn't detect the Dockerfile:"
    echo "1. Go to your Railway project settings"
    echo "2. Make sure Dockerfile is in the root directory"
    echo "3. Try redeploying"
    exit 1
fi

echo ""
echo "Step 3: Add Services (PostgreSQL & Redis)"
echo "-----------------------------------------"
echo "While building, add the services:"
echo "1. Click 'Add Plugin' → Add 'PostgreSQL'"
echo "2. Click 'Add Plugin' → Add 'Redis'"
echo ""

read -p "✅ Have you added PostgreSQL and Redis? (y/n): " SERVICES_ADDED
if [[ ! "$SERVICES_ADDED" =~ ^[Yy]$ ]]; then
    echo "Please add the services."
    exit 1
fi

echo ""
echo "Step 4: Set Environment Variables"
echo "---------------------------------"
echo "In Railway project Variables tab, add:"
echo ""

read -p "GitHub Token: " GITHUB_TOKEN
read -p "Gemini API Key: " GEMINI_API_KEY

echo ""
echo "Add these to Railway Variables:"
echo "GITHUB_TOKEN = $GITHUB_TOKEN"
echo "GEMINI_API_KEY = $GEMINI_API_KEY"
echo "ENVIRONMENT = production"
echo "API_DEBUG = false"
echo "API_RELOAD = false"
echo "LOG_LEVEL = INFO"
echo ""

read -p "✅ Have you set all environment variables? (y/n): " VARS_SET
if [[ ! "$VARS_SET" =~ ^[Yy]$ ]]; then
    echo "Please set the environment variables."
    exit 1
fi

echo ""
echo "Step 5: Wait for Deployment"
echo "---------------------------"
echo "Railway will:"
echo "✅ Build your custom Docker image"
echo "✅ Install all dependencies"
echo "✅ Build and copy frontend"
echo "✅ Start the FastAPI server"
echo "✅ Make your app available!"
echo ""

read -p "✅ Has deployment completed successfully? (y/n): " DEPLOYED
if [[ ! "$DEPLOYED" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Check the deployment logs in Railway dashboard."
    echo "The custom Dockerfile should resolve the pip issues."
    exit 1
fi

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"

echo ""
echo "🌐 Your Application:"
echo "- Main App: Check your Railway project URL"
echo "- API: /api/v1/"
echo "- Health: /health"
echo "- Docs: /docs"
echo ""

echo "🔧 What the Dockerfile does:"
echo "- ✅ Installs Python and Node.js"
echo "- ✅ Builds React frontend"
echo "- ✅ Copies frontend to backend static files"
echo "- ✅ Starts FastAPI server that serves both"
echo ""

echo "🚀 This approach avoids all Nixpacks issues!"
echo ""
echo "✅ Success! Your LinkedIn Recommendation Writer is live! 🎉"

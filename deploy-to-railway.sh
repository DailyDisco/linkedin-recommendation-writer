#!/bin/bash

# 🚀 LinkedIn Recommendation Writer - Railway Deployment Script
# This script deploys backend and frontend as separate Railway services

set -e

echo "🚀 LinkedIn Recommendation Writer - Railway Deployment"
echo "======================================================"
echo "📋 This script deploys backend and frontend as separate services (recommended)"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed."
    echo "Install it with: npm install -g @railway/cli"
    exit 1
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway:"
    railway login
fi

# Function to deploy backend
deploy_backend() {
    echo ""
    echo "🔧 Deploying Backend Service..."
    echo "================================"

    cd backend

    # Create backend project
    echo "📦 Creating backend Railway project..."
    railway init linkedin-recommendation-backend --yes

    # Add required plugins
    echo "🗄️ Adding PostgreSQL database..."
    railway add postgresql --name linkedin-recommendation-db

    echo "🔄 Adding Redis cache..."
    railway add redis --name linkedin-recommendation-redis

    # Set environment variables
    echo "⚙️ Configuring backend environment variables..."

    # Set production variables
    railway variables set ENVIRONMENT=production
    railway variables set API_DEBUG=false
    railway variables set API_RELOAD=false
    railway variables set LOG_LEVEL=INFO

    # Get API keys from user
    echo ""
    echo "🔑 Please provide your API keys:"
    read -p "GitHub Personal Access Token: " GITHUB_TOKEN
    read -p "Google Gemini API Key: " GEMINI_API_KEY

    if [[ -z "$GITHUB_TOKEN" ]] || [[ -z "$GEMINI_API_KEY" ]]; then
        echo "❌ API keys are required. Exiting..."
        exit 1
    fi

    railway variables set GITHUB_TOKEN="$GITHUB_TOKEN"
    railway variables set GEMINI_API_KEY="$GEMINI_API_KEY"

    echo "🚀 Deploying backend..."
    railway up

    # Get backend URL
    BACKEND_URL=$(railway domain)
    echo "✅ Backend deployed at: $BACKEND_URL"

    cd ..
    echo "$BACKEND_URL" > .backend_url
}

# Function to deploy frontend
deploy_frontend() {
    echo ""
    echo "🎨 Deploying Frontend Service..."
    echo "================================"

    cd frontend

    # Create frontend project
    echo "📦 Creating frontend Railway project..."
    railway init linkedin-recommendation-frontend --yes

    # Set environment variables
    echo "⚙️ Configuring frontend environment variables..."

    # Read backend URL
    if [[ -f "../.backend_url" ]]; then
        BACKEND_URL=$(cat ../.backend_url)
        echo "🔗 Using backend URL: $BACKEND_URL"
        railway variables set VITE_API_BASE_URL="$BACKEND_URL"
        railway variables set VITE_API_TIMEOUT=30000
        railway variables set NODE_ENV=production
    else
        echo "⚠️ Backend URL not found. Please set VITE_API_BASE_URL manually after deployment."
    fi

    echo "🚀 Deploying frontend..."
    railway up

    # Get frontend URL
    FRONTEND_URL=$(railway domain)
    echo "✅ Frontend deployed at: $FRONTEND_URL"

    cd ..
}

# Main deployment
echo "📋 Deployment Options:"
echo "1. Deploy both backend and frontend (recommended)"
echo "2. Deploy backend only"
echo "3. Deploy frontend only"
echo ""

read -p "Choose deployment option (1-3): " DEPLOY_OPTION

case $DEPLOY_OPTION in
    1)
        echo "🚀 Deploying both services..."
        deploy_backend
        deploy_frontend
        ;;
    2)
        echo "🚀 Deploying backend only..."
        deploy_backend
        ;;
    3)
        echo "🚀 Deploying frontend only..."
        deploy_frontend
        ;;
    *)
        echo "❌ Invalid option. Exiting..."
        exit 1
        ;;
esac

# Cleanup
if [[ -f ".backend_url" ]]; then
    rm .backend_url
fi

echo ""
echo "🎉 Deployment Summary:"
echo "===================="

if [[ -n "$BACKEND_URL" ]]; then
    echo "🔧 Backend: $BACKEND_URL"
    echo "📚 API Docs: $BACKEND_URL/docs"
    echo "💚 Health: $BACKEND_URL/health"
fi

if [[ -n "$FRONTEND_URL" ]]; then
    echo "🎨 Frontend: $FRONTEND_URL"
fi

echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Test your application by visiting the frontend URL"
echo "2. Check API documentation at backend/docs"
echo "3. Monitor logs: railway logs"
echo "4. If needed, update CORS: railway variables set ALLOWED_ORIGINS=$FRONTEND_URL"

echo ""
echo "✅ Deployment completed successfully!"
echo "🎉 Your LinkedIn Recommendation Writer is now live on Railway!"

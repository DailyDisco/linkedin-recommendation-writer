#!/bin/bash

# 🚀 LinkedIn Recommendation Writer - Railway Deployment Script
# This script helps you deploy your application to Railway

set -e

echo "🚀 LinkedIn Recommendation Writer - Railway Deployment"
echo "======================================================"

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

echo "📋 Deployment Checklist:"
echo "1. ✅ GitHub repository connected"
echo "2. ✅ PostgreSQL plugin will be added automatically"
echo "3. ✅ Redis plugin will be added automatically"
echo "4. 🔄 Setting up environment variables..."

# Create a new Railway project or link existing
if [ ! -f ".railway/project.json" ]; then
    echo "🔗 Creating new Railway project..."
    railway init linkedin-recommendation-writer
else
    echo "🔗 Linking to existing Railway project..."
    railway link
fi

# Add required plugins
echo "🗄️ Adding PostgreSQL database..."
railway add postgresql --name linkedin-recommendation-db

echo "🔄 Adding Redis cache..."
railway add redis --name linkedin-recommendation-redis

# Set environment variables
echo "⚙️ Configuring environment variables..."

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "📋 Copying env.example to .env..."
        cp env.example .env
        echo "✏️ Please edit .env file with your API keys before continuing."
        echo "Required: GITHUB_TOKEN, GEMINI_API_KEY"
        read -p "Press Enter after updating .env file..."
    else
        echo "❌ No .env or env.example file found."
        echo "Please create a .env file with required variables."
        exit 1
    fi
fi

# Set environment variables from .env file
echo "🔧 Setting Railway environment variables..."
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ $key =~ ^[[:space:]]*# ]] && continue
    [[ -z "$key" ]] && continue

    # Skip auto-configured variables
    if [[ "$key" == "DATABASE_URL" ]] || [[ "$key" == "REDIS_URL" ]]; then
        continue
    fi

    if [[ -n "$value" ]]; then
        echo "Setting $key..."
        railway variables set "$key=$value"
    fi
done < .env

# Set production-specific variables
railway variables set ENVIRONMENT=production
railway variables set API_DEBUG=false
railway variables set API_RELOAD=false

echo "🚀 Deploying to Railway..."
railway up

echo "⏳ Waiting for deployment to complete..."
sleep 30

# Get service URLs
echo "🌐 Deployment Information:"
echo "=========================="

# Get project info
PROJECT_INFO=$(railway status)
echo "$PROJECT_INFO"

echo ""
echo "📱 Next Steps:"
echo "=============="
echo "1. Visit your Railway dashboard to see the deployment"
echo "2. Copy the backend URL and update ALLOWED_ORIGINS if needed"
echo "3. Update your frontend VITE_API_BASE_URL with the backend URL"
echo "4. Test the application!"

echo ""
echo "🔗 Useful Links:"
echo "- Railway Dashboard: https://railway.app/dashboard"
echo "- API Documentation: https://your-backend-url.railway.app/docs"
echo "- Health Check: https://your-backend-url.railway.app/health"

echo ""
echo "✅ Deployment completed successfully!"
echo "🎉 Your LinkedIn Recommendation Writer is now live on Railway!"

#!/bin/bash

# 🚀 LinkedIn Recommendation Writer - Single Project Deployment
# Deploys both backend and frontend in one Railway project

echo "🚀 LinkedIn Recommendation Writer - Single Project Deployment"
echo "============================================================"
echo ""
echo "This will deploy both frontend and backend in ONE Railway project."
echo "The backend will serve the frontend static files."
echo ""

# Check prerequisites
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found."
    echo "Install: npm install -g @railway/cli"
    echo "Then: railway login"
    exit 1
fi

if ! railway whoami &> /dev/null; then
    echo "❌ Not logged into Railway."
    echo "Run: railway login"
    exit 1
fi

echo "✅ Prerequisites OK!"
echo ""

# Get API keys
echo "🔑 API Keys Configuration:"
echo "=========================="
echo "Get these from:"
echo "- GitHub: https://github.com/settings/tokens"
echo "- Gemini: https://makersuite.google.com/app/apikey"
echo ""

read -p "GitHub Personal Access Token: " GITHUB_TOKEN
read -p "Google Gemini API Key: " GEMINI_API_KEY

if [[ -z "$GITHUB_TOKEN" ]] || [[ -z "$GEMINI_API_KEY" ]]; then
    echo "❌ API keys required"
    exit 1
fi

echo ""
echo "📦 Single Project Deployment"
echo "============================"

echo ""
echo "Step 1: Create Railway Project"
echo "------------------------------"
echo "1. Go to: https://railway.app/dashboard"
echo "2. Click 'New Project'"
echo "3. Choose 'Deploy from GitHub repo'"
echo "4. Select your GitHub repository"
echo "5. Name: linkedin-recommendation-writer"
echo "6. Click 'Deploy'"
echo ""

read -p "Have you created the project? (y/n): " PROJECT_CREATED

if [[ ! "$PROJECT_CREATED" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please create the project first."
    xdg-open https://railway.app/dashboard 2>/dev/null || echo "Visit: https://railway.app/dashboard"
    exit 1
fi

echo ""
echo "Step 2: Configure Project"
echo "-------------------------"
cd "$(dirname "$0")"  # Go to project root

# Link to project
echo "Link to project:"
echo "railway link"
echo "(Select linkedin-recommendation-writer)"
echo ""
read -p "Press Enter after linking..."

# Add database
echo ""
echo "Add PostgreSQL:"
echo "railway add postgresql"
echo ""
read -p "Press Enter after adding PostgreSQL..."

# Add Redis
echo ""
echo "Add Redis:"
echo "railway add redis"
echo ""
read -p "Press Enter after adding Redis..."

# Set environment variables
echo ""
echo "Set environment variables:"
echo "railway variables set GITHUB_TOKEN=$GITHUB_TOKEN"
echo "railway variables set GEMINI_API_KEY=$GEMINI_API_KEY"
echo "railway variables set ENVIRONMENT=production"
echo "railway variables set API_DEBUG=false"
echo "railway variables set API_RELOAD=false"
echo "railway variables set LOG_LEVEL=INFO"
echo ""
read -p "Press Enter after setting variables..."

# Deploy
echo ""
echo "Step 3: Deploy"
echo "--------------"
echo "railway up"
echo ""
echo "This will:"
echo "- Install Python dependencies"
echo "- Install Node.js dependencies"
echo "- Build the frontend"
echo "- Copy frontend to backend"
echo "- Start the FastAPI server"
echo ""
read -p "Press Enter to deploy..."

railway up

# Get URL
echo ""
echo "Step 4: Get Application URL"
echo "---------------------------"
echo "railway domain"
read -p "Application URL: " APP_URL

cd - > /dev/null

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"

echo ""
echo "🌐 Application URL: $APP_URL"
echo ""
echo "📋 What you can do:"
echo "- Visit $APP_URL (serves the frontend)"
echo "- API available at $APP_URL/api/v1/"
echo "- Health check: $APP_URL/health"
echo ""

echo ""
echo "🔄 Git Integration (Optional)"
echo "============================="
echo ""
echo "For automatic redeployment on git push:"
echo "railway connect"
echo ""
read -p "Set up GitHub integration? (y/n): " GITHUB_SETUP

if [[ "$GITHUB_SETUP" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Run: railway connect"
    echo "(Connect to your GitHub repository)"
    echo ""
    read -p "Press Enter after connecting to GitHub..."
fi

echo ""
echo "✅ Success! Your LinkedIn Recommendation Writer is live on Railway!"
echo ""
echo "🎯 Single Project Benefits:"
echo "- One URL for everything"
echo "- Backend serves frontend"
echo "- Simpler management"
echo "- SPA routing works perfectly"

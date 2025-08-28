#!/bin/bash

# 🚀 LinkedIn Recommendation Writer - Simple Railway Deployment
# Step-by-step guide for deploying backend and frontend separately

echo "🚀 LinkedIn Recommendation Writer - Railway Deployment"
echo "======================================================"
echo ""
echo "This guide will walk you through deploying as separate services."
echo "Follow the steps carefully - Railway's web interface is most reliable."
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

# Backend deployment
echo "🔧 BACKEND DEPLOYMENT"
echo "===================="
echo ""
echo "Step 1: Create Backend Project"
echo "-----------------------------"
echo "1. Go to: https://railway.app/dashboard"
echo "2. Click 'New Project'"
echo "3. Choose 'Deploy from GitHub repo'"
echo "4. Select your repository"
echo "5. Click 'backend' folder"
echo "6. Name: linkedin-recommendation-backend"
echo "7. Deploy"
echo ""

read -p "Have you created backend project? (y/n): " BACKEND_DONE
if [[ ! "$BACKEND_DONE" =~ ^[Yy]$ ]]; then
    echo "Please create the backend project first."
    xdg-open https://railway.app/dashboard 2>/dev/null || echo "Visit: https://railway.app/dashboard"
    exit 1
fi

# Backend configuration
echo ""
echo "Step 2: Configure Backend"
echo "-------------------------"
cd backend

echo "Link to project:"
echo "railway link"
echo "(Select linkedin-recommendation-backend)"
echo ""
read -p "Press Enter after linking..."

echo ""
echo "Add database:"
echo "railway add postgresql"
echo ""
read -p "Press Enter after adding PostgreSQL..."

echo ""
echo "Add Redis:"
echo "railway add redis"
echo ""
read -p "Press Enter after adding Redis..."

echo ""
echo "Step 3: Set Environment Variables"
echo "----------------------------------"
echo "Get API keys from:"
echo "- GitHub: https://github.com/settings/tokens"
echo "- Gemini: https://makersuite.google.com/app/apikey"
echo ""

read -p "GitHub Token: " GITHUB_TOKEN
read -p "Gemini API Key: " GEMINI_API_KEY

if [[ -z "$GITHUB_TOKEN" ]] || [[ -z "$GEMINI_API_KEY" ]]; then
    echo "❌ API keys required"
    exit 1
fi

echo ""
echo "Set these variables:"
echo "railway variables set GITHUB_TOKEN=$GITHUB_TOKEN"
echo "railway variables set GEMINI_API_KEY=$GEMINI_API_KEY"
echo "railway variables set ENVIRONMENT=production"
echo "railway variables set API_DEBUG=false"
echo "railway variables set API_RELOAD=false"
echo "railway variables set LOG_LEVEL=INFO"
echo ""
read -p "Press Enter after setting variables..."

echo ""
echo "Step 4: Deploy Backend"
echo "----------------------"
echo "railway up"
echo ""
read -p "Press Enter after deployment..."

echo ""
echo "Step 5: Get Backend URL"
echo "-----------------------"
echo "railway domain"
read -p "Backend URL: " BACKEND_URL

cd ..
echo "✅ Backend deployed: $BACKEND_URL"

# Frontend deployment
echo ""
echo ""
echo "🎨 FRONTEND DEPLOYMENT"
echo "====================="

echo ""
echo "Step 1: Create Frontend Project"
echo "------------------------------"
echo "1. Go to: https://railway.app/dashboard"
echo "2. Click 'New Project'"
echo "3. Choose 'Deploy from GitHub repo'"
echo "4. Select your repository"
echo "5. Click 'frontend' folder"
echo "6. Name: linkedin-recommendation-frontend"
echo "7. Deploy"
echo ""

read -p "Have you created frontend project? (y/n): " FRONTEND_DONE
if [[ ! "$FRONTEND_DONE" =~ ^[Yy]$ ]]; then
    echo "Please create the frontend project."
    xdg-open https://railway.app/dashboard 2>/dev/null || echo "Visit: https://railway.app/dashboard"
    exit 1
fi

echo ""
echo "Step 2: Configure Frontend"
echo "--------------------------"
cd frontend

echo "Link to project:"
echo "railway link"
echo "(Select linkedin-recommendation-frontend)"
echo ""
read -p "Press Enter after linking..."

echo ""
echo "Set environment variables:"
echo "railway variables set VITE_API_BASE_URL=$BACKEND_URL"
echo "railway variables set VITE_API_TIMEOUT=30000"
echo "railway variables set NODE_ENV=production"
echo ""
read -p "Press Enter after setting variables..."

echo ""
echo "Step 3: Deploy Frontend"
echo "-----------------------"
echo "railway up"
echo ""
read -p "Press Enter after deployment..."

echo ""
echo "Step 4: Get Frontend URL"
echo "------------------------"
echo "railway domain"
read -p "Frontend URL: " FRONTEND_URL

cd ..

# Summary
echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"

echo ""
echo "🔧 Backend: $BACKEND_URL"
echo "🎨 Frontend: $FRONTEND_URL"
echo "📚 API Docs: $BACKEND_URL/docs"

echo ""
echo "🔗 GitHub Integration (Optional)"
echo "==============================="
echo ""
echo "For automatic redeployment on git push:"
echo ""
echo "cd backend && railway connect"
echo "cd ../frontend && railway connect"
echo ""

read -p "Set up GitHub integration? (y/n): " GITHUB_SETUP

if [[ "$GITHUB_SETUP" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Run these commands:"
    echo "cd backend && railway connect"
    echo "cd ../frontend && railway connect"
    echo ""
    read -p "Press Enter after connecting to GitHub..."
fi

echo ""
echo "✅ Success! Your app is live on Railway! 🎉"
echo ""
echo "🌐 Test: $FRONTEND_URL"

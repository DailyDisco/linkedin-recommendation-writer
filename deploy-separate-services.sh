#!/bin/bash

# 🚀 LinkedIn Recommendation Writer - Separate Services Deployment
# This script deploys backend and frontend as separate Railway services

set -e

echo "🚀 LinkedIn Recommendation Writer - Separate Services Deployment"
echo "================================================================="
echo "This will deploy backend and frontend as separate Railway services"

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

# Get API keys from user
echo ""
echo "🔑 Please provide your API keys:"
echo "(Get them from the links in DEPLOY_TO_RAILWAY.md)"
echo ""

read -p "GitHub Personal Access Token: " GITHUB_TOKEN
read -p "Google Gemini API Key: " GEMINI_API_KEY

if [[ -z "$GITHUB_TOKEN" ]] || [[ -z "$GEMINI_API_KEY" ]]; then
    echo "❌ API keys are required. Exiting..."
    exit 1
fi

echo ""
echo "🔧 Deploying Backend Service..."
echo "================================"

cd backend

# Initialize backend project
echo "📦 Creating backend Railway project..."
echo "Note: You'll need to create the project manually in Railway dashboard or CLI"
echo "1. Go to https://railway.app/dashboard"
echo "2. Click 'New Project'"
echo "3. Choose 'Deploy from GitHub repo'"
echo "4. Select your repository"
echo "5. Name it 'linkedin-recommendation-backend'"
echo ""
read -p "Have you created the backend project? (y/n): " BACKEND_READY

if [[ ! "$BACKEND_READY" =~ ^[Yy]$ ]]; then
    echo "Please create the backend project first, then run this script again."
    exit 1
fi

# Link to existing project
railway link

# Add required plugins
echo "🗄️ Adding PostgreSQL database..."
railway add postgresql --name linkedin-recommendation-db

echo "🔄 Adding Redis cache..."
railway add redis --name linkedin-recommendation-redis

# Set environment variables
echo "⚙️ Configuring backend environment variables..."
railway variables set GITHUB_TOKEN="$GITHUB_TOKEN"
railway variables set GEMINI_API_KEY="$GEMINI_API_KEY"
railway variables set ENVIRONMENT=production
railway variables set API_DEBUG=false
railway variables set API_RELOAD=false
railway variables set LOG_LEVEL=INFO

# Deploy backend
echo "🚀 Deploying backend..."
railway up

# Get backend URL
BACKEND_URL=$(railway domain)
echo "✅ Backend deployed at: $BACKEND_URL"

cd ..

echo ""
echo "🎨 Deploying Frontend Service..."
echo "================================"

cd frontend

# Initialize frontend project
echo "📦 Creating frontend Railway project..."
railway init linkedin-recommendation-frontend --yes

# Set environment variables
echo "⚙️ Configuring frontend environment variables..."
railway variables set VITE_API_BASE_URL="$BACKEND_URL"
railway variables set VITE_API_TIMEOUT=30000
railway variables set NODE_ENV=production

# Deploy frontend
echo "🚀 Deploying frontend..."
railway up

# Get frontend URL
FRONTEND_URL=$(railway domain)
echo "✅ Frontend deployed at: $FRONTEND_URL"

cd ..

echo ""
echo "🎉 Deployment Complete!"
echo "======================"

echo "🔧 Backend: $BACKEND_URL"
echo "🎨 Frontend: $FRONTEND_URL"
echo "📚 API Docs: $BACKEND_URL/docs"
echo "💚 Health Check: $BACKEND_URL/health"

echo ""
echo "🔗 Connect to GitHub for Automatic Redeployment"
echo "=============================================="
echo "To enable automatic redeployment on every git push:"
echo ""

echo "cd backend && railway connect  # Connect backend to GitHub"
echo "cd ../frontend && railway connect  # Connect frontend to GitHub"
echo ""

read -p "Would you like to connect to GitHub now? (y/n): " CONNECT_GITHUB

if [[ "$CONNECT_GITHUB" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔗 Connecting backend to GitHub..."
    cd backend && railway connect

    echo ""
    echo "🔗 Connecting frontend to GitHub..."
    cd ../frontend && railway connect

    echo ""
    echo "✅ GitHub integration complete!"
    echo "🚀 Future pushes to your main branch will automatically redeploy!"
fi

cd ..

echo ""
echo "🌐 Test your application:"
echo "1. Visit the frontend URL: $FRONTEND_URL"
echo "2. Check API documentation: $BACKEND_URL/docs"
echo "3. Monitor logs: railway logs"

echo ""
echo "📋 If you encounter CORS issues, run:"
echo "cd backend && railway variables set ALLOWED_ORIGINS=$FRONTEND_URL"

echo ""
echo "✅ Success! Your LinkedIn Recommendation Writer is live on Railway! 🎉"

if [[ "$CONNECT_GITHUB" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🎉 Git Integration Complete!"
    echo "============================"
    echo "✅ Backend connected to GitHub"
    echo "✅ Frontend connected to GitHub"
    echo "✅ Automatic redeployment enabled"
    echo ""
    echo "🚀 Your workflow:"
    echo "1. Make changes locally"
    echo "2. Push to GitHub: git push"
    echo "3. Railway automatically redeploys!"
else
    echo ""
    echo "💡 To enable automatic redeployment later:"
    echo "   cd backend && railway connect"
    echo "   cd ../frontend && railway connect"
fi

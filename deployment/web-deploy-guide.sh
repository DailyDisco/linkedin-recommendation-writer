#!/bin/bash

# 🚀 LinkedIn Recommendation Writer - Web-Based Deployment
# Complete web dashboard deployment (no CLI issues!)

echo "🚀 LinkedIn Recommendation Writer - Web Deployment"
echo "=================================================="
echo ""
echo "This guide uses Railway's web dashboard - no CLI issues!"
echo ""

# Get API keys first
echo "🔑 API Keys Setup"
echo "================="
echo ""
echo "You need these API keys:"
echo "- GitHub Token: https://github.com/settings/tokens"
echo "- Gemini API Key: https://makersuite.google.com/app/apikey"
echo ""

read -p "GitHub Personal Access Token: " GITHUB_TOKEN
read -p "Google Gemini API Key: " GEMINI_API_KEY

if [[ -z "$GITHUB_TOKEN" ]] || [[ -z "$GEMINI_API_KEY" ]]; then
    echo "❌ API keys required"
    exit 1
fi

echo ""
echo "📋 Complete Web Deployment Steps"
echo "================================"

echo ""
echo "Step 1: Create Railway Project"
echo "------------------------------"
echo "1. Open: https://railway.app/dashboard"
echo "2. Click 'New Project'"
echo "3. Choose 'Deploy from GitHub repo'"
echo "4. Select your GitHub repository"
echo "5. Name: linkedin-recommendation-writer"
echo "6. Click 'Deploy'"
echo ""

read -p "✅ Have you created the project? (y/n): " PROJECT_CREATED
if [[ ! "$PROJECT_CREATED" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please create the project first."
    xdg-open https://railway.app/dashboard 2>/dev/null || echo "Visit: https://railway.app/dashboard"
    exit 1
fi

echo ""
echo "Step 2: Add Database & Cache"
echo "----------------------------"
echo "In your Railway project dashboard:"
echo "1. Click 'Add Plugin'"
echo "2. Add 'PostgreSQL' (database)"
echo "3. Click 'Add Plugin' again"
echo "4. Add 'Redis' (cache)"
echo ""

read -p "✅ Have you added PostgreSQL and Redis? (y/n): " SERVICES_ADDED
if [[ ! "$SERVICES_ADDED" =~ ^[Yy]$ ]]; then
    echo "Please add the services first."
    exit 1
fi

echo ""
echo "Step 3: Set Environment Variables"
echo "---------------------------------"
echo "In your Railway project:"
echo "1. Go to 'Variables' tab"
echo "2. Add these variables:"
echo ""
echo "GITHUB_TOKEN = $GITHUB_TOKEN"
echo "GEMINI_API_KEY = $GEMINI_API_KEY"
echo "ENVIRONMENT = production"
echo "API_DEBUG = false"
echo "API_RELOAD = false"
echo "LOG_LEVEL = INFO"
echo ""

read -p "✅ Have you set all environment variables? (y/n): " VARS_SET
if [[ ! "$VARS_SET" =~ ^[Yy]$ ]]; then
    echo "Please set the environment variables first."
    exit 1
fi

echo ""
echo "Step 4: Deploy!"
echo "---------------"
echo "Railway will automatically:"
echo "✅ Install Python dependencies"
echo "✅ Install Node.js dependencies"
echo "✅ Build your React frontend"
echo "✅ Copy frontend to backend"
echo "✅ Start FastAPI server"
echo ""
echo "Just wait for deployment to complete!"
echo ""

read -p "✅ Has deployment completed successfully? (y/n): " DEPLOYED
if [[ ! "$DEPLOYED" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Check the deployment logs in Railway dashboard."
    echo "Look for any build errors and fix them."
    exit 1
fi

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"

echo ""
echo "🌐 Your Application URLs:"
echo "- Main App: Check your Railway project URL"
echo "- API: /api/v1/"
echo "- Health: /health"
echo "- Docs: /docs"
echo ""

echo "🔗 Optional: GitHub Integration"
echo "==============================="
echo ""
echo "For automatic redeployment:"
echo "1. In Railway project → 'Settings' tab"
echo "2. Click 'Connect to GitHub'"
echo "3. Select your repository"
echo ""
echo "Result: Every git push redeploys automatically!"
echo ""

echo "✅ Success! Your LinkedIn Recommendation Writer is live! 🎉"
echo ""
echo "🚀 Enjoy your single-project deployment!"

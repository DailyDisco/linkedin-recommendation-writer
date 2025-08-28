# 🚀 Single Project Railway Deployment

Deploy both backend and frontend in **ONE Railway project** - perfect for your needs!

## ✅ Why Single Project?

- ✅ **One project** to manage everything
- ✅ **One URL** for your entire application
- ✅ **Backend serves frontend** automatically
- ✅ **SPA routing** works perfectly
- ✅ **Simpler deployment** and maintenance

## 🎯 Quick Deployment

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### Step 2: Create Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Choose **"Deploy from GitHub repo"**
4. Select your GitHub repository
5. Name: `linkedin-recommendation-writer`
6. Click **"Deploy"**

### Step 3: Configure & Deploy

```bash
# Link to your project
railway link

# Add database and cache
railway add postgresql
railway add redis

# Set environment variables
railway variables set GITHUB_TOKEN=your_github_token_here
railway variables set GEMINI_API_KEY=your_gemini_api_key_here
railway variables set ENVIRONMENT=production

# Deploy everything together
railway up
```

## 📋 What Happens During Deployment

Railway will automatically:

1. ✅ **Install Python dependencies** (FastAPI, etc.)
2. ✅ **Install Node.js dependencies** (React, etc.)
3. ✅ **Build the frontend** (npm run build)
4. ✅ **Copy frontend to backend** (serves static files)
5. ✅ **Start FastAPI server** (serves both API + frontend)

## 🌐 Your Application URLs

After deployment, you'll have:

- **Main App**: `https://your-app.railway.app` (serves React frontend)
- **API**: `https://your-app.railway.app/api/v1/` (FastAPI backend)
- **Health**: `https://your-app.railway.app/health` (status check)
- **Docs**: `https://your-app.railway.app/docs` (API documentation)

## 🔑 Required API Keys

Get these before deploying:

### GitHub Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Create new token with `repo` and `user` scopes
3. Copy the token

### Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Copy the API key

## 🔄 Git Integration (Automatic Redeployment)

After deployment, connect to GitHub for automatic redeployment:

```bash
railway connect
```

**Result**: Every `git push` to your main branch automatically redeploys your entire application!

## 🐛 Troubleshooting

### Build Failing?

```bash
# Check build logs
railway logs --build

# Common fixes:
# - Ensure API keys are set correctly
# - Check that both requirements.txt and package.json exist
```

### Frontend Not Loading?

```bash
# Check if frontend was built and copied
railway run ls -la backend/frontend_static/
```

### CORS Issues?

```bash
# Update CORS origins (usually not needed for single project)
railway variables set ALLOWED_ORIGINS=https://your-app.railway.app
```

## 📁 Project Structure After Deployment

```
your-app.railway.app/
├── / (React frontend - index.html, static files)
├── /api/v1/ (FastAPI backend)
├── /health (health check)
└── /docs (API documentation)
```

## 🎉 Success Checklist

- [ ] Railway CLI installed and logged in
- [ ] GitHub repository connected to Railway
- [ ] PostgreSQL and Redis plugins added
- [ ] API keys configured
- [ ] Application deployed successfully
- [ ] Frontend loads at main URL
- [ ] API endpoints working
- [ ] GitHub integration set up (optional)

## 🚀 Workflow After Setup

1. **Develop locally** - make your changes
2. **Push to GitHub** - `git add . && git commit -m "changes" && git push`
3. **Automatic deployment** - Railway redeploys your entire app
4. **Test** - visit your Railway URL to see changes live

**Your LinkedIn Recommendation Writer is now live in ONE Railway project! 🎉**

# 🚀 Deploy LinkedIn Recommendation Writer on Railway

Complete guide to deploy your full-stack application on Railway with PostgreSQL and Redis.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Deployment](#quick-deployment)
- [Step-by-Step Setup](#step-by-step-setup)
- [Database Configuration](#database-configuration)
- [Environment Variables](#environment-variables)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Cost Optimization](#cost-optimization)

## 🎯 Prerequisites

Before deploying, ensure you have:

1. **Railway Account**: [Sign up at railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **API Keys**:
   - [GitHub Personal Access Token](https://github.com/settings/tokens) (with `repo` and `user` scopes)
   - [Google Gemini API Key](https://makersuite.google.com/app/apikey)
4. **Railway CLI** (optional): `npm install -g @railway/cli`

## ⚡ Quick Deployment (5 minutes)

### 🎯 Recommended: Separate Services (Best Practice)

Deploy backend and frontend as separate Railway services for better performance and easier management:

#### Backend Deployment:

```bash
# 1. Deploy backend service
cd backend
railway login
railway init linkedin-recommendation-backend
railway add postgresql
railway add redis
railway variables set GITHUB_TOKEN=your_github_token
railway variables set GEMINI_API_KEY=your_gemini_api_key
railway variables set ENVIRONMENT=production
railway up
```

#### Frontend Deployment:

```bash
# 2. Deploy frontend service
cd ../frontend
railway init linkedin-recommendation-frontend
railway variables set VITE_API_BASE_URL=https://your-backend-url.railway.app
railway up
```

### Option 2: Monorepo Deployment (Alternative)

If you prefer deploying everything together:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/YOUR_USERNAME/YOUR_REPO&envs=GITHUB_TOKEN,GEMINI_API_KEY&plugins=postgresql,redis)

**Note**: Monorepo deployment may have pip installation issues. Separate services are recommended.

## 📝 Step-by-Step Setup

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Choose **"Deploy from GitHub repo"**
4. Select your repository
5. Click **"Deploy"**

### Step 2: Add Database Services

Railway will auto-detect your project needs, but you can manually add:

1. Go to your project dashboard
2. Click **"Add Plugin"**
3. Add **PostgreSQL** database
4. Add **Redis** cache

### Step 3: Configure Environment Variables

In your Railway project:

1. Go to **"Variables"** tab
2. Add these required variables:

```bash
# Required API Keys
GITHUB_TOKEN=your_github_personal_access_token
GEMINI_API_KEY=your_google_gemini_api_key

# Application Settings
ENVIRONMENT=production
API_DEBUG=false
API_RELOAD=false
LOG_LEVEL=INFO

# Database (auto-configured by Railway)
# DATABASE_URL=postgresql://... (Railway provides this)

# Redis (auto-configured by Railway)
# REDIS_URL=redis://... (Railway provides this)
```

### Step 4: Deploy Services

Railway will automatically:

1. **Detect** your Python backend and Node.js frontend
2. **Build** using Nixpacks (Docker alternative)
3. **Deploy** both services
4. **Connect** to PostgreSQL and Redis

### Step 5: Configure CORS (Important!)

After deployment, update your backend environment variables:

```bash
# Set this to your Railway frontend URL
ALLOWED_ORIGINS=https://your-frontend-service.railway.app
```

## 🗄️ Database Configuration

### Automatic Setup

Railway automatically:

- Creates PostgreSQL database
- Sets `DATABASE_URL` environment variable
- Runs database migrations on startup
- Provides connection pooling

### Manual Migration (if needed)

If you need to run migrations manually:

```bash
# Connect to Railway service
railway connect

# Run migrations
cd backend
alembic upgrade head
```

## 🌍 Environment Variables Reference

### Required Variables

| Variable         | Description       | Example                           |
| ---------------- | ----------------- | --------------------------------- |
| `GITHUB_TOKEN`   | GitHub API access | `ghp_xxxxxxxxxxxxxxxxxxxx`        |
| `GEMINI_API_KEY` | Google AI API key | `AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxx` |

### Optional Variables

| Variable             | Default      | Description          |
| -------------------- | ------------ | -------------------- |
| `ENVIRONMENT`        | `production` | App environment      |
| `LOG_LEVEL`          | `INFO`       | Logging level        |
| `API_WORKERS`        | `4`          | Number of workers    |
| `DATABASE_POOL_SIZE` | `10`         | DB connection pool   |
| `REDIS_DEFAULT_TTL`  | `3600`       | Cache TTL in seconds |

### Auto-Configured Variables

Railway automatically sets:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `PORT` - Service port (automatically assigned)

## 🔍 Monitoring & Troubleshooting

### Check Service Health

```bash
# Check deployment status
railway status

# View service logs
railway logs

# Monitor specific service
railway logs --service backend
```

### Common Issues & Solutions

#### 1. Build Failures

```bash
# Check build logs
railway logs --build
```

**Common fixes:**

- Ensure `requirements.txt` and `package.json` are in correct directories
- Check that all dependencies are properly specified
- Verify Python/Node.js versions are supported

#### 2. Database Connection Issues

```bash
# Check database connectivity
railway run python -c "import os; print(os.environ.get('DATABASE_URL'))"
```

**Solutions:**

- Verify PostgreSQL plugin is added
- Check database credentials
- Ensure migration scripts are present

#### 3. API Key Issues

```bash
# Validate API keys
railway run python -c "
import os
from backend.app.core.config import settings
print('GitHub Token:', bool(settings.GITHUB_TOKEN))
print('Gemini Key:', bool(settings.GEMINI_API_KEY))
"
```

#### 4. Pip Installation Issues (Monorepo Deployment)

If you encounter `pip: command not found` errors during monorepo deployment:

**Solutions:**

1. **Switch to Separate Services** (Recommended):

   ```bash
   # Deploy backend and frontend as separate services
   ./deploy-to-railway.sh
   ```

2. **Fix Nixpacks Configuration**:

   - Ensure Python is properly installed: `python311` in nixPkgs
   - Use `python3 -m pip` instead of `pip`
   - Add `--user` flag: `python3 -m pip install --user -r requirements.txt`

3. **Manual Fix**:
   ```bash
   # Delete the problematic nixpacks.toml and deploy as separate services
   rm nixpacks.toml
   cd backend && railway init backend-project
   cd ../frontend && railway init frontend-project
   ```

#### 5. CORS Issues

Update `ALLOWED_ORIGINS` with your frontend URL:

```bash
railway variables set ALLOWED_ORIGINS=https://your-frontend.railway.app
```

### Health Check Endpoints

- **Backend Health**: `https://your-backend.railway.app/health`
- **API Docs**: `https://your-backend.railway.app/docs`
- **Frontend**: `https://your-frontend.railway.app`

## 💰 Cost Optimization

### Free Tier Limits

Railway Hobby plan includes:

- 512MB RAM per service
- 1GB PostgreSQL storage
- 100GB bandwidth/month
- Basic Redis (30MB)

### Upgrade Considerations

For production workloads:

1. **Pro Plan** ($10/month):

   - 8GB RAM
   - 100GB PostgreSQL
   - 500GB bandwidth
   - Better Redis (1GB)

2. **Database Optimization**:
   - Use connection pooling
   - Implement proper indexing
   - Monitor query performance

### Cost-Saving Tips

```bash
# Scale down when not in use
railway scale --service backend --replicas 0

# Monitor usage
railway usage
```

## 🚀 Advanced Configuration

### Custom Domain

1. Go to **"Settings"** → **"Domains"**
2. Add your custom domain
3. Update DNS records as instructed
4. Update `ALLOWED_ORIGINS` with your domain

### Environment-Specific Deployments

Create separate projects for staging/production:

```bash
# Staging
railway --project staging deploy

# Production
railway --project production deploy
```

### Backup Strategy

Railway automatically backs up PostgreSQL databases. For manual backups:

```bash
# Create database dump
railway run pg_dump $DATABASE_URL > backup.sql

# Restore from backup
railway run psql $DATABASE_URL < backup.sql
```

## 📞 Support & Resources

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **React Router Docs**: [reactrouter.com](https://reactrouter.com)
- **Railway Community**: [discord.gg/railway](https://discord.gg/railway)

## 🔧 Troubleshooting Commands

```bash
# Check all environment variables
railway run env | grep -E "(DATABASE|REDIS|GITHUB|GEMINI)"

# Test database connection
railway run python -c "
import asyncpg
import os
async def test():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    result = await conn.fetchval('SELECT version()')
    print('PostgreSQL version:', result)
import asyncio
asyncio.run(test())
"

# Test Redis connection
railway run python -c "
import redis
import os
r = redis.from_url(os.environ['REDIS_URL'])
r.set('test', 'hello')
print('Redis test:', r.get('test'))
"

# Check API endpoints
curl https://your-backend.railway.app/health
curl https://your-backend.railway.app/docs
```

---

## 🎉 Success Checklist

- [ ] Railway project created
- [ ] PostgreSQL plugin added
- [ ] Redis plugin added
- [ ] Environment variables configured
- [ ] Services deployed successfully
- [ ] Frontend accessible
- [ ] Backend API responding
- [ ] Database migrations completed
- [ ] CORS configured
- [ ] Health checks passing

**Your app is now live on Railway! 🚀**

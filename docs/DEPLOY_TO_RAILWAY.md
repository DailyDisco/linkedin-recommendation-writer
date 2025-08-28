# 🚀 Deploy to Railway - Simple Guide

## ✅ Single Project Deployment (Your Preference!)

Perfect! We'll deploy both backend and frontend in **ONE Railway project**. The backend will serve the frontend static files - exactly what you want!

**Benefits:**

- ✅ One project to manage
- ✅ One URL for everything
- ✅ Backend serves frontend automatically
- ✅ SPA routing works perfectly
- ✅ Simpler deployment process

---

## 🎯 Quick Deployment (3 Steps)

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### Step 2: Deploy Backend

```bash
cd backend
railway init linkedin-recommendation-backend
railway add postgresql
railway add redis

# Set environment variables
railway variables set GITHUB_TOKEN=your_github_token_here
railway variables set GEMINI_API_KEY=your_gemini_api_key_here
railway variables set ENVIRONMENT=production

# Deploy
railway up
```

### Step 3: Deploy Frontend

```bash
cd ../frontend
railway init linkedin-recommendation-frontend

# Get backend URL from Step 2
railway variables set VITE_API_BASE_URL=https://your-backend-url.railway.app
railway variables set NODE_ENV=production

# Deploy
railway up
```

---

## 📋 Detailed Instructions

### Backend Deployment

1. **Navigate to backend directory:**

   ```bash
   cd backend
   ```

2. **Initialize Railway project:**

   ```bash
   railway init linkedin-recommendation-backend
   ```

3. **Add required services:**

   ```bash
   railway add postgresql  # Database
   railway add redis       # Cache
   ```

4. **Set environment variables:**

   ```bash
   # Required API keys
   railway variables set GITHUB_TOKEN=your_github_token_here
   railway variables set GEMINI_API_KEY=your_gemini_api_key_here

   # Production settings
   railway variables set ENVIRONMENT=production
   railway variables set API_DEBUG=false
   railway variables set API_RELOAD=false
   railway variables set LOG_LEVEL=INFO
   ```

5. **Deploy:**

   ```bash
   railway up
   ```

6. **Get backend URL:**
   ```bash
   railway domain
   ```
   Copy this URL for the frontend configuration.

### Frontend Deployment

1. **Navigate to frontend directory:**

   ```bash
   cd ../frontend
   ```

2. **Initialize Railway project:**

   ```bash
   railway init linkedin-recommendation-frontend
   ```

3. **Set environment variables:**

   ```bash
   # Connect to backend (use URL from Step 6 above)
   railway variables set VITE_API_BASE_URL=https://your-backend-url.railway.app
   railway variables set VITE_API_TIMEOUT=30000
   railway variables set NODE_ENV=production
   ```

4. **Deploy:**
   ```bash
   railway up
   ```

---

## 🔑 Getting Your API Keys

### GitHub Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `user`
4. Copy the token

### Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API key"
3. Copy the API key

---

## 🌐 Access Your Application

After deployment:

- **Frontend**: Visit your frontend Railway URL
- **Backend API**: Visit `https://your-backend-url.railway.app/docs`
- **Health Check**: `https://your-backend-url.railway.app/health`

---

## 🔄 Git Integration & Redeployment

### Do You Need to Redeploy After Every Git Push?

**YES, but you can automate it!** Here are your options:

#### Option A: Automatic Redeployment (Recommended)

1. **Connect each Railway project to your GitHub repo:**

   ```bash
   # After deployment, connect to GitHub
   cd backend && railway connect
   cd ../frontend && railway connect
   ```

2. **Railway will automatically redeploy** when you push to your main/master branch

#### Option B: Manual Redeployment

```bash
# After pushing to GitHub, redeploy each service
cd backend && railway up
cd ../frontend && railway up
```

#### Option C: Use Railway CLI for Development

```bash
# For rapid development/testing
cd backend && railway dev  # Hot reload for backend
cd ../frontend && railway dev  # Hot reload for frontend
```

### Best Practice Workflow

1. **Development**: Make changes locally
2. **Push to GitHub**: `git add . && git commit -m "your changes" && git push`
3. **Automatic Deployment**: Railway detects the push and redeploys automatically
4. **Monitor**: Check Railway dashboard or logs if needed

### Connecting to GitHub

After running the deployment script:

```bash
# Connect backend project to GitHub
cd backend
railway connect  # Select your GitHub repository

# Connect frontend project to GitHub
cd ../frontend
railway connect  # Select your GitHub repository
```

**Once connected, every push to your main branch will trigger automatic redeployment!**

---

## 🐛 Troubleshooting

### Build Still Failing?

If you still get errors, try redeploying individual services:

```bash
# For backend
cd backend
railway up

# For frontend
cd ../frontend
railway up
```

### Check Logs

```bash
# Backend logs
cd backend && railway logs

# Frontend logs
cd ../frontend && railway logs
```

### CORS Issues?

Update backend CORS settings:

```bash
cd backend
railway variables set ALLOWED_ORIGINS=https://your-frontend-url.railway.app
```

---

## 💡 Why Separate Services?

- ✅ **No dependency conflicts** (Python + Node.js)
- ✅ **Independent scaling**
- ✅ **Easier debugging**
- ✅ **Better performance**
- ✅ **Railway best practice**

---

## 🎉 Success Checklist

- [ ] Railway CLI installed and logged in
- [ ] Backend deployed successfully
- [ ] Frontend deployed successfully
- [ ] API keys configured
- [ ] Frontend connects to backend
- [ ] Application loads in browser

**Your LinkedIn Recommendation Writer is now live on Railway! 🎉**

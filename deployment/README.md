# 🚀 Deployment Scripts

This folder contains scripts to deploy your LinkedIn Recommendation Writer to Railway.

## 📋 Available Scripts

### `docker-deploy.sh`

**Recommended approach** - Uses Railway's Docker detection for reliable single-project deployment.

```bash
./docker-deploy.sh
```

**Features:**

- ✅ Web-based deployment (no CLI issues)
- ✅ Single project with both frontend + backend
- ✅ Automatic frontend serving from backend
- ✅ PostgreSQL + Redis included
- ✅ Custom Docker build (most reliable)

### `web-deploy-guide.sh`

Alternative interactive guide for manual web-based deployment.

```bash
./web-deploy-guide.sh
```

## 🎯 Quick Start

1. **Make scripts executable:**

   ```bash
   chmod +x docker-deploy.sh web-deploy-guide.sh
   ```

2. **Run deployment:**

   ```bash
   ./docker-deploy.sh
   ```

3. **Follow the prompts** - the script guides you through Railway dashboard steps.

## 📁 What Gets Created

- **One Railway project** with both services
- **PostgreSQL database** (automatic)
- **Redis cache** (automatic)
- **Single URL** serving both frontend and API

## 🔄 Redeployment

After initial setup, every `git push` automatically redeploys your app!

## 🆘 Troubleshooting

- **Build fails?** Check Railway logs for errors
- **Frontend not loading?** Verify environment variables are set
- **API not working?** Check database connection in Railway

---

**Need help?** Check the main `docs/` folder for detailed guides!

# Bentley Budget Bot - Docker & Vercel Deployment Guide

## 🐳 Docker Container

Your application has been successfully containerized! Here's what was created:

### Files Created:
- `Dockerfile` - Multi-stage Docker build configuration
- `.dockerignore` - Excludes unnecessary files from Docker build
- `docker-compose.yml` - Easy development setup
- `vercel.json` - Vercel deployment configuration
- `start.sh` - Vercel startup script
- `api/index.py` - Vercel serverless entry point

### 🚀 Quick Start Commands:

#### Local Docker Development:
```bash
# Build the container
docker build -t bentley-budget-bot .

# Run locally
docker run -p 8501:8501 bentley-budget-bot

# Or use docker-compose
docker-compose up
```

#### View your app at: http://localhost:8501

## ☁️ Vercel Deployment Options

### Option 1: Direct Vercel Deployment (Recommended)
1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Deploy:**
   ```bash
   cd C:\Users\winst\BentleyBudgetBot
   vercel --prod
   ```

### Option 2: GitHub Integration
1. Push your code to GitHub
2. Connect your GitHub repo to Vercel
3. Automatic deployments on every push

### Option 3: Docker Container on Vercel
1. **Tag and push to Docker Hub:**
   ```bash
   docker tag bentley-budget-bot:latest yourdockerhub/bentley-budget-bot:latest
   docker push yourdockerhub/bentley-budget-bot:latest
   ```

2. **Deploy on Vercel with Docker:**
   ```bash
   vercel --docker
   ```

## 🔧 Environment Variables for Production

Set these in Vercel dashboard or .env file:
```bash
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

## 📊 Features Included in Container:
✅ Yahoo Finance Portfolio Integration
✅ Real-time stock data fetching
✅ Interactive charts and metrics
✅ Responsive design with custom colors
✅ Error handling and graceful fallbacks
✅ Production-ready configuration

## 🛠️ Troubleshooting

If you encounter issues:
1. **Check Docker Desktop is running**
2. **Verify all dependencies in requirements.txt**
3. **Test locally first with: `streamlit run streamlit_app.py`**
4. **Check Vercel logs for serverless function errors**

## 🌐 Production URLs

After deployment, your app will be available at:
- **Vercel**: `https://your-app-name.vercel.app`
- **Local Docker**: `http://localhost:8501`

---

**Container Status: ✅ READY FOR DEPLOYMENT**
# Stylo.AI Backend Deployment Guide

## Deploying to Render

### Prerequisites
1. A Render account (free tier available)
2. Your API keys for Gemini and SerpAPI
3. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)

### Step 1: Prepare Your Repository

The following files have been created/updated for Render deployment:

- `Procfile` - Tells Render how to start your app
- `backend/runtime.txt` - Specifies Python version
- `backend/requirements.txt` - Updated with all dependencies
- `backend/config.py` - Updated to use environment variables
- `backend/.env.example` - Template for environment variables
- `render.yaml` - Advanced deployment configuration (optional)

### Step 2: Deploy to Render

1. **Connect Repository:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your Git repository

2. **Configure Service:**
   - **Name:** `stylo-ai-backend` (or your preferred name)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && python api.py`

3. **Set Environment Variables:**
   - Go to the "Environment" tab
   - Add these variables:
     - `GEMINI_API_KEY`: Your Gemini API key
     - `SERPAPI_KEY`: Your SerpAPI key
     - `PORT`: Will be set automatically by Render

4. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy your app

### Step 3: Verify Deployment

Once deployed, you can access:
- **API Root:** `https://your-app-name.onrender.com/`
- **API Docs:** `https://your-app-name.onrender.com/docs`
- **Health Check:** `https://your-app-name.onrender.com/health`

### Important Notes

1. **Free Tier Limitations:**
   - Apps sleep after 15 minutes of inactivity
   - Cold start takes ~30 seconds
   - 750 hours/month limit

2. **File Storage:**
   - Generated images are stored in `backend/clothing_images/`
   - Files persist between deployments
   - Consider using cloud storage for production

3. **Environment Variables:**
   - Never commit API keys to your repository
   - Use Render's environment variable settings
   - The app will use your local keys as fallback for development

### Troubleshooting

**Build Fails:**
- Check that all dependencies are in `requirements.txt`
- Verify Python version in `runtime.txt`

**App Won't Start:**
- Check the logs in Render dashboard
- Verify environment variables are set
- Ensure port configuration is correct

**API Errors:**
- Check that API keys are valid
- Verify all required files are present
- Check the health endpoint first

### Local Testing

To test the production configuration locally:

```bash
# Set environment variables
export GEMINI_API_KEY="your_key_here"
export SERPAPI_KEY="your_key_here"
export PORT=8000

# Run the app
cd backend
python api.py
```

### Next Steps

1. Set up a custom domain (optional)
2. Configure monitoring and alerts
3. Set up automated deployments from main branch
4. Consider upgrading to paid plan for better performance

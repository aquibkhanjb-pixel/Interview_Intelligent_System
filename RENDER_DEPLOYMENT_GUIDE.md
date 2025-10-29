# Render Deployment Guide - Interview Intelligence System

## Quick Setup

### Step 1: Create PostgreSQL Database on Render

1. Go to Render Dashboard: https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `interview-intelligence-db`
   - **Database**: `interview_intel`
   - **User**: (auto-generated)
   - **Region**: Oregon (or nearest to you)
   - **Plan**: Free
4. Click **"Create Database"**
5. Wait for database to be created (takes ~2 minutes)
6. **IMPORTANT**: Copy the **Internal Database URL** (starts with `postgres://`)

### Step 2: Create Web Service on Render

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure the service:

#### Basic Settings
- **Name**: `interview-intelligence-system`
- **Region**: Oregon (same as database)
- **Branch**: `main`
- **Root Directory**: `interview_intelligence_system`
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

#### Environment Variables
Click **"Advanced"** → **"Add Environment Variable"** and add these:

**Required:**
```
FLASK_ENV=production
SECRET_KEY=your-random-secret-key-here-change-this
DATABASE_URL=(paste the Internal Database URL from Step 1)
```

**Optional (with defaults):**
```
USER_AGENT=Interview Intelligence Research Bot 1.0
REQUEST_DELAY=2
MAX_RETRIES=3
API_RATE_LIMIT=100
```

**To generate a secure SECRET_KEY**, run this in Python:
```python
import secrets
print(secrets.token_hex(32))
```

### Step 3: Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Start the application
3. Wait for deployment (takes ~3-5 minutes)
4. Check logs for any errors

### Step 4: Verify Deployment

Once deployed, your app will be available at:
```
https://interview-intelligence-system.onrender.com
```

Test these endpoints:
- `GET /` - Root endpoint (should return API info)
- `GET /api/health` - Health check
- `GET /api/docs` - API documentation
- `GET /api/companies/` - List of companies

## Troubleshooting Common Issues

### Issue 1: Database Connection Error
**Symptom**: `connection refused` or `can't connect to localhost`

**Solution**:
1. Verify `DATABASE_URL` environment variable is set correctly
2. Make sure you used the **Internal Database URL** (not External)
3. Check database is in the same region as web service
4. The app automatically converts `postgres://` to `postgresql+psycopg://`

### Issue 2: Module Not Found
**Symptom**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
1. Verify **Root Directory** is set to `interview_intelligence_system`
2. Check **Start Command** is `gunicorn app:app`
3. Ensure `app.py` exists in the root directory of your repository

### Issue 3: Build Fails
**Symptom**: pip install errors

**Solution**:
1. Check `requirements.txt` is in the `interview_intelligence_system` folder
2. Verify Python version (runtime.txt should specify `python-3.12.8`)
3. Check build logs for specific package errors

### Issue 4: App Crashes on Startup
**Symptom**: App starts but immediately exits with status 1

**Solution**:
1. Check logs in Render dashboard
2. Verify all required environment variables are set
3. Make sure `SECRET_KEY` is set (not the default)
4. Database URL should not contain localhost

## Configuration Files

Your repository should have these files in `interview_intelligence_system/`:

1. **app.py** - Entry point for Gunicorn
2. **requirements.txt** - Python dependencies
3. **runtime.txt** - Specifies Python 3.12.8
4. **render.yaml** (optional) - Infrastructure as code
5. **.env.example** - Example environment variables

## Post-Deployment

### Monitoring
- View logs: Render Dashboard → Your Service → Logs
- Check metrics: Dashboard shows CPU, Memory, Request count

### Updating the App
1. Push changes to GitHub
2. Render auto-deploys from your `main` branch
3. Manual deploy: Dashboard → Your Service → Manual Deploy → Deploy latest commit

### Scaling (Paid Plans)
- Free plan: Spins down after 15 min inactivity (cold starts ~30s)
- Upgrade to Starter plan ($7/month) for always-on service

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string from Render |
| `FLASK_ENV` | Yes | development | Set to `production` |
| `SECRET_KEY` | Yes | - | Random secret key for Flask sessions |
| `USER_AGENT` | No | Research Bot 1.0 | User agent for web scraping |
| `REQUEST_DELAY` | No | 2 | Delay between scraping requests (seconds) |
| `MAX_RETRIES` | No | 3 | Max retries for failed requests |
| `API_RATE_LIMIT` | No | 100 | API rate limit per hour |

## Need Help?

If you're still having issues:
1. Check Render logs for specific error messages
2. Verify all environment variables are set correctly
3. Ensure database is created and accessible
4. Check that root directory is set to `interview_intelligence_system`

## Success Checklist

- [ ] PostgreSQL database created on Render
- [ ] Internal Database URL copied
- [ ] Web service created and connected to GitHub
- [ ] Root directory set to `interview_intelligence_system`
- [ ] All required environment variables set
- [ ] SECRET_KEY generated and set (not default)
- [ ] Build completed successfully
- [ ] Service is running (not crashed)
- [ ] Root endpoint (/) returns JSON response
- [ ] Health check (/api/health) shows "healthy"

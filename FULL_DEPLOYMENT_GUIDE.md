# Complete Deployment Guide - Interview Intelligence System

## 🎯 Understanding Your Project Architecture

Your project has **TWO SEPARATE COMPONENTS**:

### 1. Backend (Flask API)
- **Location**: `interview_intelligence_system/` (root)
- **Technology**: Python Flask
- **Port**: 5000
- **Purpose**: Provides JSON API endpoints for data
- **Currently Deployed**: ✅ YES on Render at https://interview-intelligent-system-1.onrender.com

### 2. Frontend (React UI)
- **Location**: `interview_intelligence_system/frontend/`
- **Technology**: React + Vite + Material-UI
- **Port**: 5173 (development)
- **Purpose**: Visual user interface with charts, buttons, forms
- **Currently Deployed**: ❌ NO - This is why you only see JSON!

## 🚀 Running Locally (BOTH Components)

I've already started both services for you:

### Backend Running ✅
- **URL**: http://localhost:5000
- **Status**: Running
- **What you see**: JSON data
- **Command**: `python main.py --mode=web`

### Frontend Running ✅
- **URL**: http://localhost:5173
- **Status**: Running
- **What you see**: Beautiful UI with charts and dashboards
- **Command**: `npm run dev`

## 🌐 Open Your Browser NOW

**Visit**: http://localhost:5173

You should see:
- Company dashboard with charts
- List of companies (Amazon, Google, Microsoft, etc.)
- Interview insights and analysis
- Visual interface with Material-UI design

## 📊 What Each Component Does

### Backend Endpoints (http://localhost:5000)
- `GET /` - API info (JSON)
- `GET /api/companies/` - List all companies (JSON)
- `GET /api/insights/<company>` - Company insights (JSON)
- `GET /api/analysis/<company>` - Analysis data (JSON)
- `POST /api/compare/` - Compare companies (JSON)

### Frontend Pages (http://localhost:5173)
- `/` - Dashboard with company list
- `/comparison` - Company comparison tool
- Interactive charts and visualizations

## 🔧 How to Run Manually (For Future Reference)

### Start Backend
```bash
cd interview_intelligence_system
python main.py --mode=web
```

### Start Frontend (in a new terminal)
```bash
cd interview_intelligence_system/frontend
npm install  # First time only
npm run dev
```

## ☁️ Deploying to Production

### Current Status
- ✅ Backend deployed on Render (but DATABASE_URL not set)
- ❌ Frontend not deployed

### Option 1: Deploy Frontend on Vercel (Recommended)

1. **Build the frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy to Vercel**:
   - Go to https://vercel.com
   - Import your GitHub repository
   - Set root directory to `interview_intelligence_system/frontend`
   - Add environment variable:
     - `VITE_API_URL` = `https://interview-intelligent-system-1.onrender.com`
   - Deploy

3. **Result**: Frontend at `https://your-app.vercel.app` → calls backend on Render

### Option 2: Deploy Frontend on Netlify

1. **Build the frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy to Netlify**:
   - Go to https://netlify.com
   - Drag & drop the `dist/` folder
   - Or connect GitHub and set build command: `npm run build`
   - Set environment variable:
     - `VITE_API_URL` = `https://interview-intelligent-system-1.onrender.com`

### Option 3: Serve Frontend from Flask (Single Deployment)

This would require modifying the Flask app to serve the built React app.

**Steps**:
1. Build frontend: `npm run build`
2. Modify Flask app to serve `dist/` folder as static files
3. Deploy everything together on Render

## ⚠️ Fix Backend on Render FIRST

Before deploying the frontend, fix the database connection on Render:

1. Go to Render Dashboard
2. Select your Web Service
3. Go to **Environment** tab
4. Add these variables:
   - `DATABASE_URL` = (Internal Database URL from PostgreSQL service)
   - `FLASK_ENV` = `production`
   - `SECRET_KEY` = (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
5. Save and redeploy

## 📁 Project Structure

```
interview_intelligence_system/
├── api/                    # Flask API routes
├── database/              # Database models & connection
├── config/                # Configuration files
├── frontend/              # React UI (SEPARATE APP)
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API calls
│   │   └── App.jsx       # Main app
│   ├── package.json
│   └── vite.config.js
├── main.py               # Flask entry point
├── app.py                # Gunicorn entry point
├── requirements.txt       # Python dependencies
└── render.yaml           # Render configuration (backend only)
```

## 🎨 Frontend Features

Your frontend includes:
- Material-UI design system
- React Router for navigation
- Axios for API calls
- Chart.js for visualizations
- Company dashboard
- Comparison tools
- Insights display

## 🔍 Troubleshooting

### "I only see JSON on Render"
- **Reason**: You only deployed the backend
- **Solution**: Deploy the frontend separately (Vercel/Netlify)

### "Frontend can't connect to backend"
- **Reason**: CORS or wrong API URL
- **Solution**: Check `VITE_API_URL` environment variable

### "Database connection failed on Render"
- **Reason**: DATABASE_URL not set
- **Solution**: Follow the "Fix Backend on Render FIRST" section above

## 📝 Summary

1. **Local Development** ✅ (Both running now)
   - Backend: http://localhost:5000
   - Frontend: http://localhost:5173

2. **Production Backend** ⚠️ (Deployed but needs DATABASE_URL)
   - URL: https://interview-intelligent-system-1.onrender.com
   - **Action needed**: Set DATABASE_URL environment variable

3. **Production Frontend** ❌ (Not deployed)
   - **Action needed**: Deploy to Vercel or Netlify
   - **Set**: VITE_API_URL to point to Render backend

## 🎉 Next Steps

1. ✅ **Check the UI**: Open http://localhost:5173 in your browser RIGHT NOW
2. ⚠️ **Fix Render backend**: Set DATABASE_URL environment variable
3. 📦 **Deploy frontend**: Choose Vercel or Netlify
4. 🔗 **Connect them**: Set VITE_API_URL in frontend to Render backend URL

Once both are deployed and connected, you'll have a fully functional web application!

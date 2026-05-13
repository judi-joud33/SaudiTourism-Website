# Railway Deployment Guide

This Flask app is now configured for Railway deployment. Here's what was changed:

## Changes Made

### 1. Deleted Vercel Configuration
- ❌ Removed: `vercel.json`

### 2. Railway Configuration Files
- ✅ `Procfile`: Contains `web: gunicorn app:app` for Railway to start the app
- ✅ `requirements.txt`: Already includes `gunicorn==23.0.0`

### 3. App Configuration Updates (`app.py`)

#### Database Path Priority
The app now uses this priority order for the database:

1. **DATABASE_URL** (if Railway provides PostgreSQL)
   - Use: `os.getenv("DATABASE_URL")`
   - Railway will automatically set this if you connect a PostgreSQL plugin

2. **RAILWAY_VOLUME_MOUNT_PATH** (if using Volumes on Railway)
   - Use: `os.path.join(volume_path, 'site.db')`
   - Stores SQLite in persistent storage

3. **Local SQLite** (fallback - good for development)
   - Use: `site.db` in the project directory
   - Works on Railway ephemeral filesystem (survives for current deployment)

#### Production Settings
- `host='0.0.0.0'` — Listens on all interfaces (required for Railway)
- `PORT` from environment (Railway sets this automatically, default 5000)
- Debug mode depends on `FLASK_ENV` environment variable

## Deployment Steps on Railway

### Step 1: Connect Your Repository
1. Go to [Railway.app](https://railway.app)
2. Create a new project
3. Connect your GitHub repository
4. Select the repository branch

### Step 2: Set Environment Variables
In Railway dashboard → Variables:

```
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

### Step 3: Auto-Deploy
Railway will:
1. Read `Procfile`
2. Install dependencies from `requirements.txt`
3. Run: `gunicorn app:app`
4. Automatically create tables via `db.create_all()` on startup

### Step 4 (Optional): Add PostgreSQL
For production, add PostgreSQL:
1. Add a PostgreSQL plugin in Railway
2. Railway automatically sets `DATABASE_URL`
3. App will use PostgreSQL instead of SQLite

## Database Behavior

### SQLite (Current Setup)
- Persists between deployments if using Volumes
- No additional setup needed
- Good for small apps

### PostgreSQL (Recommended for Production)
1. Add PostgreSQL plugin in Railway
2. No code changes needed
3. App detects `DATABASE_URL` automatically

## Database Initialization

The app automatically:
1. Creates all tables on startup: `db.create_all()`
2. Runs seed data if needed (using `seed_db.py` locally before deploying)

### Pre-Populate Database Before Deploying
Run locally before your first Railway deployment:

```bash
python seed_db.py
```

This ensures sample data exists in your SQLite database.

## Troubleshooting

### "Database Not Found" Error
- Check Railway logs: `railway logs`
- Verify environment variables are set
- If using PostgreSQL, ensure the plugin is connected

### Port Binding Issues
- Railway automatically assigns a PORT via environment variable
- The app reads it: `port = int(os.getenv('PORT', 5000))`

### Volume Not Persisting
- SQLite files on Railway's ephemeral filesystem don't persist between redeploys
- **Solution**: Use PostgreSQL (add a plugin) for persistent data
- OR: Set up Volumes in Railway (see Railway docs)

## Cost Optimization

- **SQLite + Ephemeral Storage**: Free tier works fine
- **PostgreSQL**: ~$15/month (comes with usage limits)
- **Volumes**: Adds storage cost on paid plans

For this Saudi Tourism app, PostgreSQL is recommended to avoid data loss on redeploy.

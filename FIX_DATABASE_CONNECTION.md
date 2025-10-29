# Fix Database Connection - URGENT

Your app is live but can't connect to the database because **DATABASE_URL is not set**.

## 🚨 The Problem

The app is trying to connect to `localhost:5432` instead of your Render PostgreSQL database.
This means the `DATABASE_URL` environment variable is **NOT SET** in Render.

## ✅ Solution - Follow These Steps EXACTLY

### Step 1: Get Your PostgreSQL Connection String

1. Go to Render Dashboard: https://dashboard.render.com
2. Click on your **PostgreSQL database** (should be named something like `interview-intelligence-db`)
3. Look for **"Internal Database URL"** or **"Connections"** section
4. Copy the **Internal Database URL** - it looks like:
   ```
   postgres://username:password@dpg-xxxxx.oregon-postgres.render.com/dbname
   ```
5. **IMPORTANT**: Use the **Internal Database URL**, NOT the External one!

### Step 2: Add DATABASE_URL to Your Web Service

1. In Render Dashboard, go to your **Web Service** (interview-intelligent-system-1)
2. Click **"Environment"** in the left sidebar
3. Click **"Add Environment Variable"**
4. Add:
   - **Key**: `DATABASE_URL`
   - **Value**: (paste the Internal Database URL you copied)
5. Click **"Save Changes"**

### Step 3: Add Other Required Variables

While you're there, add these too:

**FLASK_ENV**
- Key: `FLASK_ENV`
- Value: `production`

**SECRET_KEY**
- Key: `SECRET_KEY`
- Value: Generate one by running in terminal:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Then paste the generated string

### Step 4: Redeploy

After saving the environment variables:
1. Render will **automatically redeploy** your service
2. Wait for the deployment to complete (~2-3 minutes)
3. Check the logs for success

## 🔍 Verify It's Fixed

After redeploying, check the logs. You should see:
```
✓ Using external database: dpg-xxxxx.oregon-postgres.render.com/dbname
```

Instead of:
```
⚠️  WARNING: Using localhost database!
```

## 📸 Visual Guide

Here's what to do in Render Dashboard:

1. **Left Menu** → Click your PostgreSQL database
2. **Copy** the "Internal Database URL"
3. **Left Menu** → Click your Web Service
4. **Environment** tab → Add Environment Variable
5. **Key**: `DATABASE_URL`
6. **Value**: [paste the URL]
7. **Save Changes** → Auto redeploys

## 🎯 Expected Result

Once DATABASE_URL is set correctly:
- ✅ Database connection successful
- ✅ Tables created automatically
- ✅ API endpoints work with real data
- ✅ No more "connection refused" errors

## ❓ Still Not Working?

If you still see errors after setting DATABASE_URL:

1. **Verify the URL format**:
   - Should start with `postgres://` or `postgresql://`
   - Should contain `@dpg-` or another Render host
   - Should NOT contain `localhost` or `127.0.0.1`

2. **Check you copied the right URL**:
   - Use **Internal Database URL** (for services in same region)
   - NOT External Database URL

3. **Verify environment variable is saved**:
   - Go to Environment tab
   - Confirm DATABASE_URL is listed
   - Click "Edit" to verify the value is correct

4. **Manual redeploy if needed**:
   - Click "Manual Deploy" → "Deploy latest commit"

## 🆘 Common Mistakes

❌ **Using External Database URL** - Use Internal instead
❌ **Not saving after adding variable** - Click "Save Changes"
❌ **Typo in variable name** - Must be exactly `DATABASE_URL`
❌ **Extra spaces** - Make sure no spaces before/after the URL

## 📞 Need More Help?

Share these from Render Dashboard:
1. Screenshot of Environment variables tab (hide sensitive values)
2. Latest deployment logs (first 50 lines)
3. The database connection string format (hide password)

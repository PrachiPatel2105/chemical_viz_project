# Deployment Guide - Vercel & Render

## 🚀 Deployment Strategy

**Backend (Django)**: Deploy to **Render** (Free tier available)
**Frontend (React)**: Deploy to **Vercel** (Free tier available)

---

## Part 1: Deploy Django Backend to Render

### Step 1: Prepare Backend for Deployment

First, create necessary configuration files:

#### 1.1 Create `build.sh` (for Render)
```bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

#### 1.2 Update `requirements.txt`
Add these production dependencies:
```
Django==5.0.1
djangorestframework==3.14.0
django-cors-headers==4.3.1
pandas==2.1.4
reportlab==4.0.8
matplotlib==3.10.7
requests==2.31.0
openpyxl==3.1.2
gunicorn==21.2.0
whitenoise==6.6.0
psycopg2-binary==2.9.9
```

#### 1.3 Update `chemical_viz_project/settings.py`
Add these production settings:

```python
import os
from pathlib import Path

# Add at the top after imports
import dj_database_url

# Update ALLOWED_HOSTS
ALLOWED_HOSTS = ['*']  # Or specify your Render domain

# Update DATABASES for production
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add WhiteNoise to MIDDLEWARE (after SecurityMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    # ... rest of middleware
]

# Update CORS for production
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.vercel.app",  # Update after deploying frontend
]
```

### Step 2: Deploy to Render

1. **Push code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Go to Render**: https://render.com
   - Sign up / Login with GitHub

3. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `chemical_viz_project` repository

4. **Configure Service**:
   ```
   Name: chemical-viz-backend
   Environment: Python 3
   Build Command: ./build.sh
   Start Command: gunicorn chemical_viz_project.wsgi:application
   ```

5. **Add Environment Variables**:
   ```
   PYTHON_VERSION=3.11.0
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ```

6. **Deploy**: Click "Create Web Service"

7. **Note your backend URL**: `https://chemical-viz-backend.onrender.com`

---

## Part 2: Deploy React Frontend to Vercel

### Step 1: Prepare Frontend for Deployment

#### 1.1 Update API Base URL

Create `chemical-viz-frontend/.env.production`:
```env
VITE_API_BASE_URL=https://chemical-viz-backend.onrender.com
```

#### 1.2 Update `App.jsx` to use environment variable:
```javascript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
});
```

#### 1.3 Create `vercel.json` in `chemical-viz-frontend/`:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### Step 2: Deploy to Vercel

**Option A: Using Vercel CLI**

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Navigate to frontend folder**:
   ```bash
   cd chemical-viz-frontend
   ```

3. **Deploy**:
   ```bash
   vercel
   ```
   - Follow prompts
   - Select "Yes" to link to existing project or create new
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

4. **Deploy to production**:
   ```bash
   vercel --prod
   ```

**Option B: Using Vercel Dashboard**

1. **Go to Vercel**: https://vercel.com
   - Sign up / Login with GitHub

2. **Import Project**:
   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - Select `chemical-viz-frontend` folder as root directory

3. **Configure Project**:
   ```
   Framework Preset: Vite
   Root Directory: chemical-viz-frontend
   Build Command: npm run build
   Output Directory: dist
   ```

4. **Add Environment Variables**:
   ```
   VITE_API_BASE_URL=https://chemical-viz-backend.onrender.com
   ```

5. **Deploy**: Click "Deploy"

6. **Note your frontend URL**: `https://your-app.vercel.app`

---

## Part 3: Final Configuration

### Update Backend CORS Settings

Go back to Render dashboard and update environment variable:

```
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
```

Or update `settings.py` and redeploy:
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
]
```

### Create Superuser on Render

In Render dashboard:
1. Go to your web service
2. Click "Shell" tab
3. Run:
   ```bash
   python manage.py createsuperuser
   ```

---

## 🎯 Quick Deployment Checklist

### Backend (Render):
- [ ] Create `build.sh` file
- [ ] Update `requirements.txt` with production dependencies
- [ ] Update `settings.py` for production
- [ ] Push to GitHub
- [ ] Create Render web service
- [ ] Configure environment variables
- [ ] Deploy and note backend URL
- [ ] Create superuser via Shell

### Frontend (Vercel):
- [ ] Create `.env.production` with backend URL
- [ ] Update `App.jsx` to use environment variable
- [ ] Create `vercel.json`
- [ ] Deploy via CLI or Dashboard
- [ ] Note frontend URL

### Final Steps:
- [ ] Update backend CORS with frontend URL
- [ ] Test registration and login
- [ ] Test file upload
- [ ] Test PDF download

---

## 🔧 Troubleshooting

### Backend Issues:
- **Static files not loading**: Check WhiteNoise configuration
- **Database errors**: Render provides PostgreSQL, update DATABASE_URL
- **CORS errors**: Verify CORS_ALLOWED_ORIGINS includes frontend URL

### Frontend Issues:
- **API connection failed**: Check VITE_API_BASE_URL in environment variables
- **Build failed**: Ensure all dependencies in package.json
- **404 on refresh**: Verify vercel.json rewrites configuration

---

## 💰 Cost

Both services offer **FREE tiers**:
- **Render**: Free tier with 750 hours/month
- **Vercel**: Free tier with unlimited deployments

---

## 📚 Additional Resources

- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- Django Deployment: https://docs.djangoproject.com/en/5.0/howto/deployment/

---

**Ready to deploy! Follow the steps above.** 🚀

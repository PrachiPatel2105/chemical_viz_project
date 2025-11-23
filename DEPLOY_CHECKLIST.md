# 🚀 Deployment Checklist

## ✅ Pre-Deployment (Completed)

- [x] Created `build.sh` for Render
- [x] Updated `requirements.txt` with production dependencies
- [x] Updated `settings.py` for production (WhiteNoise, CORS, environment variables)
- [x] Updated `App.jsx` to use environment variable for API URL
- [x] Created `.env.production` for frontend
- [x] Created `vercel.json` for frontend routing
- [x] Updated database configuration for production

## 📋 Deployment Steps

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

### Step 2: Deploy Backend to Render

1. Go to https://render.com and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `chemical-viz-backend`
   - **Environment**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn chemical_viz_project.wsgi:application`
   
5. Add Environment Variables:
   ```
   PYTHON_VERSION=3.11.0
   SECRET_KEY=your-random-secret-key-here
   DEBUG=False
   CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
   ```

6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Copy your backend URL: `https://chemical-viz-backend.onrender.com`

### Step 3: Create Superuser on Render

1. In Render dashboard, go to your service
2. Click "Shell" tab
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Follow prompts to create admin user

### Step 4: Deploy Frontend to Vercel

**Option A: Using Vercel CLI**
```bash
cd chemical-viz-frontend
npm install -g vercel
vercel login
vercel
# Follow prompts
vercel --prod
```

**Option B: Using Vercel Dashboard**
1. Go to https://vercel.com and sign in
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `chemical-viz-frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   
5. Add Environment Variable:
   ```
   VITE_API_BASE_URL=https://chemical-viz-backend.onrender.com
   ```

6. Click "Deploy"
7. Copy your frontend URL: `https://your-app.vercel.app`

### Step 5: Update Backend CORS

1. Go back to Render dashboard
2. Update environment variable:
   ```
   CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
   ```
3. Save and wait for automatic redeploy

### Step 6: Test Your Deployment

- [ ] Visit your frontend URL
- [ ] Test user registration
- [ ] Test login
- [ ] Upload a CSV file
- [ ] View charts and analytics
- [ ] Download PDF report
- [ ] Test logout

## 🔧 Troubleshooting

### Backend Issues

**Problem**: Static files not loading
**Solution**: Check WhiteNoise is in MIDDLEWARE and run `python manage.py collectstatic`

**Problem**: CORS errors
**Solution**: Verify CORS_ALLOWED_ORIGINS includes your Vercel URL (no trailing slash)

**Problem**: Database errors
**Solution**: Check DATABASE_URL environment variable in Render

### Frontend Issues

**Problem**: API connection failed
**Solution**: Check VITE_API_BASE_URL in Vercel environment variables

**Problem**: 404 on page refresh
**Solution**: Verify vercel.json exists with rewrites configuration

**Problem**: Build failed
**Solution**: Check all dependencies are in package.json

## 📝 Important URLs

After deployment, save these URLs:

- **Frontend**: https://your-app.vercel.app
- **Backend**: https://chemical-viz-backend.onrender.com
- **Admin Panel**: https://chemical-viz-backend.onrender.com/admin

## 🎯 Post-Deployment

- [ ] Update README.md with live URLs
- [ ] Test all features in production
- [ ] Monitor Render logs for errors
- [ ] Set up custom domain (optional)
- [ ] Enable HTTPS (automatic on both platforms)

## 💡 Tips

- Render free tier sleeps after 15 minutes of inactivity (first request may be slow)
- Vercel has unlimited bandwidth on free tier
- Both platforms auto-deploy on git push
- Use Render's persistent disk for media files (paid feature)

---

**Ready to deploy! Follow the steps above.** 🚀

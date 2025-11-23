# 🚀 Deploy Both Frontend & Backend on Render

## Overview

Deploy your entire Chemical Equipment Visualizer (Django backend + React frontend) on **Render.com** using their free tier.

**Advantages:**
- ✅ Everything in one place
- ✅ Single platform to manage
- ✅ Simpler CORS configuration
- ✅ Both services on same domain
- ✅ 100% Free tier available

---

## 📋 Deployment Strategy

We'll create **2 services** on Render:
1. **Web Service** - Django Backend (API)
2. **Static Site** - React Frontend (Built files)

---

## Part 1: Deploy Django Backend

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Create Backend Service on Render

1. Go to https://render.com and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:

```
Name: chemical-viz-backend
Environment: Python 3
Branch: main
Root Directory: (leave empty - uses project root)
Build Command: ./build.sh
Start Command: gunicorn chemical_viz_project.wsgi:application
```

5. Add Environment Variables:
```
PYTHON_VERSION=3.11.0
SECRET_KEY=your-random-secret-key-here
DEBUG=False
CORS_ALLOWED_ORIGINS=https://chemical-viz-frontend.onrender.com
```

6. Select **Free** plan
7. Click "Create Web Service"
8. Wait 5-10 minutes for deployment
9. **Copy your backend URL**: `https://chemical-viz-backend.onrender.com`

### Step 3: Create Superuser

1. In Render dashboard, go to your backend service
2. Click "Shell" tab
3. Run:
```bash
python manage.py createsuperuser
```

---

## Part 2: Deploy React Frontend

### Step 1: Update Frontend Configuration

Update `chemical-viz-frontend/.env.production`:
```env
VITE_API_BASE_URL=https://chemical-viz-backend.onrender.com
```

### Step 2: Create Build Script for Frontend

Create `chemical-viz-frontend/build-render.sh`:
```bash
#!/usr/bin/env bash
set -o errexit

npm install
npm run build
```

### Step 3: Create Static Site on Render

1. In Render dashboard, click "New +" → "Static Site"
2. Select your GitHub repository
3. Configure:

```
Name: chemical-viz-frontend
Branch: main
Root Directory: chemical-viz-frontend
Build Command: npm install && npm run build
Publish Directory: chemical-viz-frontend/dist
```

4. Add Environment Variable:
```
VITE_API_BASE_URL=https://chemical-viz-backend.onrender.com
```

5. Select **Free** plan
6. Click "Create Static Site"
7. Wait 2-3 minutes for deployment
8. **Copy your frontend URL**: `https://chemical-viz-frontend.onrender.com`

### Step 4: Update Backend CORS

1. Go back to your backend service
2. Update environment variable:
```
CORS_ALLOWED_ORIGINS=https://chemical-viz-frontend.onrender.com
```
3. Save (will auto-redeploy)

---

## 🎯 Final URLs

After deployment, you'll have:
- **Frontend**: https://chemical-viz-frontend.onrender.com
- **Backend API**: https://chemical-viz-backend.onrender.com
- **Admin Panel**: https://chemical-viz-backend.onrender.com/admin

---

## ✅ Testing Your Deployment

Visit your frontend URL and test:
1. ✓ User registration
2. ✓ Login
3. ✓ Upload CSV file
4. ✓ View charts
5. ✓ Download PDF report

---

## 📊 Render Free Tier Limits

| Service | Type | Free Tier |
|---------|------|-----------|
| Backend | Web Service | 750 hours/month |
| Frontend | Static Site | Unlimited bandwidth |
| **Total Cost** | | **$0/month** |

**Note**: Free tier web services sleep after 15 minutes of inactivity. First request after sleep takes 30-60 seconds.

---

## 🔧 Alternative: Single Service Deployment

You can also serve both from a single Django service:

### Option: Django Serves React Build

1. Build React app locally:
```bash
cd chemical-viz-frontend
npm run build
```

2. Copy `dist` folder to Django `staticfiles/`

3. Update Django `urls.py` to serve React:
```python
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('data_api.urls')),
    path('', TemplateView.as_view(template_name='index.html')),
]
```

4. Deploy only the backend service

**Pros**: Single service, simpler
**Cons**: More complex setup, slower frontend updates

---

## 🆚 Render vs Vercel Comparison

| Feature | Render Only | Render + Vercel |
|---------|-------------|-----------------|
| Setup Complexity | Medium | Easy |
| Management | Single platform | Two platforms |
| Frontend Performance | Good | Excellent (CDN) |
| Backend Performance | Same | Same |
| Free Tier | 750 hrs backend | 750 hrs backend + unlimited frontend |
| Auto-deploy | Yes | Yes |
| Custom domains | Yes (both) | Yes (both) |

**Recommendation**: 
- **Render Only**: If you prefer single platform
- **Render + Vercel**: If you want best frontend performance

---

## 📝 Quick Deployment Checklist

### Backend Service:
- [ ] Push code to GitHub
- [ ] Create Web Service on Render
- [ ] Configure build and start commands
- [ ] Add environment variables
- [ ] Deploy and note URL
- [ ] Create superuser via Shell

### Frontend Static Site:
- [ ] Update .env.production with backend URL
- [ ] Create Static Site on Render
- [ ] Configure build command and publish directory
- [ ] Add environment variable
- [ ] Deploy and note URL
- [ ] Update backend CORS with frontend URL

### Testing:
- [ ] Test registration
- [ ] Test login
- [ ] Test file upload
- [ ] Test charts display
- [ ] Test PDF download

---

## 🔄 Continuous Deployment

Both services auto-deploy when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Render automatically:
1. Detects the push
2. Rebuilds affected services
3. Deploys new version
4. No manual steps needed!

---

## 🆘 Troubleshooting

### Backend Issues

**Problem**: Build fails
**Solution**: Check build.sh has correct commands and requirements.txt is complete

**Problem**: Service won't start
**Solution**: Check Start Command is `gunicorn chemical_viz_project.wsgi:application`

**Problem**: Database errors
**Solution**: Run migrations via Shell: `python manage.py migrate`

### Frontend Issues

**Problem**: Build fails
**Solution**: Check package.json has all dependencies

**Problem**: Blank page
**Solution**: Check Publish Directory is `chemical-viz-frontend/dist`

**Problem**: API connection fails
**Solution**: Verify VITE_API_BASE_URL environment variable

### CORS Issues

**Problem**: CORS errors in browser
**Solution**: Ensure CORS_ALLOWED_ORIGINS in backend matches frontend URL exactly (no trailing slash)

---

## 💡 Pro Tips

1. **Custom Domains**: Both services support custom domains on free tier
2. **Environment Variables**: Use Render's environment variable management
3. **Logs**: Check service logs in Render dashboard for debugging
4. **Shell Access**: Use Shell tab for running Django commands
5. **Auto-deploy**: Disable if you want manual control over deployments

---

## 📚 Resources

- [Render Documentation](https://render.com/docs)
- [Render Static Sites](https://render.com/docs/static-sites)
- [Render Web Services](https://render.com/docs/web-services)
- [Django on Render](https://render.com/docs/deploy-django)

---

## ✨ You're Ready!

Follow the steps above to deploy both services on Render. Total deployment time: **15-20 minutes**.

**Start with Step 1: Push to GitHub!** 🚀

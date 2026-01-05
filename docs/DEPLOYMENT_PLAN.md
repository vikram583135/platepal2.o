# PlatePal Deployment Plan

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLOUDFLARE (CDN/DNS)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           ▼                           ▼                           ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   VERCEL/NETLIFY    │  │   VERCEL/NETLIFY    │  │   VERCEL/NETLIFY    │
│   Customer App      │  │   Restaurant App    │  │   Admin/Delivery    │
│   app.platepal.com  │  │   biz.platepal.com  │  │   admin/rider.xxx   │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAILWAY / RENDER                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Django API     │  │  Django         │  │  Celery         │             │
│  │  (Gunicorn)     │  │  Channels       │  │  Workers        │             │
│  │  api.platepal   │  │  (Daphne/ASGI)  │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           ▼                           ▼                           ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   NEON / SUPABASE   │  │   UPSTASH REDIS     │  │   CLOUDINARY        │
│   PostgreSQL        │  │   Cache + Pub/Sub   │  │   Media Storage     │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

---

## Deployment Options

### Option A: Budget-Friendly (Free Tier Focus)
Best for: MVP/Testing - **$0-20/month**

| Component | Service | Cost |
|-----------|---------|------|
| Frontend Apps (4) | Vercel | Free |
| Django API | Railway | Free tier (500 hrs) |
| PostgreSQL | Neon | Free (0.5GB) |
| Redis | Upstash | Free (10K/day) |
| Media | Cloudinary | Free (25GB) |
| Domain & SSL | Cloudflare | Free |

### Option B: Production-Ready
Best for: Live Production - **$50-100/month**

| Component | Service | Cost |
|-----------|---------|------|
| Frontend Apps (4) | Vercel Pro | $20/month |
| Django API + Channels | Railway | $20/month |
| Celery Workers | Railway | $10/month |
| PostgreSQL | Neon Pro / Supabase | $25/month |
| Redis | Upstash Pro | $10/month |
| Media | Cloudinary | $99/month or S3 |
| Domain & SSL | Cloudflare | Free |

### Option C: Enterprise Scale
Best for: High Traffic - **$200+/month**

| Component | Service | Cost |
|-----------|---------|------|
| Frontend Apps | Vercel Enterprise | Custom |
| Backend | AWS ECS / GCP Cloud Run | Variable |
| Database | AWS RDS / GCP Cloud SQL | Variable |
| Redis | AWS ElastiCache | Variable |
| Media | AWS S3 + CloudFront | Variable |

---

## Step-by-Step Deployment Guide

### Phase 1: Database & Cache Setup

#### 1.1 PostgreSQL (Neon - Recommended)
```bash
# 1. Create account at https://neon.tech
# 2. Create new project "platepal-production"
# 3. Copy connection string:
#    postgresql://user:pass@ep-xxx.region.aws.neon.tech/platepal
```

#### 1.2 Redis (Upstash - Recommended)
```bash
# 1. Create account at https://upstash.com
# 2. Create Redis database "platepal-redis"
# 3. Copy REDIS_URL:
#    redis://default:xxx@xxx.upstash.io:6379
```

---

### Phase 2: Backend Deployment (Railway)

#### 2.1 Prepare Backend for Production

Create `backend/Procfile`:
```
web: gunicorn platepal.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A platepal worker --loglevel=info
channels: daphne -b 0.0.0.0 -p $PORT platepal.asgi:application
```

Create `backend/railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn platepal.wsgi:application --bind 0.0.0.0:$PORT",
    "healthcheckPath": "/api/health/",
    "healthcheckTimeout": 100
  }
}
```

Update `backend/platepal/settings.py` for production:
```python
import os

# Production settings
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# CORS
CORS_ALLOWED_ORIGINS = [
    "https://app.platepal.com",
    "https://biz.platepal.com",
    "https://admin.platepal.com",
    "https://rider.platepal.com",
]
```

#### 2.2 Deploy to Railway
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and link project
railway login
cd backend
railway link

# 3. Add environment variables
railway variables set \
  DEBUG=False \
  SECRET_KEY=your-production-secret-key \
  ALLOWED_HOSTS=api.platepal.com \
  DB_NAME=platepal \
  DB_USER=xxx \
  DB_PASSWORD=xxx \
  DB_HOST=ep-xxx.neon.tech \
  REDIS_URL=redis://xxx@xxx.upstash.io:6379

# 4. Deploy
railway up
```

---

### Phase 3: Frontend Deployment (Vercel)

#### 3.1 Customer App
```bash
cd frontend

# Build customer app
npm run build:customer

# Deploy to Vercel
npx vercel --prod
# Set custom domain: app.platepal.com
```

Create `frontend/apps/customer/vercel.json`:
```json
{
  "buildCommand": "cd ../.. && npm run build:customer",
  "outputDirectory": "../../dist/customer",
  "framework": "vite",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

#### 3.2 Deploy All Apps
```bash
# Restaurant App → biz.platepal.com
# Admin App → admin.platepal.com  
# Delivery App → rider.platepal.com
```

Environment variables for each frontend:
```
VITE_API_BASE_URL=https://api.platepal.com/api
VITE_WS_URL=wss://ws.platepal.com/ws
```

---

### Phase 4: Domain & SSL Setup (Cloudflare)

```bash
# 1. Add domain to Cloudflare
# 2. Configure DNS records:

# A/CNAME Records:
api.platepal.com     → railway-app.railway.app (CNAME)
ws.platepal.com      → railway-channels.railway.app (CNAME)
app.platepal.com     → cname.vercel-dns.com (CNAME)
biz.platepal.com     → cname.vercel-dns.com (CNAME)
admin.platepal.com   → cname.vercel-dns.com (CNAME)
rider.platepal.com   → cname.vercel-dns.com (CNAME)

# 3. Enable SSL/TLS (Full Strict mode)
# 4. Enable caching for static assets
```

---

### Phase 5: CI/CD Pipeline

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy PlatePal

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: platepal-api
          
  deploy-frontend:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app: [customer, restaurant, admin, delivery]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build:${{ matrix.app }}
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID_${{ matrix.app }} }}
          working-directory: frontend
```

---

## Environment Variables Checklist

### Backend (Railway)
```env
# Django
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=api.platepal.com,ws.platepal.com

# Database (Neon)
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=5432

# Redis (Upstash)
REDIS_URL=

# CORS
CORS_ALLOWED_ORIGINS=https://app.platepal.com,https://biz.platepal.com

# Media (Cloudinary)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

### Frontend Apps (Vercel)
```env
VITE_API_BASE_URL=https://api.platepal.com/api
VITE_WS_URL=wss://ws.platepal.com/ws
```

---

## Cost Summary

| Tier | Monthly Cost | Best For |
|------|--------------|----------|
| Free Tier | $0-5 | Development/Testing |
| Starter | $25-50 | Early Startup |
| Production | $100-200 | Live Business |
| Scale | $500+ | High Traffic |

---

## Quick Start Commands

```bash
# 1. Setup databases
# (Create Neon + Upstash accounts, copy credentials)

# 2. Deploy backend
cd backend
railway login
railway up

# 3. Deploy frontends
cd frontend
vercel --prod  # Repeat for each app

# 4. Configure domains in Cloudflare
# 5. Test all endpoints
```

---

## Monitoring & Maintenance

- **Uptime**: Use UptimeRobot (free) or Better Uptime
- **Logs**: Railway built-in logs + Logtail
- **Errors**: Sentry (free tier)
- **Analytics**: Vercel Analytics + Google Analytics

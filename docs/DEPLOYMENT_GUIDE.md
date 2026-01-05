# PlatePal Deployment Guide

This guide covers all manual steps required to deploy PlatePal to production.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [External Services Setup](#external-services-setup)
3. [Backend Deployment (Railway)](#backend-deployment-railway)
4. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
5. [Domain & DNS Configuration](#domain--dns-configuration)
6. [GitHub Secrets Configuration](#github-secrets-configuration)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Optional Enhancements](#optional-enhancements)

---

## Prerequisites

Before starting, ensure you have:

- [ ] GitHub account with repository access
- [ ] Node.js 20+ installed locally
- [ ] Python 3.11+ installed locally
- [ ] Credit/debit card (for some services, though free tiers are available)
- [ ] Custom domain (optional but recommended)

---

## External Services Setup

### 1. PostgreSQL Database (Neon) - REQUIRED

1. [ ] Go to [https://neon.tech](https://neon.tech) and create an account
2. [ ] Create a new project named `platepal-production`
3. [ ] Create a database named `platepal`
4. [ ] Copy the connection details:
   - **Host**: `ep-xxx-xxx-xxx.region.aws.neon.tech`
   - **Database**: `platepal`
   - **User**: (provided)
   - **Password**: (provided)
   - **Connection String**: `postgresql://user:pass@ep-xxx.region.aws.neon.tech/platepal?sslmode=require`

> **Free Tier**: 0.5 GB storage, autoscaling compute

---

### 2. Redis Cache (Upstash) - REQUIRED

1. [ ] Go to [https://upstash.com](https://upstash.com) and create an account
2. [ ] Create a new Redis database named `platepal-redis`
3. [ ] Select the region closest to your backend server
4. [ ] Copy the connection details:
   - **REDIS_URL**: `rediss://default:xxx@xxx.upstash.io:6379`
   - Or individual values:
     - **Host**: `xxx.upstash.io`
     - **Port**: `6379`
     - **Password**: (provided)

> **Free Tier**: 10,000 commands/day

---

### 3. Media Storage (Cloudinary) - RECOMMENDED

1. [ ] Go to [https://cloudinary.com](https://cloudinary.com) and create an account
2. [ ] Navigate to Dashboard → Settings
3. [ ] Copy the credentials:
   - **Cloud Name**: (your cloud name)
   - **API Key**: (provided)
   - **API Secret**: (provided)

> **Free Tier**: 25 GB storage, 25 GB bandwidth/month

---

### 4. Error Tracking (Sentry) - RECOMMENDED

1. [ ] Go to [https://sentry.io](https://sentry.io) and create an account
2. [ ] Create a new project → Select "Django"
3. [ ] Copy the **DSN** from the setup page:
   - **SENTRY_DSN**: `https://xxx@xxx.ingest.sentry.io/xxx`

> **Free Tier**: 5,000 errors/month

---

### 5. Domain Registrar & DNS (Cloudflare) - RECOMMENDED

1. [ ] Go to [https://cloudflare.com](https://cloudflare.com) and create an account
2. [ ] Add your domain (e.g., `platepal.com`)
3. [ ] Update nameservers at your domain registrar to Cloudflare's nameservers
4. [ ] Wait for DNS propagation (up to 24 hours)

> **Free Tier**: Unlimited bandwidth, free SSL

---

## Backend Deployment (Railway)

### Step 1: Create Railway Account

1. [ ] Go to [https://railway.app](https://railway.app)
2. [ ] Sign up with GitHub (recommended for easy integration)

### Step 2: Install Railway CLI

```bash
npm install -g @railway/cli
```

### Step 3: Create New Project

1. [ ] In Railway dashboard, click "New Project"
2. [ ] Select "Deploy from GitHub repo"
3. [ ] Connect your GitHub account if not already connected
4. [ ] Select the `platepal2.o` repository
5. [ ] Set the root directory to `/backend`

### Step 4: Configure Environment Variables

In Railway dashboard → Variables, add all these variables:

```env
# Django (REQUIRED)
SECRET_KEY=<generate-a-secure-64-char-random-string>
DEBUG=False
ALLOWED_HOSTS=your-railway-app.railway.app,api.platepal.com

# Database - Neon (REQUIRED)
DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/platepal?sslmode=require

# Redis - Upstash (REQUIRED)
REDIS_URL=rediss://default:xxx@xxx.upstash.io:6379
USE_REDIS=1

# CORS (REQUIRED - update with your actual domains)
CORS_ALLOWED_ORIGINS=https://app.platepal.com,https://biz.platepal.com,https://admin.platepal.com,https://rider.platepal.com

# Cloudinary (OPTIONAL but recommended)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Sentry (OPTIONAL but recommended)
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
SENTRY_ENVIRONMENT=production

# Email (OPTIONAL - for password reset, notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@platepal.com
```

> **Generate SECRET_KEY**: Run `python -c "import secrets; print(secrets.token_urlsafe(64))"`

### Step 5: Deploy

```bash
cd backend
railway login
railway link  # Select your project
railway up
```

### Step 6: Run Migrations

```bash
railway run python manage.py migrate
```

### Step 7: Create Superuser (Optional)

```bash
railway run python manage.py createsuperuser
```

### Step 8: Verify Health Check

Visit: `https://your-app.railway.app/api/health/`

Expected response:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "cache": "ok"
  }
}
```

---

## Frontend Deployment (Vercel)

### Step 1: Create Vercel Account

1. [ ] Go to [https://vercel.com](https://vercel.com)
2. [ ] Sign up with GitHub (recommended)

### Step 2: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 3: Deploy Customer App

```bash
cd frontend/apps/customer
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Select your account
# - Link to existing project? No
# - Project name: platepal-customer
# - Directory: ./
# - Override settings? No
```

Add environment variables in Vercel dashboard:
```env
VITE_API_BASE_URL=https://api.platepal.com/api
VITE_WS_URL=wss://api.platepal.com/ws
```

Deploy to production:
```bash
vercel --prod
```

### Step 4: Deploy Restaurant App

```bash
cd frontend/apps/restaurant
vercel
# Project name: platepal-restaurant
vercel --prod
```

### Step 5: Deploy Admin App

```bash
cd frontend/apps/admin
vercel
# Project name: platepal-admin
vercel --prod
```

### Step 6: Deploy Delivery App

```bash
cd frontend/apps/delivery
vercel
# Project name: platepal-delivery
vercel --prod
```

### Step 7: Note Project IDs

For each app, go to Vercel dashboard → Project Settings → General and note:
- [ ] **Vercel Org ID**: (same for all projects)
- [ ] **Customer Project ID**
- [ ] **Restaurant Project ID**
- [ ] **Admin Project ID**
- [ ] **Delivery Project ID**

---

## Domain & DNS Configuration

### Step 1: Add Custom Domains in Vercel

For each frontend app:
1. [ ] Go to Project → Settings → Domains
2. [ ] Add domain:
   - Customer: `app.platepal.com`
   - Restaurant: `biz.platepal.com`
   - Admin: `admin.platepal.com`
   - Delivery: `rider.platepal.com`

### Step 2: Add Custom Domain in Railway

1. [ ] Go to Railway project → Settings → Domains
2. [ ] Add custom domain: `api.platepal.com`

### Step 3: Configure Cloudflare DNS

Add these DNS records in Cloudflare:

| Type  | Name    | Target                          | Proxy |
|-------|---------|--------------------------------|-------|
| CNAME | api     | your-app.railway.app           | ✅    |
| CNAME | app     | cname.vercel-dns.com           | ❌    |
| CNAME | biz     | cname.vercel-dns.com           | ❌    |
| CNAME | admin   | cname.vercel-dns.com           | ❌    |
| CNAME | rider   | cname.vercel-dns.com           | ❌    |

> **Note**: Vercel domains should have Cloudflare proxy OFF (gray cloud)

### Step 4: Configure SSL/TLS

In Cloudflare → SSL/TLS:
1. [ ] Set mode to "Full (strict)"
2. [ ] Enable "Always Use HTTPS"
3. [ ] Enable "Automatic HTTPS Rewrites"

---

## GitHub Secrets Configuration

For automated CI/CD deployments, add these secrets to your GitHub repository:

Go to: Repository → Settings → Secrets and variables → Actions

### Required Secrets

| Secret Name | Where to Get It |
|-------------|-----------------|
| `RAILWAY_TOKEN` | Railway → Account Settings → Tokens → Create Token |
| `VERCEL_TOKEN` | Vercel → Account Settings → Tokens → Create Token |
| `VERCEL_ORG_ID` | Vercel → Team Settings → General → Team ID |
| `VERCEL_PROJECT_ID_CUSTOMER` | Vercel → Customer Project → Settings → Project ID |
| `VERCEL_PROJECT_ID_RESTAURANT` | Vercel → Restaurant Project → Settings → Project ID |
| `VERCEL_PROJECT_ID_ADMIN` | Vercel → Admin Project → Settings → Project ID |
| `VERCEL_PROJECT_ID_DELIVERY` | Vercel → Delivery Project → Settings → Project ID |
| `VITE_API_BASE_URL` | `https://api.platepal.com/api` |
| `VITE_WS_URL` | `wss://api.platepal.com/ws` |

---

## Post-Deployment Verification

### Backend Checks

1. [ ] Health check: `https://api.platepal.com/api/health/`
2. [ ] API docs: `https://api.platepal.com/api/docs/`
3. [ ] Admin panel: `https://api.platepal.com/admin/`

### Frontend Checks

1. [ ] Customer app loads: `https://app.platepal.com`
2. [ ] Restaurant app loads: `https://biz.platepal.com`
3. [ ] Admin app loads: `https://admin.platepal.com`
4. [ ] Delivery app loads: `https://rider.platepal.com`

### Integration Checks

1. [ ] Login works on customer app
2. [ ] API calls succeed (no CORS errors)
3. [ ] WebSocket connections work
4. [ ] Images upload correctly (if Cloudinary configured)

---

## Optional Enhancements

### 1. Uptime Monitoring (Free)

1. [ ] Sign up at [https://uptimerobot.com](https://uptimerobot.com)
2. [ ] Add monitors for:
   - `https://api.platepal.com/api/health/`
   - `https://app.platepal.com`
   - `https://biz.platepal.com`

### 2. Analytics

1. [ ] Add Google Analytics to frontend apps
2. [ ] Enable Vercel Analytics (in project settings)

### 3. WebSocket Server (Separate Process)

For production WebSocket support, create a separate Railway service:
1. [ ] Create new service in Railway
2. [ ] Set start command: `daphne -b 0.0.0.0 -p $PORT platepal.asgi:application`
3. [ ] Add domain: `ws.platepal.com`

### 4. Celery Worker (Background Tasks)

Create a separate Railway service for Celery:
1. [ ] Create new service in Railway
2. [ ] Set start command: `celery -A platepal worker --loglevel=info`
3. [ ] Add same environment variables as main API

---

## Summary Checklist

### Services to Create (Manual)
- [ ] Neon PostgreSQL database
- [ ] Upstash Redis instance
- [ ] Cloudinary account (optional)
- [ ] Sentry project (optional)
- [ ] Railway account + project
- [ ] Vercel account + 4 projects

### Configurations to Set (Manual)
- [ ] Railway environment variables (15+ variables)
- [ ] Vercel environment variables (2 per app)
- [ ] Cloudflare DNS records (5 CNAME entries)
- [ ] GitHub repository secrets (9 secrets)
- [ ] Custom domains in Railway and Vercel

### Commands to Run (Manual)
- [ ] `railway up` - Backend deployment
- [ ] `railway run python manage.py migrate` - Database migrations
- [ ] `vercel --prod` - Frontend deployments (4 times)

---

## Estimated Time

| Task | Time |
|------|------|
| External services setup | 30-45 min |
| Backend deployment | 15-20 min |
| Frontend deployment | 20-30 min |
| DNS configuration | 15-20 min + propagation |
| GitHub secrets | 10-15 min |
| Verification | 15-20 min |
| **Total** | **~2-3 hours** |

---

## Support

If you encounter issues:
1. Check Railway logs: `railway logs`
2. Check Vercel build logs in dashboard
3. Verify all environment variables are set correctly
4. Test health endpoint: `/api/health/`
5. Check browser console for CORS or WebSocket errors

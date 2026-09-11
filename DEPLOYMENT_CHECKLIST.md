# SmartPath Deployment Checklist

## Pre-Deployment

### Repository Setup
- [ ] Code pushed to GitHub (main branch)
- [ ] Repository is public or connected to Vercel/Render/Railway/Fly
- [ ] `.gitignore` excludes: `__pycache__/`, `node_modules/`, `.env`, `*.log`, `*.sqlite`, `models/`, `data/raw/`, `data/processed/`

### Environment Variables Prepared

#### Frontend (Vercel)
- [ ] `VITE_API_URL` = Backend URL (e.g., `https://smartpath-backend.onrender.com`)

#### Backend (Render/Railway/Fly)
- [ ] `FLASK_ENV=production`
- [ ] `TRAFFIC_PROVIDER=simulation`
- [ ] `WEATHER_PROVIDER=open_meteo`
- [ ] `INCIDENT_PROVIDER=simulation`
- [ ] `BACKEND_URL` = Your deployed backend URL
- [ ] `SECRET_KEY` (if using Flask sessions)
- [ ] `PORT` (auto-set by platform, but good to know)

---

## Frontend Deployment (Vercel)

### Initial Setup
- [ ] Go to https://vercel.com/new
- [ ] Import GitHub repository
- [ ] Configure:
  - Framework Preset: **Vite**
  - Root Directory: `frontend`
  - Build Command: `npm run build`
  - Output Directory: `dist`
  - Install Command: `npm install`
- [ ] Add Environment Variable: `VITE_API_URL` = `https://your-backend.onrender.com`
- [ ] Click **Deploy**

### Post-Deploy Verification
- [ ] Frontend loads at `https://your-app.vercel.app`
- [ ] No console errors in browser dev tools
- [ ] Map loads (Leaflet tiles visible)
- [ ] Route calculation works (or shows backend unavailable message)
- [ ] All UI components render correctly

### Custom Domain (Optional)
- [ ] Add domain in Vercel Settings → Domains
- [ ] Configure DNS (CNAME to `cname.vercel-dns.com`)
- [ ] SSL certificate auto-provisioned
- [ ] Update `VITE_API_URL` if backend on subdomain

---

## Backend Deployment (Choose One)

### Option A: Render (Recommended for Free Tier)

#### Initial Setup
- [ ] Go to https://dashboard.render.com
- [ ] New → Web Service → Connect GitHub repo
- [ ] Configure:
  - Name: `smartpath-backend`
  - Region: Oregon (or closest)
  - Branch: `main`
  - Root Directory: `backend`
  - Build Command: `pip install --no-cache-dir -r requirements.txt`
  - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app`
  - Plan: Free
- [ ] Add Environment Variables (from above)
- [ ] Create Service

#### Post-Deploy
- [ ] Wait for build (10-15 min first time)
- [ ] Check logs for: `[GraphLoader] Graph loaded: X nodes, Y edges`
- [ ] Health check passes: `https://your-app.onrender.com/api/health`
- [ ] Test route endpoint: `POST /api/route`

### Option B: Railway

- [ ] `railway login`
- [ ] `railway init` (select repo)
- [ ] `railway up`
- [ ] Add env vars in Railway dashboard
- [ ] Verify deployment

### Option C: Fly.io
- [ ] `fly launch --dockerfile backend/Dockerfile`
- [ ] Edit `fly.toml` if needed
- [ ] `fly deploy`
- [ ] `fly secrets set FLASK_ENV=production ...`

### Option D: Docker (Any Cloud)
- [ ] `docker build -t smartpath-backend ./backend`
- [ ] `docker run -p 5000:5000 -e FLASK_ENV=production smartpath-backend`
- [ ] Push to registry: `docker push your-registry/smartpath-backend`
- [ ] Deploy to your cloud provider

---

## Integration Testing

### Frontend → Backend
- [ ] Open frontend URL
- [ ] Set source and destination on map
- [ ] Select vehicle and mode
- [ ] Click "Calculate Route"
- [ ] Verify route appears on map
- [ ] Check metrics panel shows data
- [ ] Test "Compare" button
- [ ] Test blockage simulation
- [ ] Test weather/traffic/incidents panels

### API Endpoints Direct
- [ ] `GET /api/health` → `{ "status": "healthy" }`
- [ ] `GET /api/map-bounds` → Returns bounds
- [ ] `GET /api/vehicles` → Returns vehicle configs
- [ ] `GET /api/analytics` → Returns metrics
- [ ] `POST /api/route` → Returns route with segments
- [ ] `GET /api/weather?lat=12.97&lng=77.59` → Returns weather
- [ ] `GET /api/traffic` → Returns traffic data
- [ ] `GET /api/incidents` → Returns incidents

---

## Performance & Monitoring

### Frontend (Vercel)
- [ ] Enable Vercel Analytics (Project Settings → Analytics)
- [ ] Enable Vercel Speed Insights
- [ ] Check Core Web Vitals

### Backend (Platform Dependent)
- [ ] Enable logging (Render: Logs tab, Railway: Logs, Fly: `fly logs`)
- [ ] Set up uptime monitoring (UptimeRobot, BetterUptime, or platform native)
- [ ] Set up error alerting (Sentry, or platform alerts)

### Sentry Setup (Recommended)
- [ ] Frontend: Add `@sentry/react` and configure DSN
- [ ] Backend: Add `sentry-sdk[flask]` and configure DSN
- [ ] Test error reporting

---

## Security Checklist

- [ ] CORS configured for your Vercel domain only
- [ ] No secrets in frontend code (API keys, etc.)
- [ ] Backend uses HTTPS in production
- [ ] Rate limiting on API endpoints (consider adding)
- [ ] Input validation on all endpoints
- [ ] No debug mode in production (`FLASK_ENV=production`)
- [ ] Dependencies scanned for vulnerabilities (`npm audit`, `pip-audit`)

---

## Post-Launch

### Immediate (Day 1)
- [ ] Smoke test all user flows
- [ ] Monitor error rates
- [ ] Check backend resource usage (CPU/Memory)
- [ ] Verify DCRNN model loads correctly

### Week 1
- [ ] Review analytics
- [ ] Check for any 5xx errors
- [ ] Monitor database/graph cache size
- [ ] Verify DCRNN predictions are reasonable

### Ongoing
- [ ] Weekly: Check model performance metrics
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Retrain DCRNN with new data (if pipeline exists)
- [ ] As needed: Scale backend resources

---

## Rollback Plan

### Frontend (Vercel)
```bash
# Instant rollback to previous deployment
vercel rollback
# Or in dashboard: Deployments → Previous → Promote to Production
```

### Backend (Platform Dependent)
```bash
# Render: Dashboard → Deploys → Previous → Rollback
# Railway: railway rollback
# Fly: fly releases rollback
# Docker: docker tag old-version latest && docker push && redeploy
```

---

## Emergency Contacts / Resources

- **Vercel Status**: https://www.vercel-status.com
- **Render Status**: https://status.render.com
- **Railway Status**: https://status.railway.app
- **Fly.io Status**: https://status.fly.io
- **Vercel Docs**: https://vercel.com/docs
- **Render Docs**: https://render.com/docs
- **SmartPath Repo**: https://github.com/ShreeshaN2006/SmartPath

---

## Quick Commands Reference

```bash
# Local development
cd frontend && npm run dev          # Frontend on :3000
cd backend && python app.py         # Backend on :5000
vercel dev                          # Full stack local

# Deploy
vercel --prod                       # Deploy frontend to Vercel
railway up                          # Deploy to Railway
fly deploy                          # Deploy to Fly.io

# Logs
vercel logs                         # Vercel function logs
railway logs                        # Railway logs
fly logs                            # Fly logs

# Environment
vercel env ls                       # List Vercel env vars
vercel env add VITE_API_URL         # Add env var
```
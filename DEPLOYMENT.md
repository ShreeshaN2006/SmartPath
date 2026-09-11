# SmartPath Deployment Guide

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐
│   Vercel        │     │  Backend        │
│   (Frontend)    │────▶│  (Flask + ML)   │
│   React + Vite  │     │  Python/GPU     │
└─────────────────┘     └─────────────────┘
```

- **Frontend**: React + TypeScript + Vite → Deployed on Vercel
- **Backend**: Flask + DCRNN + OSMnx → Deployed on Render/Railway/Fly.io (GPU support needed)
- **Communication**: Frontend calls backend via REST API

---

## Quick Deploy (Frontend Only)

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Vercel deployment config"
git push origin main
```

### 2. Import on Vercel
1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add Environment Variable:
   - `VITE_API_URL` = `https://your-backend-url.onrender.com` (or your backend URL)
5. Deploy

---

## Backend Deployment (Required for Full Functionality)

The ML backend requires Python with GPU support for DCRNN inference. Vercel serverless functions cannot run PyTorch/GPU workloads.

### Option A: Render (Recommended - Free tier available)
1. Create `render.yaml` in project root:
```yaml
services:
  - type: web
    name: smartpath-backend
    env: python
    region: oregon
    plan: free
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && gunicorn app:app"
    envVars:
      - key: FLASK_ENV
        value: production
      - key: PYTHON_VERSION
        value: 3.11.0
```

2. Connect GitHub repo to Render
3. Deploy (first build takes 10-15 mins for PyTorch)

### Option B: Railway
```bash
railway login
railway init
railway up
```

### Option C: Fly.io (GPU support)
```bash
fly launch --dockerfile backend/Dockerfile
fly deploy
```

### Option D: Docker (Any Cloud)
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 5000
CMD ["gunicorn", "app:app"]
```

---

## Environment Variables

### Frontend (Vercel)
| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_URL` | Backend API URL (e.g., `https://smartpath-backend.onrender.com`) | Yes |

### Backend (Render/Railway/Fly)
| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `PORT` | Server port | `5000` (or `$PORT` on Render) |
| `BACKEND_URL` | Internal backend URL | `http://localhost:5000` |
| `TRAFFIC_PROVIDER` | Traffic data source | `simulation` |
| `WEATHER_PROVIDER` | Weather data source | `open_meteo` |
| `INCIDENT_PROVIDER` | Incident data source | `simulation` |

---

## Local Development

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
# Runs on http://localhost:5000
```

### With Vercel CLI (Full Stack Local)
```bash
npm i -g vercel
vercel dev
# Runs frontend on 3000, API routes on 3000/api/*
```

---

## Project Structure for Vercel

```
SmartPath/
├── api/                    # Vercel Serverless Functions (API proxies)
│   ├── health.ts
│   ├── route.ts
│   ├── weather.ts
│   ├── traffic.ts
│   ├── incidents.ts
│   ├── vehicles.ts
│   ├── analytics.ts
│   ├── map-bounds.ts
│   └── random-blockages.ts
├── frontend/               # React + Vite app
│   ├── src/
│   ├── package.json
│   ├── vercel.json         # (handled by root vercel.json)
│   └── .env.example
├── backend/                # Flask + ML (deploy separately)
│   ├── app.py
│   ├── requirements.txt
│   └── ...
├── vercel.json             # Root Vercel config
├── DEPLOYMENT.md           # This file
└── DEPLOYMENT_CHECKLIST.md
```

---

## Vercel Configuration Details

The `vercel.json` at project root handles:
- Build from `frontend/` directory
- Output to `frontend/dist`
- SPA routing (fallback to index.html)
- API routes under `/api/*` → serverless functions
- Environment variable injection for `VITE_API_URL`

---

## API Routes (Vercel Functions)

All routes proxy to backend:
- `GET  /api/health` - Health check
- `POST /api/route` - Calculate route
- `POST /api/replan` - Replan route
- `GET  /api/weather` - Weather data
- `GET  /api/traffic` - Traffic data
- `GET  /api/incidents` - Incidents
- `POST /api/incidents/simulate` - Simulate incident
- `GET  /api/vehicles` - Vehicle constraints
- `GET  /api/analytics` - Analytics
- `GET  /api/map-bounds` - Map bounds
- `POST /api/random-blockages` - Random blockages

---

## CORS Configuration

The backend (`backend/api/routes.py`) should allow Vercel domain:
```python
CORS(app, origins=[
    "https://your-app.vercel.app",
    "https://your-custom-domain.com",
    "http://localhost:3000"  # for local dev
])
```

---

## Troubleshooting

### Build Fails
- Check Node version (use 18+ or 20+)
- Clear cache: `vercel --force`
- Check build logs for TypeScript errors

### API Returns 503
- Check `BACKEND_URL` env var in Vercel
- Verify backend is deployed and healthy
- Check backend CORS settings

### Map Not Loading
- Leaflet CSS loaded from CDN
- Check browser console for CSP errors
- Verify tile server allows your domain

### Environment Variables Not Working
- Must prefix with `VITE_` for Vite
- Redeploy after adding env vars
- Check `vercel env ls` for current values

---

## Cost Estimates

| Service | Free Tier | Paid |
|---------|-----------|------|
| Vercel (Frontend) | ✅ Unlimited personal | $20/mo Pro |
| Render (Backend) | ✅ 750 hrs/mo | $7/mo |
| Railway | ✅ $5 credit/mo | $5/mo |
| Fly.io | ✅ 3 shared VMs | $5/mo+ |

---

## Custom Domain

1. Vercel Dashboard → Project → Settings → Domains
2. Add domain → Configure DNS
3. Update `VITE_API_URL` if backend on subdomain
4. Update backend CORS for new domain

---

## Monitoring

- **Vercel Analytics**: Enable in project settings
- **Backend Logs**: Render/Railway/Fly dashboard
- **Error Tracking**: Add Sentry to both frontend/backend
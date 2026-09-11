# SmartPath — Intelligent Delivery Route Optimization

> AI-based delivery route optimization system using **Hybrid A\* + DFS** and Spatio-Temporal Graph Neural Networks on real-world urban road networks.

![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwindcss&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-Deployed-black?logo=vercel&logoColor=white)

---

## Features

- **Hybrid A\*/DFS Algorithm** — Globally optimal A\* search with DFS-based local recovery around blockages
- **Spatio-Temporal GNNs (DCRNN)** — Deep graph neural network traffic flow forecasting
- **Real-World Road Network** — Uses OSMnx to load actual street data from OpenStreetMap
- **Haversine Heuristic** — Admissible heuristic using the great-circle distance formula
- **Dynamic Blockage Simulation** — Manual and random road blockages with live re-routing
- **Modern Interactive UI** — React 18 + Leaflet with click-to-set origin/destination/blockages and glassmorphism styling
- **Delivery Animation** — Animated delivery marker tracing the computed route
- **Performance Metrics** — Nodes expanded, path cost, execution time, MAE/RMSE analytics
- **Algorithm Comparison** — Side-by-side Hybrid A\*/DFS vs BFS analysis
- **Traffic Multiplier** — Real-time traffic simulation with dynamic edge weights

---

## Recommended VS Code Extensions

To get the best development experience in Visual Studio Code, install these extensions:

1. **Python** (Microsoft) — Essential for running the Flask backend and debugging.
2. **Pylance** (Microsoft) — Provides high-performance language support and type checking.
3. **Tailwind CSS IntelliSense** — Autocomplete for utility classes.
4. **ESLint** & **Prettier** — Code formatting and linting.

---

## Project Structure

```
├── api/                    # Vercel Serverless API proxies (TypeScript)
│   ├── analytics.ts
│   ├── health.ts
│   ├── incidents.ts
│   ├── map-bounds.ts
│   ├── random-blockages.ts
│   ├── route.ts
│   ├── traffic.ts
│   ├── vehicles.ts
│   └── weather.ts
├── backend/                # Python / Flask ML Backend
│   ├── app.py              # Flask REST API
│   ├── requirements.txt    # Python dependencies
│   ├── algorithms/         # Hybrid A*, DFS, and BFS implementations
│   ├── models/             # PyTorch DCRNN model architecture
│   └── utils/              # Graph loader, Haversine metrics, weather helpers
├── frontend/               # Modern React + Vite + TypeScript Frontend
│   ├── src/
│   │   ├── components/     # Reusable UI, Map, and Analytics components
│   │   ├── pages/          # LandingPage, PlannerPage
│   │   ├── hooks/          # Custom state and simulation hooks
│   │   └── lib/            # API client and distance utilities
│   ├── package.json
│   └── vite.config.ts
├── vercel.json             # Vercel deployment configuration
└── package.json            # Root configuration & scripts
```

---

## Quick Start

### Prerequisites

- Python 3.9+ installed
- `pip` package manager
- Internet connection (for first-time map download)

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Run the Server

```bash
python app.py
```

The first run will download the Bangalore road network (~3km radius) from OpenStreetMap and cache it locally. This takes 20-30 seconds. Subsequent starts load from cache instantly.

### Step 3: Open the App

Visit **http://localhost:5000** in your browser.

---

## Detailed VS Code Setup Guide

If you are running this project manually in Visual Studio Code, follow these steps:

1. **Open Folder**: Open VS Code and select `File > Open Folder...` and choose the **AI project** directory.
2. **Terminal**: Open a new terminal in VS Code (`Ctrl + ` ` ` or `Terminal > New Terminal`).
3. **Virtual Environment (Recommended)**:
   ```powershell
   # Create a virtual environment
   python -m venv venv
   
   # Activate it (Windows)
   .\venv\Scripts\activate
   ```
4. **Install Requirements**:
   ```powershell
   pip install -r backend/requirements.txt
   ```
5. **Run the App**:
   - Open `backend/app.py`
   - Press **F5** to start debugging, or run `python backend/app.py` in the terminal.
6. **Troubleshooting**:
   - If you see `ModuleNotFoundError`, ensure your VS Code Python Interpreter is set to the one inside your `venv`. Press `Ctrl+Shift+P` and type `Python: Select Interpreter`.
   - If the map doesn't load, ensure you have an active internet connection for the first-time download.

---

## How to Use

1. **Set Source** → Click "Source" button, then click the map
2. **Set Destination** → Click "Destination" button, then click the map
3. **Add Blockages** (optional) → Click "Manual Block" and click road locations, or "Random" for auto-generated blockages
4. **Calculate Route** → Click the purple "Calculate Route" button
5. **Compare Algorithms** → Click "Compare" to see Hybrid A\*/DFS vs BFS side-by-side

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Serve frontend |
| `/map-bounds` | GET | Get map bounding box |
| `/get-route` | POST | Compute hybrid A\*/DFS route |
| `/compare` | POST | Compare Hybrid vs BFS |
| `/random-blockages` | POST | Generate random blockages |

### Sample API Request

```json
POST /get-route
{
    "source": {"lat": 12.975, "lng": 77.590},
    "destination": {"lat": 12.965, "lng": 77.600},
    "blocked_coords": [
        {"lat": 12.970, "lng": 77.595}
    ]
}
```

### Sample Response

```json
{
    "success": true,
    "astar": {
        "path_coords": [[12.975, 77.590], ...],
        "cost": 3.45,
        "nodes_expanded": 127,
        "execution_time_ms": 15.23
    },
    "dfs": {
        "detour_coords": [[12.969, 77.594], ...],
        "nodes_expanded": 18,
        "execution_time_ms": 2.1
    },
    "merged": {
        "path_coords": [[12.975, 77.590], ...],
        "cost": 4.12
    },
    "blockage_detected": true,
    "total_time_ms": 18.5
}
```

---

## How Hybrid A\*/DFS Works

### 1. A\* Search (Global Optimal)

A\* uses a priority queue with evaluation function **f(n) = g(n) + h(n)**:
- **g(n)** = actual travel time from start to current node
- **h(n)** = Haversine distance heuristic (never overestimates → admissible)

The Haversine formula computes the great-circle distance:

```
h(n) = 2R × arcsin(√(sin²(Δlat/2) + cos(lat₁)·cos(lat₂)·sin²(Δlon/2)))
R = 6371 km
```

### 2. Blockage Detection

After A\* finds the optimal path, the system checks each node and edge against the blocked set. If any intersection is found, the blockage index is recorded.

### 3. DFS Recovery (Local Detour)

Starting from the node just before the blockage, DFS explores neighbors depth-first to find an alternate route that reconnects with the original A\* path downstream of the blockage. This is bounded by `max_depth=50` to prevent excessive exploration.

### 4. Path Merging

The final route is assembled as:
```
[A* path before blockage] + [DFS detour] + [A* path after rejoin point]
```

### 5. Fallback

If DFS fails to find a recovery path, the system falls back to running A\* with full blockage awareness to find a completely new route.

---

## Sample Test Cases

### Test 1: Direct Route (No Blockage)
- Source: (12.975, 77.590)
- Destination: (12.965, 77.600)
- Expected: A\* finds optimal path, no DFS triggered

### Test 2: Route with Blockage
- Source: (12.975, 77.590)
- Destination: (12.965, 77.600)
- Blockage: (12.970, 77.595)
- Expected: A\* finds initial path → blockage detected → DFS recovery → merged route

### Test 3: Multiple Blockages
- Use "Random" button to add 5 blockages
- Expected: A\* path may hit blockage, DFS explores around it

### Test 4: Algorithm Comparison
- Set source/destination → click "Compare"
- Expected: BFS explores significantly more nodes than Hybrid A\*/DFS

---

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Leaflet, Framer Motion, Lucide Icons |
| Backend | Python 3.11+, Flask, PyTorch (DCRNN), OSMnx, NetworkX, Scikit-learn |
| Routing Algorithms | Hybrid A* (Haversine Priority Queue) + DFS Detour Recovery + BFS Benchmark |
| Serverless Layer | Vercel Serverless Functions (`@vercel/node`) |
| Data Source | OpenStreetMap (via OSMnx road graph extraction) |
| Cloud Hosting | Vercel (Frontend & Serverless API), Render / Railway / Fly.io (ML Backend) |

---

## Deployment Guide

### 1. Deploy Frontend on Vercel
1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Update project and configurations"
   git push origin main
   ```
2. Go to [vercel.com/new](https://vercel.com/new) and import `ShreeshaN2006/SmartPath`.
3. Vercel will automatically detect `vercel.json` and build the application.
4. Set the environment variable:
   - `BACKEND_URL` (optional): The URL of your deployed Python backend (e.g., `https://smartpath-backend.onrender.com`).

### 2. Deploy Backend on Render / Railway
1. Create a new **Web Service** on Render.
2. Connect your GitHub repository (`ShreeshaN2006/SmartPath`).
3. Set the following settings:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment Variables**:
     - `FLASK_ENV`: `production`
     - `PYTHON_VERSION`: `3.11.0`

---

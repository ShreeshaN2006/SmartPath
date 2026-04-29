# SmartPath — Intelligent Delivery Route Optimization

> AI-based delivery route optimization system using **Hybrid A\* + DFS** on real-world urban road networks.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![Leaflet](https://img.shields.io/badge/Leaflet-1.9-brightgreen)

---

## Features

- **Hybrid A\*/DFS Algorithm** — Globally optimal A\* search with DFS-based local recovery around blockages
- **Real-World Road Network** — Uses OSMnx to load actual street data from OpenStreetMap
- **Haversine Heuristic** — Admissible heuristic using the great-circle distance formula
- **Dynamic Blockage Simulation** — Manual and random road blockages with live re-routing
- **Interactive Map** — Leaflet.js map with click-to-set source/destination/blockages
- **Delivery Animation** — Animated delivery marker tracing the computed route
- **Performance Metrics** — Nodes expanded, path cost, execution time
- **Algorithm Comparison** — Side-by-side Hybrid A\*/DFS vs BFS analysis
- **Traffic Multiplier** — Real-time traffic simulation with dynamic edge weights

---

## Recommended VS Code Extensions

To get the best development experience in Visual Studio Code, install these extensions:

1. **Python** (Microsoft) — Essential for running the Flask backend and debugging.
2. **Pylance** (Microsoft) — Provides high-performance language support and type checking.
3. **Prettier** (Prettier) — Ensures consistent styling for CSS and JavaScript files.
4. **Error Lens** (Optional) — Highlights errors directly in the code for faster debugging.
5. **Live Server** (Optional) — Useful if you are modifying the frontend without the Flask backend.

---

## Project Structure

```
backend/
  app.py                 # Flask REST API (serves frontend + 4 endpoints)
  requirements.txt       # Python dependencies
  algorithms/
    __init__.py
    astar.py             # Custom A* search with heapq + Haversine heuristic
    dfs.py               # DFS recovery for local blockage avoidance
    hybrid.py            # Hybrid A*/DFS orchestrator + BFS comparison
  utils/
    __init__.py
    haversine.py         # Haversine distance formula (admissible heuristic)
    graph_loader.py      # OSMnx graph loading with disk caching

frontend/
  index.html             # Main page with Leaflet map and control panels
  styles.css             # Dark-themed premium UI with glassmorphism
  script.js              # Map interaction, route drawing, and metrics
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
| Backend | Python 3, Flask, OSMnx, NetworkX |
| Frontend | HTML5, CSS3, JavaScript, Leaflet.js |
| Heuristic | Haversine formula |
| Data Source | OpenStreetMap (via OSMnx) |
| Graph Format | NetworkX MultiDiGraph |
| Deployment | Render, Railway, Vercel |

---

## Cloud Deployment (Render)

This application is ready to be deployed to **Render** or any other cloud provider that supports Python.

### 1. Prepare your Repository
- Ensure `backend/requirements.txt` includes `gunicorn`.
- Ensure `graph_cache.graphml` is committed (to avoid long download times during the first request).

### 2. Deploy to Render
1. Create a new **Web Service** on Render.
2. Connect your GitHub repository.
3. Use the following settings:
   - **Environment**: `Python 3`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Add Environment Variables:
   - `PORT`: `5000` (optional, Render sets this automatically)
   - `FLASK_ENV`: `production`

---

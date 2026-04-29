// ═══════════════════════════════════════════════════════════════
// SmartPath — Frontend Logic
// Interactive Leaflet.js map with route visualization,
// blockage simulation, and performance metrics
// ═══════════════════════════════════════════════════════════════

// ─── Configuration ───
const API_BASE = '';  // Same origin (Flask serves frontend)

// ─── Application State ───
let map;
let sourceMarker = null;
let destMarker = null;
let blockedMarkers = [];
let blockedCoords = [];
let routeLayers = [];
let deliveryMarker = null;
let deliveryAnimation = null;

// Interaction modes: 'source', 'dest', 'block', 'waypoint', or null
let currentMode = null;

// Multi-stop waypoints
let waypointMarkers = [];
let waypointCoords = [];

// Named route layer references for toggle visibility
let astarLayer = null;
let dfsLayer = null;
let mergedLayer = null;
let bfsLayer = null;
let blockageLayer = null;

// ─── DOM References ───
const btnSetSource   = document.getElementById('btnSetSource');
const btnSetDest     = document.getElementById('btnSetDest');
const btnBlockMode   = document.getElementById('btnBlockMode');
const btnRandomBlock = document.getElementById('btnRandomBlock');
const btnCalcRoute   = document.getElementById('btnCalcRoute');
const btnCompare     = document.getElementById('btnCompare');
const btnClear       = document.getElementById('btnClear');
const btnWaypoint    = document.getElementById('btnWaypointMode');
const trafficSlider  = document.getElementById('trafficSlider');
const trafficValue   = document.getElementById('trafficValue');
const mapTooltip     = document.getElementById('mapTooltip');
const loadingOverlay = document.getElementById('loadingOverlay');
const statusText     = document.querySelector('.status-text');
const statusDot      = document.querySelector('.status-dot');

// ═══════════════════════════════════════════════════════════════
// MAP INITIALIZATION
// ═══════════════════════════════════════════════════════════════

async function initMap() {
    // Create the Leaflet map
    map = L.map('map', {
        zoomControl: true,
        attributionControl: true
    }).setView([12.9716, 77.5946], 14);  // Default: Bangalore

    // Add tile layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors | SmartPath',
        maxZoom: 19
    }).addTo(map);

    // Map click handler
    map.on('click', handleMapClick);

    // Load map bounds from backend
    try {
        const resp = await fetch(`${API_BASE}/map-bounds`);
        const data = await resp.json();
        if (data.success) {
            const b = data.bounds;
            map.fitBounds([[b.south, b.west], [b.north, b.east]]);
            showToast('Map loaded — Bangalore road network ready', 'success');
        }
    } catch (err) {
        showToast('Backend not responding. Start the Flask server first.', 'error');
    }
}

// ═══════════════════════════════════════════════════════════════
// EVENT HANDLERS
// ═══════════════════════════════════════════════════════════════

// Mode buttons
btnSetSource.addEventListener('click', () => setMode('source'));
btnSetDest.addEventListener('click', () => setMode('dest'));
btnBlockMode.addEventListener('click', () => setMode('block'));
btnWaypoint.addEventListener('click', () => setMode('waypoint'));

// Action buttons
btnCalcRoute.addEventListener('click', calculateRoute);
btnCompare.addEventListener('click', runComparison);
btnRandomBlock.addEventListener('click', addRandomBlockages);
btnClear.addEventListener('click', clearAll);

// Traffic slider
trafficSlider.addEventListener('input', () => {
    trafficValue.textContent = `${parseFloat(trafficSlider.value).toFixed(1)}×`;
});

// Route layer toggles
document.getElementById('toggleAstar').addEventListener('change', (e) => toggleLayer(astarLayer, e.target.checked));
document.getElementById('toggleDfs').addEventListener('change', (e) => toggleLayer(dfsLayer, e.target.checked));
document.getElementById('toggleMerged').addEventListener('change', (e) => toggleLayer(mergedLayer, e.target.checked));
document.getElementById('toggleBfs').addEventListener('change', (e) => toggleLayer(bfsLayer, e.target.checked));

function toggleLayer(layer, visible) {
    if (!layer) return;
    if (visible) { map.addLayer(layer); }
    else { map.removeLayer(layer); }
}

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        e.target.classList.add('active');
        document.getElementById(`tab-${e.target.dataset.tab}`).classList.add('active');
    });
});

// ═══════════════════════════════════════════════════════════════
// MODE MANAGEMENT
// ═══════════════════════════════════════════════════════════════

function setMode(mode) {
    // Toggle mode off if already active
    if (currentMode === mode) {
        currentMode = null;
        updateModeUI();
        return;
    }

    currentMode = mode;
    updateModeUI();
}

function updateModeUI() {
    // Reset all mode buttons
    [btnSetSource, btnSetDest, btnBlockMode, btnWaypoint].forEach(b => b.classList.remove('active'));

    const tooltips = {
        source: '🟢 Click on the map to set SOURCE location',
        dest: '🔴 Click on the map to set DESTINATION location',
        block: '⛔ Click on the map to place road BLOCKAGES',
        waypoint: '🟣 Click on the map to add WAYPOINT stops',
        null: 'Select a mode then click the map'
    };

    mapTooltip.textContent = tooltips[currentMode] || tooltips[null];
    mapTooltip.classList.toggle('hidden', currentMode === null);

    if (currentMode === 'source') btnSetSource.classList.add('active');
    if (currentMode === 'dest') btnSetDest.classList.add('active');
    if (currentMode === 'block') btnBlockMode.classList.add('active');
    if (currentMode === 'waypoint') btnWaypoint.classList.add('active');
}

// ═══════════════════════════════════════════════════════════════
// MAP INTERACTION
// ═══════════════════════════════════════════════════════════════

function handleMapClick(e) {
    const { lat, lng } = e.latlng;

    switch (currentMode) {
        case 'source':
            setSourceMarker(lat, lng);
            showToast(`Source set: ${lat.toFixed(5)}, ${lng.toFixed(5)}`, 'info');
            currentMode = null;
            updateModeUI();
            break;

        case 'dest':
            setDestMarker(lat, lng);
            showToast(`Destination set: ${lat.toFixed(5)}, ${lng.toFixed(5)}`, 'info');
            currentMode = null;
            updateModeUI();
            break;

        case 'block':
            addBlockedNode(lat, lng);
            showToast(`Blockage placed: ${lat.toFixed(5)}, ${lng.toFixed(5)}`, 'warning');
            break;

        case 'waypoint':
            addWaypoint(lat, lng);
            showToast(`Waypoint #${waypointCoords.length} added`, 'info');
            break;
    }
}

// ─── Custom Marker Icons ───

function createIcon(color, symbol) {
    return L.divIcon({
        className: 'custom-marker',
        html: `<div style="
            width: 28px; height: 28px;
            background: ${color};
            border-radius: 50%;
            border: 3px solid white;
            display: flex; align-items: center; justify-content: center;
            font-size: 14px; font-weight: bold;
            box-shadow: 0 2px 12px ${color}88;
            color: white;
        ">${symbol}</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
    });
}

const sourceIcon  = createIcon('#22c55e', 'S');
const destIcon    = createIcon('#ef4444', 'D');
const blockedIcon = createIcon('#f43f5e', '✕');

function setSourceMarker(lat, lng) {
    if (sourceMarker) map.removeLayer(sourceMarker);
    sourceMarker = L.marker([lat, lng], { icon: sourceIcon })
        .addTo(map)
        .bindPopup('<strong>📍 Source</strong><br>Start location');
}

function setDestMarker(lat, lng) {
    if (destMarker) map.removeLayer(destMarker);
    destMarker = L.marker([lat, lng], { icon: destIcon })
        .addTo(map)
        .bindPopup('<strong>🎯 Destination</strong><br>End location');
}

function addBlockedNode(lat, lng) {
    const marker = L.marker([lat, lng], { icon: blockedIcon })
        .addTo(map)
        .bindPopup('<strong>⛔ Blocked Node</strong><br>Road blockage');

    blockedMarkers.push(marker);
    blockedCoords.push({ lat, lng });
}

function addWaypoint(lat, lng) {
    const num = waypointCoords.length + 1;
    const wpIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div class="waypoint-badge">${num}</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    const marker = L.marker([lat, lng], { icon: wpIcon })
        .addTo(map)
        .bindPopup(`<strong>🟣 Waypoint #${num}</strong><br>Delivery stop`);

    waypointMarkers.push(marker);
    waypointCoords.push({ lat, lng });
}

// ═══════════════════════════════════════════════════════════════
// ROUTE CALCULATION
// ═══════════════════════════════════════════════════════════════

async function calculateRoute() {
    if (!sourceMarker || !destMarker) {
        showToast('Please set both source and destination first', 'error');
        return;
    }

    const srcLatLng = sourceMarker.getLatLng();
    const dstLatLng = destMarker.getLatLng();
    const trafficMultiplier = parseFloat(trafficSlider.value);

    showLoading(true);
    setStatus('Computing...', '#f59e0b');
    clearRoutes();

    // Build the ordered list of stops: source -> waypoints -> destination
    const stops = [
        { lat: srcLatLng.lat, lng: srcLatLng.lng },
        ...waypointCoords,
        { lat: dstLatLng.lat, lng: dstLatLng.lng }
    ];

    try {
        if (stops.length === 2) {
            // Direct route (no waypoints)
            const data = await fetchRoute(stops[0], stops[1], trafficMultiplier);
            if (!data) return;
            drawRoutes(data);
            updateMetrics(data);
            if (data.merged && data.merged.success && data.merged.path_coords.length > 0) {
                animateDelivery(data.merged.path_coords);
            }
        } else {
            // Multi-stop: chain routes between consecutive stops
            let allMergedCoords = [];
            let totalCost = 0;
            let totalNodesExpanded = 0;
            let totalTime = 0;
            let lastData = null;

            for (let i = 0; i < stops.length - 1; i++) {
                setStatus(`Computing leg ${i + 1}/${stops.length - 1}...`, '#f59e0b');
                const data = await fetchRoute(stops[i], stops[i + 1], trafficMultiplier);
                if (!data) {
                    showToast(`Failed on leg ${i + 1}`, 'error');
                    showLoading(false);
                    return;
                }

                // Draw each leg's A* path (faded)
                if (data.astar && data.astar.path_coords && data.astar.path_coords.length > 1) {
                    const legLine = L.polyline(data.astar.path_coords, {
                        color: '#38bdf8', weight: 3, opacity: 0.3, dashArray: '6, 6'
                    }).addTo(map);
                    routeLayers.push(legLine);
                }

                if (data.merged && data.merged.success) {
                    // Remove duplicate connecting point
                    const coords = data.merged.path_coords;
                    if (allMergedCoords.length > 0 && coords.length > 0) {
                        allMergedCoords = allMergedCoords.concat(coords.slice(1));
                    } else {
                        allMergedCoords = allMergedCoords.concat(coords);
                    }
                    totalCost += data.merged.cost;
                }

                if (data.astar) totalNodesExpanded += data.astar.nodes_expanded;
                if (data.dfs) totalNodesExpanded += data.dfs.nodes_expanded;
                totalTime += data.total_time_ms;
                lastData = data;
            }

            // Draw the full merged multi-stop route
            if (allMergedCoords.length > 1) {
                mergedLayer = L.polyline(allMergedCoords, {
                    color: '#a78bfa', weight: 5, opacity: 0.9
                }).addTo(map);
                routeLayers.push(mergedLayer);
                map.fitBounds(mergedLayer.getBounds().pad(0.15));
                animateDelivery(allMergedCoords);
            }

            // Show combined metrics
            if (lastData) {
                setText('metricAstarNodes', totalNodesExpanded);
                setText('metricAstarTime', `${totalTime.toFixed(1)} ms`);
                setText('metricAstarCost', `${totalCost.toFixed(2)} min`);
                setText('metricMergedCost', `${totalCost.toFixed(2)} min`);
                setText('metricTotalTime', `${totalTime.toFixed(1)} ms`);
                setText('metricDfsNodes', lastData.blockage_detected ? (lastData.dfs ? lastData.dfs.nodes_expanded : 'N/A') : 'N/A');
                setText('metricDfsTime', '—');
            }
        }

        setStatus('Route Found', '#22c55e');
        showToast(`Route computed with ${stops.length} stops!`, 'success');

    } catch (err) {
        showLoading(false);
        setStatus('Error', '#ef4444');
        showToast(`Network error: ${err.message}`, 'error');
    }
}

async function fetchRoute(source, destination, trafficMultiplier) {
    try {
        const resp = await fetch(`${API_BASE}/get-route`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source: source,
                destination: destination,
                blocked_coords: blockedCoords,
                traffic_multiplier: trafficMultiplier
            })
        });

        const data = await resp.json();
        showLoading(false);

        if (!data.success) {
            showToast(`Error: ${data.error}`, 'error');
            setStatus('Error', '#ef4444');
            return null;
        }
        return data;
    } catch (err) {
        showLoading(false);
        showToast(`Network error: ${err.message}`, 'error');
        return null;
    }
}

// ═══════════════════════════════════════════════════════════════
// ROUTE DRAWING
// ═══════════════════════════════════════════════════════════════

function drawRoutes(data) {
    // 1. A* optimal path (dashed, blue)
    if (data.astar && data.astar.path_coords && data.astar.path_coords.length > 1) {
        astarLayer = L.polyline(data.astar.path_coords, {
            color: '#38bdf8', weight: 4, opacity: 0.6, dashArray: '8, 8'
        }).addTo(map);
        routeLayers.push(astarLayer);
    }

    // 2. DFS recovery path (dashed, orange)
    if (data.dfs && data.dfs.detour_coords && data.dfs.detour_coords.length > 1) {
        dfsLayer = L.polyline(data.dfs.detour_coords, {
            color: '#fb923c', weight: 5, opacity: 0.8, dashArray: '5, 10'
        }).addTo(map);
        routeLayers.push(dfsLayer);
    }

    // 3. Final merged route (solid, purple — on top)
    if (data.merged && data.merged.path_coords && data.merged.path_coords.length > 1) {
        mergedLayer = L.polyline(data.merged.path_coords, {
            color: '#a78bfa', weight: 5, opacity: 0.9
        }).addTo(map);
        routeLayers.push(mergedLayer);
        map.fitBounds(mergedLayer.getBounds().pad(0.15));
    }

    // 4. Blockage location marker (if detected)
    if (data.blockage_detected && data.blockage_location) {
        const bCoords = data.blockage_location.coords;
        blockageLayer = L.circleMarker([bCoords[0], bCoords[1]], {
            radius: 10, color: '#f43f5e', fillColor: '#f43f5e',
            fillOpacity: 0.5, weight: 3
        }).addTo(map).bindPopup('<strong>⚠️ Blockage Detected</strong><br>DFS recovery triggered here');
        routeLayers.push(blockageLayer);
    }

    // Sync toggle checkbox states
    document.getElementById('toggleAstar').checked = !!astarLayer;
    document.getElementById('toggleDfs').checked = !!dfsLayer;
    document.getElementById('toggleMerged').checked = !!mergedLayer;
}

// ═══════════════════════════════════════════════════════════════
// DELIVERY ANIMATION
// ═══════════════════════════════════════════════════════════════

function animateDelivery(coords) {
    // Stop any existing animation
    if (deliveryAnimation) clearInterval(deliveryAnimation);
    if (deliveryMarker) map.removeLayer(deliveryMarker);

    // Create delivery marker
    const deliveryIcon = L.divIcon({
        className: 'delivery-marker-container',
        html: '<div class="delivery-marker"></div>',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });

    deliveryMarker = L.marker(coords[0], { icon: deliveryIcon, zIndexOffset: 1000 }).addTo(map);

    let idx = 0;
    const speed = Math.max(30, Math.min(100, 3000 / coords.length));

    deliveryAnimation = setInterval(() => {
        idx++;
        if (idx >= coords.length) {
            clearInterval(deliveryAnimation);
            deliveryAnimation = null;
            if (deliveryMarker) map.removeLayer(deliveryMarker);
            showToast('🎉 Delivery completed!', 'success');
            return;
        }
        deliveryMarker.setLatLng(coords[idx]);
    }, speed);
}

// ═══════════════════════════════════════════════════════════════
// METRICS UPDATE
// ═══════════════════════════════════════════════════════════════

function updateMetrics(data) {
    // A* metrics
    if (data.astar) {
        setText('metricAstarNodes', data.astar.nodes_expanded);
        setText('metricAstarTime', `${data.astar.execution_time_ms} ms`);
        setText('metricAstarCost', (data.astar.cost == null || data.astar.cost === -1) ? '∞' : `${data.astar.cost.toFixed(2)} min`);
    }

    // DFS metrics
    if (data.dfs && data.dfs.success) {
        setText('metricDfsNodes', data.dfs.nodes_expanded);
        setText('metricDfsTime', `${data.dfs.execution_time_ms} ms`);
    } else {
        setText('metricDfsNodes', data.blockage_detected ? 'Failed' : 'N/A');
        setText('metricDfsTime', data.blockage_detected ? 'N/A' : '—');
    }

    // Merged metrics
    if (data.merged && data.merged.success) {
        const cost = data.merged.cost;
        setText('metricMergedCost', (cost == null || cost === -1) ? '∞' : `${cost.toFixed(2)} min`);
    } else {
        setText('metricMergedCost', '∞');
    }
    setText('metricTotalTime', `${data.total_time_ms} ms`);

    // Blockage card
    const blockCard = document.getElementById('blockageCard');
    if (data.blockage_detected) {
        blockCard.style.display = 'block';
    } else {
        blockCard.style.display = 'none';
    }
}

// ═══════════════════════════════════════════════════════════════
// COMPARISON
// ═══════════════════════════════════════════════════════════════

async function runComparison() {
    if (!sourceMarker || !destMarker) {
        showToast('Set source & destination first', 'error');
        return;
    }

    const srcLatLng = sourceMarker.getLatLng();
    const dstLatLng = destMarker.getLatLng();

    showLoading(true);
    setStatus('Comparing algorithms...', '#f59e0b');

    // Switch to comparison tab
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector('[data-tab="comparison"]').classList.add('active');
    document.getElementById('tab-comparison').classList.add('active');

    try {
        const resp = await fetch(`${API_BASE}/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source: { lat: srcLatLng.lat, lng: srcLatLng.lng },
                destination: { lat: dstLatLng.lat, lng: dstLatLng.lng },
                blocked_coords: blockedCoords,
                traffic_multiplier: parseFloat(trafficSlider.value)
            })
        });

        const data = await resp.json();
        showLoading(false);

        if (!data.success) {
            showToast(`Compare error: ${data.error}`, 'error');
            setStatus('Error', '#ef4444');
            return;
        }

        // Update comparison table
        setText('cmpHybridNodes', data.hybrid.nodes_expanded);
        setText('cmpBfsNodes', data.bfs.nodes_expanded);
        setText('cmpHybridTime', `${data.hybrid.execution_time_ms} ms`);
        setText('cmpBfsTime', `${data.bfs.execution_time_ms} ms`);
        setText('cmpHybridCost', (data.hybrid.cost == null || data.hybrid.cost === -1) ? '∞' : `${data.hybrid.cost.toFixed(2)}`);
        setText('cmpBfsCost', (data.bfs.cost == null || data.bfs.cost === -1) ? '∞' : `${data.bfs.cost.toFixed(2)}`);
        setText('cmpHybridSuccess', data.hybrid.success ? '✅ Yes' : '❌ No');
        setText('cmpBfsSuccess', data.bfs.success ? '✅ Yes' : '❌ No');

        // Draw BFS path on map (green)
        if (data.bfs.path_coords && data.bfs.path_coords.length > 1) {
            bfsLayer = L.polyline(data.bfs.path_coords, {
                color: '#34d399', weight: 4, opacity: 0.7, dashArray: '12, 6'
            }).addTo(map);
            routeLayers.push(bfsLayer);
            document.getElementById('toggleBfs').checked = true;
        }

        // Verdict
        const verdict = document.getElementById('comparisonVerdict');
        if (data.hybrid.success && data.bfs.success) {
            const efficiency = ((data.bfs.nodes_expanded - data.hybrid.nodes_expanded) / data.bfs.nodes_expanded * 100).toFixed(1);
            verdict.innerHTML = `
                <strong>🏆 Hybrid A*/DFS</strong> explored <strong>${Math.abs(efficiency)}%</strong> 
                ${efficiency > 0 ? 'fewer' : 'more'} nodes than BFS.<br>
                A* heuristic guides search toward the goal, while BFS explores blindly.
            `;
            verdict.classList.add('visible');
        } else {
            verdict.innerHTML = 'One or both algorithms failed to find a path.';
            verdict.classList.add('visible');
        }

        setStatus('Comparison complete', '#22c55e');
        showToast('Algorithm comparison complete!', 'success');

    } catch (err) {
        showLoading(false);
        setStatus('Error', '#ef4444');
        showToast(`Network error: ${err.message}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════════
// RANDOM BLOCKAGES
// ═══════════════════════════════════════════════════════════════

async function addRandomBlockages() {
    try {
        const bounds = map.getBounds();
        const resp = await fetch(`${API_BASE}/random-blockages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                count: 5,
                bounds: {
                    south: bounds.getSouth(),
                    north: bounds.getNorth(),
                    west: bounds.getWest(),
                    east: bounds.getEast()
                }
            })
        });

        const data = await resp.json();

        if (data.success) {
            data.blocked_coords.forEach(coord => {
                addBlockedNode(coord.lat, coord.lng);
            });
            showToast(`${data.count} random blockages added`, 'warning');
        }
    } catch (err) {
        showToast('Could not generate random blockages', 'error');
    }
}

// ═══════════════════════════════════════════════════════════════
// CLEAR / RESET
// ═══════════════════════════════════════════════════════════════

function clearAll() {
    // Clear routes
    clearRoutes();

    // Clear markers
    if (sourceMarker) { map.removeLayer(sourceMarker); sourceMarker = null; }
    if (destMarker) { map.removeLayer(destMarker); destMarker = null; }
    blockedMarkers.forEach(m => map.removeLayer(m));
    blockedMarkers = [];
    blockedCoords = [];

    // Clear delivery animation
    if (deliveryAnimation) { clearInterval(deliveryAnimation); deliveryAnimation = null; }
    if (deliveryMarker) { map.removeLayer(deliveryMarker); deliveryMarker = null; }

    // Reset metrics
    ['metricAstarNodes', 'metricAstarTime', 'metricAstarCost',
     'metricDfsNodes', 'metricDfsTime', 'metricMergedCost', 'metricTotalTime'
    ].forEach(id => setText(id, '—'));
    document.getElementById('blockageCard').style.display = 'none';

    // Reset comparison
    ['cmpHybridNodes', 'cmpBfsNodes', 'cmpHybridTime', 'cmpBfsTime',
     'cmpHybridCost', 'cmpBfsCost', 'cmpHybridSuccess', 'cmpBfsSuccess'
    ].forEach(id => setText(id, '—'));
    document.getElementById('comparisonVerdict').classList.remove('visible');

    // Clear waypoints
    waypointMarkers.forEach(m => map.removeLayer(m));
    waypointMarkers = [];
    waypointCoords = [];

    // Reset traffic slider
    trafficSlider.value = 1;
    trafficValue.textContent = '1.0×';

    // Reset mode
    currentMode = null;
    updateModeUI();
    setStatus('Ready', '#22c55e');
    showToast('All cleared', 'info');
}

function clearRoutes() {
    routeLayers.forEach(layer => map.removeLayer(layer));
    routeLayers = [];
    astarLayer = null;
    dfsLayer = null;
    mergedLayer = null;
    bfsLayer = null;
    blockageLayer = null;
}

// ═══════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function showLoading(show) {
    loadingOverlay.classList.toggle('visible', show);
}

function setStatus(text, color) {
    statusText.textContent = text;
    statusDot.style.background = color;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toast-out 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// ═══════════════════════════════════════════════════════════════
// INITIALIZE
// ═══════════════════════════════════════════════════════════════

initMap();

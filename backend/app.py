"""
SmartPath — Flask REST API
--------------------------
Serves the frontend and provides route optimization endpoints.

Endpoints:
    GET  /                → Serve frontend index.html
    GET  /map-bounds      → Get graph bounding box for map init
    POST /get-route       → Compute hybrid A*/DFS route
    POST /compare         → Compare Hybrid A*/DFS vs BFS
    POST /random-blockages→ Generate random blocked nodes
"""

import os
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from utils.graph_loader import load_graph, get_nearest_node, get_graph_bounds, get_node_coords, get_edge_weight
from algorithms.hybrid import hybrid_route, bfs_search

# ─── App Configuration ───
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

# ─── Load Graph on Startup ───
print("[SmartPath] Initializing road network graph...")
G = load_graph()
print("[SmartPath] Ready to serve routes!")


# ─── Frontend Routes ───

@app.route('/')
def serve_frontend():
    """Serve the main frontend page."""
    return send_from_directory(FRONTEND_DIR, 'index.html')


# ─── API Routes ───

@app.route('/map-bounds', methods=['GET'])
def map_bounds():
    """Return the bounding box and center of the loaded graph."""
    try:
        bounds = get_graph_bounds(G)
        return jsonify({'success': True, 'bounds': bounds})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/get-route', methods=['POST'])
def get_route():
    """
    Compute the hybrid A*/DFS route.

    Request JSON:
        {
            "source": {"lat": float, "lng": float},
            "destination": {"lat": float, "lng": float},
            "blocked_nodes": [int, ...],         # optional: OSM node IDs
            "blocked_edges": [[int, int], ...],   # optional: [u, v] pairs
            "blocked_coords": [{"lat": float, "lng": float}, ...]  # optional: GPS coords
        }

    Response JSON:
        {
            "success": bool,
            "astar": { path, path_coords, cost, nodes_expanded, execution_time_ms },
            "dfs": { detour_path, detour_coords, nodes_expanded, execution_time_ms } or null,
            "merged": { path_coords, cost },
            "blockage_detected": bool,
            "blockage_location": { coords } or null,
            "total_time_ms": float
        }
    """
    try:
        data = request.get_json()

        # Parse source and destination
        src = data['source']
        dst = data['destination']
        start_node = get_nearest_node(G, src['lat'], src['lng'])
        goal_node = get_nearest_node(G, dst['lat'], dst['lng'])

        if start_node == goal_node:
            return jsonify({'success': False, 'error': 'Source and destination are the same node'}), 400

        # Parse blocked elements
        blocked_nodes = set(data.get('blocked_nodes', []))
        blocked_edges = set()
        for edge in data.get('blocked_edges', []):
            blocked_edges.add((edge[0], edge[1]))

        # Convert blocked GPS coordinates to nearest node IDs
        for coord in data.get('blocked_coords', []):
            node_id = get_nearest_node(G, coord['lat'], coord['lng'])
            blocked_nodes.add(node_id)

        # Remove start/end from blocked set (user shouldn't block their own endpoints)
        blocked_nodes.discard(start_node)
        blocked_nodes.discard(goal_node)

        # Apply traffic congestion multiplier if provided
        traffic_multiplier = float(data.get('traffic_multiplier', 1.0))
        G_routed = G  # default: use original graph
        if traffic_multiplier > 1.0:
            G_routed = _apply_traffic(G, traffic_multiplier)

        # Run the hybrid algorithm
        result = hybrid_route(G_routed, start_node, goal_node, blocked_nodes, blocked_edges)

        # Add exact source/dest to path to visually connect the drawn route to markers
        if result['astar'] and result['astar'].get('success'):
            result['astar']['path_coords'] = [[src['lat'], src['lng']]] + result['astar']['path_coords'] + [[dst['lat'], dst['lng']]]
        if result['merged'] and result['merged'].get('success'):
            # Only append if we haven't already modified this list (important when merged == astar)
            # Using concatenation creates a new list, avoiding double-insertion issues
            if result['merged']['path_coords'] is not (result['astar']['path_coords'] if result['astar'] else None):
                 result['merged']['path_coords'] = [[src['lat'], src['lng']]] + result['merged']['path_coords'] + [[dst['lat'], dst['lng']]]

        # Build response (convert node IDs to ints for JSON serialization)
        response = {
            'success': True,
            'source_coords': list(get_node_coords(G, start_node)),
            'dest_coords': list(get_node_coords(G, goal_node)),
            'astar': _serialize_astar(result['astar']),
            'dfs': _serialize_dfs(result['dfs']),
            'merged': result['merged'],
            'blockage_detected': result['blockage_detected'],
            'blockage_location': result['blockage_location'],
            'total_time_ms': result['total_time_ms']
        }

        return jsonify(response)

    except KeyError as e:
        return jsonify({'success': False, 'error': f'Missing required field: {e}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/compare', methods=['POST'])
def compare_algorithms():
    """
    Compare Hybrid A*/DFS vs BFS.

    Same input format as /get-route.
    Returns metrics for both algorithms side-by-side.
    """
    try:
        data = request.get_json()
        src = data['source']
        dst = data['destination']
        start_node = get_nearest_node(G, src['lat'], src['lng'])
        goal_node = get_nearest_node(G, dst['lat'], dst['lng'])

        blocked_nodes = set(data.get('blocked_nodes', []))
        blocked_edges = set()
        for edge in data.get('blocked_edges', []):
            blocked_edges.add((edge[0], edge[1]))
        for coord in data.get('blocked_coords', []):
            blocked_nodes.add(get_nearest_node(G, coord['lat'], coord['lng']))
        blocked_nodes.discard(start_node)
        blocked_nodes.discard(goal_node)

        # Apply traffic multiplier
        traffic_multiplier = float(data.get('traffic_multiplier', 1.0))
        G_routed = _apply_traffic(G, traffic_multiplier) if traffic_multiplier > 1.0 else G

        # Run both algorithms
        hybrid_result = hybrid_route(G_routed, start_node, goal_node, blocked_nodes, blocked_edges)
        bfs_result = bfs_search(G_routed, start_node, goal_node, blocked_nodes, blocked_edges)

        if hybrid_result['merged'] and hybrid_result['merged'].get('success'):
            hybrid_result['merged']['path_coords'] = [[src['lat'], src['lng']]] + hybrid_result['merged']['path_coords'] + [[dst['lat'], dst['lng']]]
        if bfs_result.get('success'):
            bfs_result['path_coords'] = [[src['lat'], src['lng']]] + bfs_result['path_coords'] + [[dst['lat'], dst['lng']]]

        response = {
            'success': True,
            'hybrid': {
                'path_coords': hybrid_result['merged']['path_coords'] if hybrid_result['merged'] else [],
                'cost': hybrid_result['merged']['cost'] if hybrid_result['merged'] else None,
                'nodes_expanded': (
                    (hybrid_result['astar']['nodes_expanded'] if hybrid_result['astar'] else 0) +
                    (hybrid_result['dfs']['nodes_expanded'] if hybrid_result['dfs'] else 0)
                ),
                'execution_time_ms': hybrid_result['total_time_ms'],
                'success': hybrid_result['merged']['success'] if hybrid_result['merged'] else False
            },
            'bfs': {
                'path_coords': bfs_result['path_coords'],
                'cost': bfs_result['cost'],
                'nodes_expanded': bfs_result['nodes_expanded'],
                'execution_time_ms': bfs_result['execution_time_ms'],
                'success': bfs_result['success']
            }
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/random-blockages', methods=['POST'])
def random_blockages():
    """Generate random blocked nodes in the graph area."""
    try:
        data = request.get_json() or {}
        count = min(data.get('count', 5), 20)  # cap at 20
        bounds = data.get('bounds')

        nodes = list(G.nodes)
        
        # Filter nodes by current map bounds if provided
        if bounds:
            south, north = bounds.get('south', -90), bounds.get('north', 90)
            west, east = bounds.get('west', -180), bounds.get('east', 180)
            valid_nodes = [
                n for n in nodes 
                if south <= G.nodes[n]['y'] <= north and west <= G.nodes[n]['x'] <= east
            ]
            if len(valid_nodes) > count:
                nodes = valid_nodes

        blocked = random.sample(nodes, min(count, len(nodes)))
        coords = [{'lat': G.nodes[n]['y'], 'lng': G.nodes[n]['x']} for n in blocked]

        return jsonify({'success': True, 'blocked_coords': coords, 'count': len(coords)})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── Helpers ───

def _serialize_astar(astar):
    if astar is None:
        return None
    return {
        'path_coords': astar['path_coords'],
        'cost': astar['cost'],
        'nodes_expanded': astar['nodes_expanded'],
        'execution_time_ms': astar['execution_time_ms'],
        'success': astar['success']
    }


def _serialize_dfs(dfs):
    if dfs is None:
        return None
    return {
        'detour_coords': dfs['detour_coords'],
        'nodes_expanded': dfs['nodes_expanded'],
        'execution_time_ms': dfs['execution_time_ms'],
        'success': dfs['success']
    }


# ─── Entry Point ───

def _apply_traffic(G, multiplier):
    """
    Create a view of the graph with traffic-scaled travel times.
    Applies random scaling to simulate uneven congestion.
    """
    import random
    G_traffic = G.copy()
    for u, v, key, data in G_traffic.edges(keys=True, data=True):
        if 'travel_time' in data:
            # Scale travel time randomly to simulate dynamic traffic
            edge_multiplier = random.uniform(1.0, multiplier)
            data['travel_time'] = float(data['travel_time']) * edge_multiplier
            
    return G_traffic


if __name__ == '__main__':
    # Use PORT environment variable for cloud deployment (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    # Run in debug mode locally, but normal mode in production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

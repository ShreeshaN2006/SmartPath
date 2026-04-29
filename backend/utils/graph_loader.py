"""
Graph Loader Utility
--------------------
Loads a real-world urban road network using OSMnx and caches it locally
as a GraphML file to avoid repeated downloads.

The graph is a NetworkX MultiDiGraph where:
    - Nodes → GPS coordinates (latitude 'y', longitude 'x')
    - Edges → weighted by travel time (minutes) computed from length and speed
"""

import os
import osmnx as ox
import networkx as nx

# Cache file path (stored alongside the backend code)
GRAPH_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'graph_cache.graphml')

# Default center: Bangalore, India — a dense urban area ideal for routing demos
DEFAULT_CENTER = (12.9716, 77.5946)

# Radius in meters around the center point to load the road network
NETWORK_RADIUS = 3000


def load_graph() -> nx.MultiDiGraph:
    """
    Load the road network graph. If a cached GraphML file exists, load from
    disk. Otherwise, download from OpenStreetMap via OSMnx and cache it.

    The graph edges are augmented with a 'travel_time' attribute (in minutes)
    computed as: travel_time = length_meters / (speed_kph * 1000 / 60)

    Returns
    -------
    networkx.MultiDiGraph
        The road network graph with travel_time edge weights.
    """
    if os.path.exists(GRAPH_CACHE_FILE):
        print(f"[GraphLoader] Loading cached graph from {GRAPH_CACHE_FILE}")
        G = ox.load_graphml(GRAPH_CACHE_FILE)
    else:
        print(f"[GraphLoader] Downloading road network from OSM (center={DEFAULT_CENTER}, radius={NETWORK_RADIUS}m)...")
        G = ox.graph_from_point(
            DEFAULT_CENTER,
            dist=NETWORK_RADIUS,
            network_type='drive'
        )
        # Save to cache for future runs
        ox.save_graphml(G, GRAPH_CACHE_FILE)
        print(f"[GraphLoader] Graph cached to {GRAPH_CACHE_FILE}")

    # Add travel_time weights to edges
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    print(f"[GraphLoader] Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def get_nearest_node(G: nx.MultiDiGraph, lat: float, lon: float) -> int:
    """
    Find the nearest graph node to the given GPS coordinates.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        The road network graph.
    lat, lon : float
        Latitude and longitude of the query point.

    Returns
    -------
    int
        The OSM node ID of the nearest node.
    """
    return ox.nearest_nodes(G, lon, lat)


def get_node_coords(G: nx.MultiDiGraph, node_id: int) -> tuple:
    """
    Get the GPS coordinates of a node.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        The road network graph.
    node_id : int
        The node ID to look up.

    Returns
    -------
    tuple
        (latitude, longitude) of the node.
    """
    return (G.nodes[node_id]['y'], G.nodes[node_id]['x'])


def get_graph_bounds(G: nx.MultiDiGraph) -> dict:
    """
    Get the bounding box of the graph for map initialization.

    Returns
    -------
    dict
        {'north': float, 'south': float, 'east': float, 'west': float,
         'center_lat': float, 'center_lon': float}
    """
    lats = [G.nodes[n]['y'] for n in G.nodes]
    lons = [G.nodes[n]['x'] for n in G.nodes]
    return {
        'north': max(lats),
        'south': min(lats),
        'east': max(lons),
        'west': min(lons),
        'center_lat': sum(lats) / len(lats),
        'center_lon': sum(lons) / len(lons)
    }


def get_edge_weight(G: nx.MultiDiGraph, u: int, v: int) -> float:
    """
    Get the travel time (in minutes) for traversing an edge.
    Falls back to length-based estimation if travel_time is missing.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        The road network graph.
    u, v : int
        Source and target node IDs.

    Returns
    -------
    float
        Travel time in minutes.
    """
    # MultiDiGraph can have multiple edges between two nodes; pick the shortest
    edge_data = G.get_edge_data(u, v)
    if edge_data is None:
        return float('inf')

    min_time = float('inf')
    for key in edge_data:
        data = edge_data[key]
        # travel_time is in seconds, convert to minutes
        if 'travel_time' in data:
            t = float(data['travel_time']) / 60.0
        elif 'length' in data:
            # Estimate: assume 30 kph average speed
            t = (float(data['length']) / 1000.0) / 30.0 * 60.0
        else:
            t = 1.0  # fallback: 1 minute
        min_time = min(min_time, t)

    return min_time

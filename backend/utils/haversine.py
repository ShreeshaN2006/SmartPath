"""
Haversine Distance Formula
--------------------------
Computes the great-circle distance between two points on the Earth's surface,
given their latitudes and longitudes in decimal degrees.

Formula:
    h(n) = 2R * arcsin( sqrt(
        sin²((lat2 - lat1) / 2) +
        cos(lat1) * cos(lat2) * sin²((lon2 - lon1) / 2)
    ))

    R = 6371 km (mean radius of the Earth)

Used as the admissible heuristic h(n) in the A* search algorithm.
"""

import math

# Mean radius of the Earth in kilometers
EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance in kilometers between two points
    on the Earth specified by their latitude and longitude in decimal degrees.

    Parameters
    ----------
    lat1, lon1 : float
        Latitude and longitude of point 1 (in decimal degrees).
    lat2, lon2 : float
        Latitude and longitude of point 2 (in decimal degrees).

    Returns
    -------
    float
        Distance between the two points in kilometers.
    """
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(dlon / 2.0) ** 2)

    c = 2.0 * math.asin(math.sqrt(a))

    distance = EARTH_RADIUS_KM * c
    return distance


def haversine_heuristic(G, node, goal) -> float:
    """
    Wrapper that extracts GPS coordinates from a NetworkX graph and computes
    the Haversine distance. Used as h(n) in A* search.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        The road network graph (nodes must have 'y' and 'x' attributes).
    node : int
        The current node ID.
    goal : int
        The goal node ID.

    Returns
    -------
    float
        Estimated distance in km from node to goal (admissible heuristic).
    """
    lat1, lon1 = G.nodes[node]['y'], G.nodes[node]['x']
    lat2, lon2 = G.nodes[goal]['y'], G.nodes[goal]['x']
    return haversine(lat1, lon1, lat2, lon2)

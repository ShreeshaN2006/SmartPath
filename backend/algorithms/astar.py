"""
A* Search Algorithm
-------------------
Custom implementation of A* search on a NetworkX road network graph.

Uses a priority queue (heapq) with evaluation function:
    f(n) = g(n) + h(n)

Where:
    g(n) = actual cost from start to current node (travel time in minutes)
    h(n) = Haversine distance heuristic (admissible — never overestimates)

The implementation tracks performance metrics:
    - nodes_expanded: total nodes popped from the priority queue
    - execution_time: wall-clock time in milliseconds
    - path_cost: total travel time of the found path in minutes
"""

import heapq
import time

from utils.haversine import haversine_heuristic
from utils.graph_loader import get_edge_weight


def astar_search(graph, start_node, goal_node, blocked_nodes=None, blocked_edges=None):
    """
    Perform A* search from start_node to goal_node on graph.

    Parameters
    ----------
    graph : networkx.MultiDiGraph
        The road network graph.
    start_node : int
        OSM node ID of the source.
    goal_node : int
        OSM node ID of the destination.
    blocked_nodes : set or None
        Set of node IDs that are blocked (cannot be traversed).
    blocked_edges : set or None
        Set of (u, v) tuples representing blocked edges.

    Returns
    -------
    dict
        {
            'path': list of node IDs (empty if no path found),
            'path_coords': list of [lat, lon] pairs,
            'cost': float (total travel time in minutes),
            'nodes_expanded': int,
            'execution_time_ms': float,
            'success': bool
        }
    """
    if blocked_nodes is None:
        blocked_nodes = set()
    if blocked_edges is None:
        blocked_edges = set()

    start_time = time.perf_counter()

    # Check if start or goal is blocked
    if start_node in blocked_nodes or goal_node in blocked_nodes:
        return _failure_result(time.perf_counter() - start_time)

    def process_neighbors(current_node):
        nonlocal counter
        for neighbor in graph.neighbors(current_node):
            if neighbor in blocked_nodes or (current_node, neighbor) in blocked_edges:
                continue

            edge_cost = get_edge_weight(graph, current_node, neighbor)
            tentative_g = g_score[current_node] + edge_cost

            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current_node
                g_score[neighbor] = tentative_g
                h_score = haversine_heuristic(graph, neighbor, goal_node)
                counter += 1
                heapq.heappush(open_set, (tentative_g + h_score, counter, neighbor))

    # Priority queue: (f_score, tie_breaker, node_id)
    # tie_breaker ensures FIFO ordering when f_scores are equal
    counter = 0
    open_set = []
    heapq.heappush(open_set, (0.0, counter, start_node))

    # g_score[node] = cost of cheapest path from start to node
    g_score = {start_node: 0.0}

    # came_from[node] = previous node in optimal path
    came_from = {}

    # Track which nodes have been fully explored
    closed_set = set()

    # Performance metric
    nodes_expanded = 0

    while open_set:
        # Pop node with lowest f_score
        _, _, current = heapq.heappop(open_set)

        # Skip if already explored (duplicate entry in heap)
        if current in closed_set:
            continue

        nodes_expanded += 1
        closed_set.add(current)

        # Goal reached — reconstruct path
        if current == goal_node:
            path = _reconstruct_path(came_from, current)
            path_coords = [[graph.nodes[n]['y'], graph.nodes[n]['x']] for n in path]
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return {
                'path': path,
                'path_coords': path_coords,
                'cost': g_score[goal_node],
                'nodes_expanded': nodes_expanded,
                'execution_time_ms': round(elapsed_ms, 2),
                'success': True
            }

        # Expand neighbors
        process_neighbors(current)

    # No path found
    return _failure_result(time.perf_counter() - start_time, nodes_expanded)


def _reconstruct_path(came_from, current):
    """
    Trace back from goal to start using the came_from dictionary.
    Returns the path as a list of node IDs from start to goal.
    """
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def _failure_result(elapsed_seconds, nodes_expanded=0):
    """Return a standardized failure result."""
    return {
        'path': [],
        'path_coords': [],
        'cost': -1,
        'nodes_expanded': nodes_expanded,
        'execution_time_ms': round(elapsed_seconds * 1000.0, 2),
        'success': False
    }



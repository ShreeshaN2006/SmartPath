"""
DFS Recovery Algorithm
----------------------
When the A* optimal path hits a blocked node or edge, DFS performs a local
exploration from the blocked point to find an alternate route that reconnects
with the original A* path downstream of the blockage.

Strategy:
    1. Start from the node just before the blockage
    2. Explore neighbors depth-first, avoiding blocked nodes/edges
    3. Try to reach any node on the original A* path that is past the blockage
    4. Return the detour path that reconnects with the main route

The max_depth parameter limits how far DFS will explore to prevent infinite
loops in dense urban networks.
"""

import time
from utils.haversine import haversine_heuristic


def dfs_recovery(G, blocked_index, original_path, blocked_nodes, blocked_edges, max_depth=150):
    """
    DFS-based local recovery around a blockage in the A* path.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        The road network graph.
    blocked_index : int
        Index in original_path where the blockage was detected.
        The DFS starts from original_path[blocked_index - 1] (the node before blockage).
    original_path : list
        The original A* path (list of node IDs).
    blocked_nodes : set
        Set of blocked node IDs.
    blocked_edges : set
        Set of blocked (u, v) edge tuples.
    max_depth : int
        Maximum DFS exploration depth (default: 50).

    Returns
    -------
    dict
        {
            'detour_path': list of node IDs for the detour,
            'detour_coords': list of [lat, lon] pairs,
            'rejoin_index': int (index in original_path where detour reconnects),
            'nodes_expanded': int,
            'execution_time_ms': float,
            'success': bool
        }
    """
    start_time = time.perf_counter()

    # Validate inputs
    if blocked_index < 1 or blocked_index >= len(original_path):
        return _dfs_failure(time.perf_counter() - start_time)

    # Start DFS from the node just before the blockage
    dfs_start = original_path[blocked_index - 1]

    # Target: any node on the original path that is PAST the blockage
    # and not itself blocked
    rejoin_candidates = set()
    for i in range(blocked_index + 1, len(original_path)):
        node = original_path[i]
        if node not in blocked_nodes:
            rejoin_candidates.add(node)

    if not rejoin_candidates:
        return _dfs_failure(time.perf_counter() - start_time)

    # DFS with iterative stack (avoids Python recursion limits)
    # Stack entries: (current_node, path_so_far)
    stack = [(dfs_start, [dfs_start])]
    visited = {}
    nodes_expanded = 0

    while stack:
        current, path = stack.pop()
        depth = len(path)

        if current in visited and visited[current] <= depth:
            continue

        visited[current] = depth
        nodes_expanded += 1

        # Check if we've reached a rejoin point
        if current in rejoin_candidates and current != dfs_start:
            # Find where in the original path this node is
            rejoin_index = original_path.index(current)
            detour_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in path]
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return {
                'detour_path': path,
                'detour_coords': detour_coords,
                'rejoin_index': rejoin_index,
                'nodes_expanded': nodes_expanded,
                'execution_time_ms': round(elapsed_ms, 2),
                'success': True
            }

        # Depth limit check
        if len(path) >= max_depth:
            continue

        # Explore neighbors (depth-first via stack — LIFO)
        goal_node = original_path[-1]
        neighbors = list(G.neighbors(current))
        
        # Sort DESCENDING by distance to goal so best neighbors are pushed last (LIFO = popped first)
        neighbors.sort(key=lambda n: haversine_heuristic(G, n, goal_node), reverse=True)

        for neighbor in neighbors:
            if neighbor in blocked_nodes:
                continue
            if (current, neighbor) in blocked_edges:
                continue

            stack.append((neighbor, path + [neighbor]))

    # No recovery path found
    return _dfs_failure(time.perf_counter() - start_time, nodes_expanded)


def _dfs_failure(elapsed_seconds, nodes_expanded=0):
    """Return a standardized DFS failure result."""
    return {
        'detour_path': [],
        'detour_coords': [],
        'rejoin_index': -1,
        'nodes_expanded': nodes_expanded,
        'execution_time_ms': round(elapsed_seconds * 1000.0, 2),
        'success': False
    }

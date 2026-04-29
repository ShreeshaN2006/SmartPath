"""
Hybrid A*/DFS Orchestrator & BFS Comparison
"""

import time
from collections import deque
from algorithms.astar import astar_search
from algorithms.dfs import dfs_recovery
from utils.graph_loader import get_edge_weight


def hybrid_route(G, start_node, goal_node, blocked_nodes, blocked_edges):
    """
    Hybrid A*/DFS route computation.
    1. Run A* for optimal path
    2. Detect blockage on the path
    3. Trigger DFS recovery if needed
    4. Merge paths into final route
    """
    total_start = time.perf_counter()
    result = {
        'astar': None, 'dfs': None, 'merged': None,
        'blockage_detected': False, 'blockage_location': None, 'total_time_ms': 0
    }

    # Step 1: Run A* (no blockage awareness to get ideal path)
    astar_result = astar_search(G, start_node, goal_node)
    if not astar_result['success']:
        astar_result = astar_search(G, start_node, goal_node, blocked_nodes, blocked_edges)
        result['astar'] = astar_result
        if astar_result['success']:
            result['merged'] = {
                'path': astar_result['path'], 'path_coords': astar_result['path_coords'],
                'cost': astar_result['cost'], 'success': True
            }
        else:
            result['merged'] = {
                'path': [], 'path_coords': [], 'cost': -1, 'success': False
            }
        result['total_time_ms'] = round((time.perf_counter() - total_start) * 1000, 2)
        return result

    result['astar'] = astar_result
    astar_path = astar_result['path']

    # Step 2: Detect blockage
    blocked_index = None
    for i, node in enumerate(astar_path):
        if node in blocked_nodes:
            blocked_index = i
            break
    if blocked_index is None:
        for i in range(len(astar_path) - 1):
            if (astar_path[i], astar_path[i + 1]) in blocked_edges:
                blocked_index = i + 1
                break

    # No blockage — return A* as final
    if blocked_index is None:
        result['merged'] = {
            'path': astar_path, 'path_coords': astar_result['path_coords'],
            'cost': astar_result['cost'], 'success': True
        }
        result['total_time_ms'] = round((time.perf_counter() - total_start) * 1000, 2)
        return result

    # Step 3: Blockage detected → DFS Recovery
    result['blockage_detected'] = True
    bnode = astar_path[blocked_index]
    result['blockage_location'] = {
        'node_id': int(bnode), 'index': blocked_index,
        'coords': [G.nodes[bnode]['y'], G.nodes[bnode]['x']]
    }

    dfs_result = dfs_recovery(G, blocked_index, astar_path, blocked_nodes, blocked_edges, max_depth=50)
    result['dfs'] = dfs_result

    # Step 4: Merge paths
    if dfs_result['success']:
        pre = astar_path[:blocked_index]
        detour = dfs_result['detour_path']
        post = astar_path[dfs_result['rejoin_index']:]

        merged = list(pre)
        if detour:
            merged = merged + (detour[1:] if merged and merged[-1] == detour[0] else detour)
        if post:
            merged = merged + (post[1:] if merged and merged[-1] == post[0] else post)

        cost = sum(get_edge_weight(G, merged[i], merged[i+1]) for i in range(len(merged)-1))
        coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in merged]
        result['merged'] = {'path': merged, 'path_coords': coords, 'cost': round(cost, 4), 'success': True}
    else:
        fb = astar_search(G, start_node, goal_node, blocked_nodes, blocked_edges)
        result['merged'] = {
            'path': fb['path'], 'path_coords': fb['path_coords'],
            'cost': fb['cost'], 'success': fb['success']
        }

    result['total_time_ms'] = round((time.perf_counter() - total_start) * 1000, 2)
    return result


def bfs_search(G, start_node, goal_node, blocked_nodes=None, blocked_edges=None):
    """BFS for the comparison module. No heuristic — explores uniformly."""
    if blocked_nodes is None:
        blocked_nodes = set()
    if blocked_edges is None:
        blocked_edges = set()

    start_time = time.perf_counter()
    if start_node in blocked_nodes or goal_node in blocked_nodes:
        return _bfs_fail(time.perf_counter() - start_time)

    queue = deque([(start_node, [start_node])])
    visited = {start_node}
    nodes_expanded = 0

    while queue:
        current, path = queue.popleft()
        nodes_expanded += 1
        if current == goal_node:
            cost = sum(get_edge_weight(G, path[i], path[i+1]) for i in range(len(path)-1))
            coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in path]
            ms = (time.perf_counter() - start_time) * 1000.0
            return {
                'path': path, 'path_coords': coords, 'cost': round(cost, 4),
                'nodes_expanded': nodes_expanded, 'execution_time_ms': round(ms, 2), 'success': True
            }
        for nb in G.neighbors(current):
            if nb in visited or nb in blocked_nodes or (current, nb) in blocked_edges:
                continue
            visited.add(nb)
            queue.append((nb, path + [nb]))

    return _bfs_fail(time.perf_counter() - start_time, nodes_expanded)


def _bfs_fail(elapsed, expanded=0):
    return {
        'path': [], 'path_coords': [], 'cost': -1,
        'nodes_expanded': expanded, 'execution_time_ms': round(elapsed * 1000, 2), 'success': False
    }

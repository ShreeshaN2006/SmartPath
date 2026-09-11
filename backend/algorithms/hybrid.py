import time
from collections import deque

import networkx as nx

from algorithms.base import RoutingContext


def get_edge_weight(graph: nx.MultiDiGraph, u: int, v: int) -> float:
    edge_data = graph.get_edge_data(u, v)
    if edge_data is None:
        return float('inf')
    min_time = float('inf')
    for key in edge_data:
        data = edge_data[key]
        if 'travel_time' in data:
            t = float(data['travel_time']) / 60.0
        elif 'length' in data:
            t = (float(data['length']) / 1000.0) / 30.0 * 60.0
        else:
            t = 1.0
        min_time = min(min_time, t)
    return min_time


def bfs_search(graph: nx.MultiDiGraph, start_node: int, goal_node: int,
               blocked_nodes: set[int] | None = None,
               blocked_edges: set[tuple[int, int]] | None = None) -> dict:
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
            cost = sum(get_edge_weight(graph, path[i], path[i+1]) for i in range(len(path)-1))
            coords = [[graph.nodes[n]['y'], graph.nodes[n]['x']] for n in path]
            ms = (time.perf_counter() - start_time) * 1000.0
            return {
                'path': path, 'path_coords': coords, 'cost': round(cost, 4),
                'nodes_expanded': nodes_expanded, 'execution_time_ms': round(ms, 2), 'success': True
            }
        for nb in graph.neighbors(current):
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


def hybrid_route(graph: nx.MultiDiGraph, start_node: int, goal_node: int,
                 blocked_nodes: set[int], blocked_edges: set[tuple[int, int]],
                 context: RoutingContext | None = None) -> dict:
    total_start = time.perf_counter()
    result = {
        'astar': None, 'dfs': None, 'merged': None,
        'blockage_detected': False, 'blockage_location': None, 'total_time_ms': 0
    }

    from algorithms.astar import AStarAlgorithm
    from algorithms.dfs import dfs_recovery
    astar = AStarAlgorithm()

    astar_result = astar.route(graph, start_node, goal_node, context or RoutingContext())
    if not astar_result.success:
        astar_result = astar.route(graph, start_node, goal_node, context or RoutingContext(
            blocked_nodes=blocked_nodes, blocked_edges=blocked_edges
        ))
        result['astar'] = _serialize_astar(astar_result)
        if astar_result.success:
            result['merged'] = {
                'path': astar_result.path, 'path_coords': astar_result.path_coords,
                'cost': astar_result.cost, 'success': True
            }
        else:
            result['merged'] = {'path': [], 'path_coords': [], 'cost': -1, 'success': False}
        result['total_time_ms'] = round((time.perf_counter() - total_start) * 1000, 2)
        return result

    result['astar'] = _serialize_astar(astar_result)
    astar_path = astar_result.path

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

    if blocked_index is None:
        result['merged'] = {
            'path': astar_path, 'path_coords': astar_result.path_coords,
            'cost': astar_result.cost, 'success': True
        }
        result['total_time_ms'] = round((time.perf_counter() - total_start) * 1000, 2)
        return result

    result['blockage_detected'] = True
    bnode = astar_path[blocked_index]
    result['blockage_location'] = {
        'node_id': int(bnode), 'index': blocked_index,
        'coords': [graph.nodes[bnode]['y'], graph.nodes[bnode]['x']]
    }

    dfs_result = dfs_recovery(graph, blocked_index, astar_path, blocked_nodes, blocked_edges, max_depth=50)
    result['dfs'] = _serialize_dfs(dfs_result)

    if dfs_result['success']:
        pre = astar_path[:blocked_index]
        detour = dfs_result['detour_path']
        post = astar_path[dfs_result['rejoin_index']:]

        merged = list(pre)
        if detour:
            merged = merged + (detour[1:] if merged and merged[-1] == detour[0] else detour)
        if post:
            merged = merged + (post[1:] if merged and merged[-1] == post[0] else post)

        cost = sum(get_edge_weight(graph, merged[i], merged[i+1]) for i in range(len(merged)-1))
        coords = [[graph.nodes[n]['y'], graph.nodes[n]['x']] for n in merged]
        result['merged'] = {'path': merged, 'path_coords': coords, 'cost': round(cost, 4), 'success': True}
    else:
        fb = astar.route(graph, start_node, goal_node, context or RoutingContext(
            blocked_nodes=blocked_nodes, blocked_edges=blocked_edges
        ))
        result['merged'] = {
            'path': fb.path, 'path_coords': fb.path_coords,
            'cost': fb.cost, 'success': fb.success
        }

    result['total_time_ms'] = round((time.perf_counter() - total_start) * 1000, 2)
    return result


def _serialize_astar(astar):
    if astar is None or not astar.success:
        return None
    return {
        'path_coords': astar.path_coords,
        'cost': astar.cost,
        'nodes_expanded': astar.nodes_expanded,
        'execution_time_ms': astar.execution_time_ms,
        'success': True
    }


def _serialize_dfs(dfs):
    if dfs is None or not dfs['success']:
        return None
    return {
        'detour_coords': dfs['detour_coords'],
        'nodes_expanded': dfs['nodes_expanded'],
        'execution_time_ms': dfs['execution_time_ms'],
        'success': True
    }

import math
import time

import networkx as nx

from algorithms.base import RoutingContext


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def haversine_heuristic(graph: nx.MultiDiGraph, node: int, goal: int) -> float:
    lat1, lon1 = graph.nodes[node]['y'], graph.nodes[node]['x']
    lat2, lon2 = graph.nodes[goal]['y'], graph.nodes[goal]['x']
    return haversine(lat1, lon1, lat2, lon2)


def dfs_recovery(
    graph: nx.MultiDiGraph,
    blocked_index: int,
    original_path: list[int],
    blocked_nodes: set[int],
    blocked_edges: set[tuple[int, int]],
    max_depth: int = 150,
    context: RoutingContext | None = None,
) -> dict:
    start_time = time.perf_counter()

    if blocked_index < 1 or blocked_index >= len(original_path):
        return _dfs_failure(time.perf_counter() - start_time)

    dfs_start = original_path[blocked_index - 1]
    goal_node = original_path[-1]

    rejoin_candidates = set()
    for i in range(blocked_index + 1, len(original_path)):
        node = original_path[i]
        if node not in blocked_nodes:
            rejoin_candidates.add(node)

    if not rejoin_candidates:
        return _dfs_failure(time.perf_counter() - start_time)

    stack = [(dfs_start, [dfs_start])]
    visited: dict[int, int] = {}
    nodes_expanded = 0

    while stack:
        current, path = stack.pop()
        depth = len(path)

        if current in visited and visited[current] <= depth:
            continue

        visited[current] = depth
        nodes_expanded += 1

        if current in rejoin_candidates and current != dfs_start:
            rejoin_index = original_path.index(current)
            detour_coords = [[graph.nodes[n]['y'], graph.nodes[n]['x']] for n in path]
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return {
                'detour_path': path,
                'detour_coords': detour_coords,
                'rejoin_index': rejoin_index,
                'nodes_expanded': nodes_expanded,
                'execution_time_ms': round(elapsed_ms, 2),
                'success': True
            }

        if len(path) >= max_depth:
            continue

        neighbors = list(graph.neighbors(current))
        neighbors.sort(key=lambda n: haversine_heuristic(graph, n, goal_node), reverse=True)

        for neighbor in neighbors:
            if neighbor in blocked_nodes:
                continue
            if (current, neighbor) in blocked_edges:
                continue

            if context and context.is_blocked(current, neighbor, context):
                continue

            stack.append((neighbor, path + [neighbor]))

    return _dfs_failure(time.perf_counter() - start_time, nodes_expanded)


def _dfs_failure(elapsed_seconds, nodes_expanded=0):
    return {
        'detour_path': [],
        'detour_coords': [],
        'rejoin_index': -1,
        'nodes_expanded': nodes_expanded,
        'execution_time_ms': round(elapsed_seconds * 1000.0, 2),
        'success': False
    }

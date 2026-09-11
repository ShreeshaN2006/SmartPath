import heapq
import math
import time

import networkx as nx

from algorithms.base import RouteResult, RoutingAlgorithm, RoutingAlgorithmBase, RoutingContext


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


class AStarAlgorithm(RoutingAlgorithmBase, RoutingAlgorithm):
    def get_edge_cost(self, graph: nx.MultiDiGraph, u: int, v: int, context: RoutingContext) -> float:
        if context.edge_costs and (u, v) in context.edge_costs:
            return context.edge_costs[(u, v)]
        return get_edge_weight(graph, u, v)

    def route(
        self,
        graph: nx.MultiDiGraph,
        source: int,
        target: int,
        context: RoutingContext,
    ) -> RouteResult:
        start_time = time.perf_counter()

        if source in context.blocked_nodes or target in context.blocked_nodes:
            return RouteResult([], [], -1, 0, (time.perf_counter() - start_time) * 1000, False)

        counter = 0
        open_set = [(0.0, counter, source)]
        g_score: dict[int, float] = {source: 0.0}
        came_from: dict[int, int] = {}
        closed_set: set[int] = set()
        nodes_expanded = 0

        while open_set:
            _, _, current = heapq.heappop(open_set)

            if current in closed_set:
                continue

            nodes_expanded += 1
            closed_set.add(current)

            if current == target:
                path = self._reconstruct_path(came_from, current)
                path_coords = [[graph.nodes[n]['y'], graph.nodes[n]['x']] for n in path]
                cost = g_score[target]
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return RouteResult(path, path_coords, cost, nodes_expanded, elapsed_ms, True)

            for neighbor in graph.neighbors(current):
                if self.is_blocked(current, neighbor, context) or (current, neighbor) in context.blocked_edges:
                    continue

                edge_cost = self.get_edge_cost(graph, current, neighbor, context)
                tentative_g = g_score[current] + edge_cost

                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h_score = haversine_heuristic(graph, neighbor, target)
                    counter += 1
                    heapq.heappush(open_set, (tentative_g + h_score, counter, neighbor))

        return RouteResult([], [], -1, nodes_expanded, (time.perf_counter() - start_time) * 1000, False)

    def _reconstruct_path(self, came_from: dict[int, int], current: int) -> list[int]:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

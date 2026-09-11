import heapq
import math
import time

import networkx as nx

from algorithms.base import RouteResult, RoutingAlgorithm, RoutingContext


class DStarLite(RoutingAlgorithm):
    def __init__(self):
        self.km = 0.0
        self.g = {}
        self.rhs = {}
        self.U = []
        self.start = None
        self.goal = None
        self.graph = None

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

        self.graph = graph
        self.start = source
        self.goal = target
        self.km = 0.0
        self.g = {node: float('inf') for node in graph.nodes}
        self.rhs = {node: float('inf') for node in graph.nodes}
        self.rhs[target] = 0.0
        self.U = []

        self._push(target, self._calculate_key(target))

        nodes_expanded = 0
        max_iterations = 10000

        while self.U and nodes_expanded < max_iterations:
            if not (self._top_key() < self._calculate_key(self.start) or self.rhs[self.start] > self.g[self.start]):
                break

            k_old = self._top_key()
            u = self._pop()
            nodes_expanded += 1

            if k_old < self._calculate_key(u):
                self._push(u, self._calculate_key(u))
                continue
            elif self.g[u] > self.rhs[u]:
                self.g[u] = self.rhs[u]
                for s in graph.predecessors(u):
                    if s != self.goal:
                        self._update_vertex(s)
                    self._push(s, self._calculate_key(s))
            else:
                g_old = self.g[u]
                self.g[u] = float('inf')
                for s in list(graph.predecessors(u)) + [u]:
                    if s != self.goal:
                        self._update_vertex(s)
                    self._push(s, self._calculate_key(s))

        if self.g[self.start] == float('inf'):
            return RouteResult([], [], -1, nodes_expanded, (time.perf_counter() - start_time) * 1000, False)

        path = self._reconstruct_path()
        path_coords = [[graph.nodes[n]['y'], graph.nodes[n]['x']] for n in path]
        cost = self.g[self.start]
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return RouteResult(path, path_coords, cost, nodes_expanded, elapsed_ms, True)

    def _calculate_key(self, node: int) -> tuple[float, float]:
        h = self._heuristic(node)
        g_val = min(self.g.get(node, float('inf')), self.rhs.get(node, float('inf')))
        return (g_val + h + self.km, g_val)

    def _heuristic(self, node: int) -> float:
        lat1, lon1 = self.graph.nodes[node]['y'], self.graph.nodes[node]['x']
        lat2, lon2 = self.graph.nodes[self.goal]['y'], self.graph.nodes[self.goal]['x']
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        return R * math.asin(math.sqrt(a))

    def _update_vertex(self, u: int):
        if u != self.goal:
            min_rhs = float('inf')
            for s in self.graph.successors(u):
                cost = self._get_edge_cost(u, s)
                if cost < float('inf'):
                    min_rhs = min(min_rhs, cost + self.g.get(s, float('inf')))
            self.rhs[u] = min_rhs

    def _get_edge_cost(self, u: int, v: int) -> float:
        edge_data = self.graph.get_edge_data(u, v)
        if not edge_data:
            return float('inf')
        min_cost = float('inf')
        for key in edge_data:
            data = edge_data[key]
            if 'travel_time' in data:
                cost = float(data['travel_time']) / 60.0
            elif 'length' in data:
                cost = (float(data['length']) / 1000.0) / 30.0 * 60.0
            else:
                cost = 1.0
            min_cost = min(min_cost, cost)
        return min_cost

    def _push(self, node: int, key: tuple[float, float]):
        heapq.heappush(self.U, (key, node))

    def _pop(self) -> int:
        return heapq.heappop(self.U)[1]

    def _top_key(self) -> tuple[float, float]:
        return self.U[0][0] if self.U else (float('inf'), float('inf'))

    def _reconstruct_path(self) -> list[int]:
        path = [self.start]
        current = self.start
        visited = set()

        while current != self.goal and current not in visited:
            visited.add(current)
            min_cost = float('inf')
            next_node = None
            for s in self.graph.successors(current):
                cost = self._get_edge_cost(current, s)
                if cost < float('inf'):
                    total = cost + self.g.get(s, float('inf'))
                    if total < min_cost:
                        min_cost = total
                        next_node = s
            if next_node is None or next_node in path:
                break
            path.append(next_node)
            current = next_node
        return path

    def update_edge_cost(self, u: int, v: int, new_cost: float):
        if self.graph is None:
            return
        if self.g.get(v, float('inf')) < float('inf'):
            self._update_vertex(u)
            self._push(u, self._calculate_key(u))

    def replan(self, changed_edges: list[tuple[int, int, float]]) -> RouteResult:
        start_time = time.perf_counter()

        for u, v, new_cost in changed_edges:
            self.update_edge_cost(u, v, new_cost)

        nodes_expanded = 0
        max_iterations = 10000

        while self.U and nodes_expanded < max_iterations:
            if not (self._top_key() < self._calculate_key(self.start) or self.rhs[self.start] > self.g[self.start]):
                break

            k_old = self._top_key()
            u = self._pop()
            nodes_expanded += 1

            if k_old < self._calculate_key(u):
                self._push(u, self._calculate_key(u))
                continue
            elif self.g[u] > self.rhs[u]:
                self.g[u] = self.rhs[u]
                for s in self.graph.predecessors(u):
                    if s != self.goal:
                        self._update_vertex(s)
                    self._push(s, self._calculate_key(s))
            else:
                g_old = self.g[u]
                self.g[u] = float('inf')
                for s in list(self.graph.predecessors(u)) + [u]:
                    if s != self.goal:
                        self._update_vertex(s)
                    self._push(s, self._calculate_key(s))

        if self.g[self.start] == float('inf'):
            return RouteResult([], [], -1, nodes_expanded, (time.perf_counter() - start_time) * 1000, False)

        path = self._reconstruct_path()
        path_coords = [[self.graph.nodes[n]['y'], self.graph.nodes[n]['x']] for n in path]
        cost = self.g[self.start]
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return RouteResult(path, path_coords, cost, nodes_expanded, elapsed_ms, True)

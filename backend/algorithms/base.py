from abc import abstractmethod
from typing import Protocol

import networkx as nx


class RouteResult:
    def __init__(
        self,
        path: list[int],
        path_coords: list[tuple[float, float]],
        cost: float,
        nodes_expanded: int,
        execution_time_ms: float,
        success: bool,
    ):
        self.path = path
        self.path_coords = path_coords
        self.cost = cost
        self.nodes_expanded = nodes_expanded
        self.execution_time_ms = execution_time_ms
        self.success = success


class RoutingContext:
    def __init__(
        self,
        traffic_multiplier: float = 1.0,
        blocked_nodes: set | None = None,
        blocked_edges: set | None = None,
        vehicle_type: str = "delivery_van",
        routing_mode: str = "balanced",
        edge_costs: dict[tuple[int, int], float] | None = None,
    ):
        self.traffic_multiplier = traffic_multiplier
        self.blocked_nodes = blocked_nodes or set()
        self.blocked_edges = blocked_edges or set()
        self.vehicle_type = vehicle_type
        self.routing_mode = routing_mode
        self.edge_costs = edge_costs or {}


class RoutingAlgorithm(Protocol):
    @abstractmethod
    def route(
        self,
        graph: nx.MultiDiGraph,
        source: int,
        target: int,
        context: RoutingContext,
    ) -> RouteResult:
        ...


class RoutingAlgorithmBase:
    def get_edge_cost(self, graph: nx.MultiDiGraph, u: int, v: int, context: RoutingContext) -> float:
        if context.edge_costs and (u, v) in context.edge_costs:
            return context.edge_costs[(u, v)]
        return 1.0

    def is_blocked(self, u: int, v: int, context: RoutingContext) -> bool:
        return u in context.blocked_nodes or v in context.blocked_nodes or (u, v) in context.blocked_edges

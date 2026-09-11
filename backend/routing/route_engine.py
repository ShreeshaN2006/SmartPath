import uuid
from typing import Any

from algorithms.astar import AStarAlgorithm
from models.schemas import Coordinates, DataQuality, RouteRequest, RouteResponse, RouteSegment
from risk.risk_engine import compute_edge_cost
from utils.graph_loader import get_nearest_node, load_graph


class RouteEngine:
    def __init__(self):
        self.graph = load_graph()
        self.astar = AStarAlgorithm()

    def _build_context(self, request: RouteRequest) -> dict[str, Any]:
        from providers.incidents.simulation import get_incident_provider
        from providers.traffic.simulation import get_traffic_provider
        from providers.weather.open_meteo import get_weather_provider

        weather_provider = get_weather_provider()
        traffic_provider = get_traffic_provider()
        incident_provider = get_incident_provider()

        weather = weather_provider.get_weather(request.origin.lat, request.origin.lng)
        traffic = traffic_provider.get_traffic()
        incidents = incident_provider.get_incidents()

        edge_costs = {}
        for u, v in self.graph.edges():
            cost = compute_edge_cost(self.graph, u, v, {
                "mode": request.mode,
                "vehicle": request.vehicle,
                "weather": weather.model_dump(),
                "incidents": [i.model_dump() for i in incidents],
            })
            edge_costs[(u, v)] = cost

        return {
            "mode": request.mode,
            "vehicle": request.vehicle,
            "weather": weather.model_dump(),
            "incidents": [i.model_dump() for i in incidents],
            "traffic": [t.model_dump() for t in traffic],
            "edge_costs": edge_costs,
        }

    def _route_segment(
        self,
        source: Coordinates,
        destination: Coordinates,
        context: dict,
        request: RouteRequest,
    ) -> RouteResponse:
        start_node = get_nearest_node(self.graph, source.lat, source.lng)
        goal_node = get_nearest_node(self.graph, destination.lat, destination.lng)

        astar_result = self.astar.route(self.graph, start_node, goal_node, context)

        segments = []
        if astar_result.success and astar_result.path:
            for i in range(len(astar_result.path) - 1):
                u = astar_result.path[i]
                v = astar_result.path[i + 1]
                edge_data = self.graph.get_edge_data(u, v)
                if edge_data:
                    for key in edge_data:
                        data = edge_data[key]
                        length = data.get('length', 0)
                        travel_time = data.get('travel_time', length / 30000 * 60) / 60.0
                        highway = data.get('highway', 'residential')

                        congestion = data.get('congestion', 0.3)
                        risk = 0.2

                        segments.append(RouteSegment(
                            edge_id=f"{u}_{v}",
                            coords=[[self.graph.nodes[u]['y'], self.graph.nodes[u]['x']],
                                   [self.graph.nodes[v]['y'], self.graph.nodes[v]['x']]],
                            distance_m=length,
                            travel_time_min=travel_time,
                            congestion=congestion,
                            risk=risk,
                            road_class=highway,
                        ))

        total_distance = sum(s.distance_m for s in segments) / 1000.0
        total_eta = sum(s.travel_time_min for s in segments)
        avg_risk = sum(s.risk for s in segments) / len(segments) if segments else 0.2

        return RouteResponse(
            route_id=f"route_{uuid.uuid4().hex[:8]}",
            algorithm="astar",
            distance_km=round(total_distance, 2),
            eta_min=round(total_eta, 1),
            risk_score=round(avg_risk, 2),
            reliability_score=round(1.0 - avg_risk * 0.5, 2),
            segments=segments,
            explanation=[
                "Route calculated using A* with Haversine heuristic",
                f"Vehicle: {request.vehicle.value}",
                f"Mode: {request.mode.value}",
            ],
            data_quality=DataQuality(),
        )

    def calculate_route(self, request: RouteRequest) -> RouteResponse:
        context = self._build_context(request)

        stops = [request.origin] + request.waypoints + [request.destination]
        all_segments = []
        total_distance = 0.0
        total_eta = 0.0
        total_risk = 0.0
        all_explanations = []

        for i in range(len(stops) - 1):
            segment_route = self._route_segment(stops[i], stops[i + 1], context, request)
            all_segments.extend(segment_route.segments)
            total_distance += segment_route.distance_km
            total_eta += segment_route.eta_min
            total_risk += segment_route.risk_score
            all_explanations.extend(segment_route.explanation)

        return RouteResponse(
            route_id=f"route_{uuid.uuid4().hex[:8]}",
            algorithm="astar",
            distance_km=round(total_distance, 2),
            eta_min=round(total_eta, 1),
            risk_score=round(total_risk / max(1, len(stops) - 1), 2),
            reliability_score=round(1.0 - (total_risk / max(1, len(stops) - 1)) * 0.5, 2),
            segments=all_segments,
            explanation=list(set(all_explanations)),
            data_quality=DataQuality(),
        )

    def replan(self, route_id: str, changes: list[dict]) -> RouteResponse:
        return RouteResponse(
            route_id=route_id,
            algorithm="dstar_lite",
            distance_km=0.0,
            eta_min=0.0,
            risk_score=0.0,
            reliability_score=1.0,
            segments=[],
            explanation=["Replanning not yet implemented"],
            data_quality=DataQuality(),
        )


route_engine = RouteEngine()

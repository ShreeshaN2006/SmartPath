import networkx as nx
from models.schemas import RoutingMode, VehicleType
from vehicles.models import get_vehicle_penalty

from risk.weights import get_weights


def calculate_congestion_risk(congestion: float) -> float:
    if congestion < 0.3:
        return 0.1
    elif congestion < 0.6:
        return 0.4
    elif congestion < 0.8:
        return 0.7
    return 0.9


def calculate_weather_risk(weather_code: int, precipitation: float) -> float:
    if weather_code == 0:
        return 0.05
    elif weather_code in [1, 2, 3]:
        return 0.15
    elif weather_code in [45, 48]:
        return 0.3
    elif weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return min(0.2 + precipitation * 0.05, 0.7)
    elif weather_code in [71, 73, 75]:
        return 0.5
    elif weather_code in [95, 96, 99]:
        return 0.8
    return 0.2


def calculate_incident_risk(incidents: list[dict], edge_id: str) -> float:
    for inc in incidents:
        if inc.get("edge_id") == edge_id and inc.get("active", False):
            return inc.get("severity", 0.5)
    return 0.0


def calculate_road_class_risk(highway: str) -> float:
    risk_map = {
        "motorway": 0.1,
        "trunk": 0.15,
        "primary": 0.2,
        "secondary": 0.3,
        "tertiary": 0.4,
        "residential": 0.3,
        "service": 0.5,
        "living_street": 0.6,
        "cycleway": 0.8,
        "footway": 0.9,
        "path": 0.9,
    }
    return risk_map.get(highway, 0.3)


def compute_edge_risk(
    graph: nx.MultiDiGraph,
    u: int,
    v: int,
    weather_data: dict,
    incidents: list[dict],
    vehicle_type: str,
) -> float:
    edge_data = graph.get_edge_data(u, v)
    if not edge_data:
        return 0.5

    for key in edge_data:
        data = edge_data[key]
        highway = data.get("highway", "residential")

        congestion = data.get("congestion", 0.3)
        weather_risk = calculate_weather_risk(weather_data.get("weather_code", 0), weather_data.get("precipitation_mm", 0))
        incident_risk = calculate_incident_risk(incidents, f"{u}_{v}")
        road_class_risk = calculate_road_class_risk(highway)
        vehicle_penalty = get_vehicle_penalty(graph, u, v, vehicle_type) / 1000.0

        return max(
            calculate_congestion_risk(congestion),
            weather_risk,
            incident_risk,
            road_class_risk,
            vehicle_penalty,
        )

    return 0.3


def compute_edge_cost(
    graph: nx.MultiDiGraph,
    u: int,
    v: int,
    context: dict,
) -> float:
    edge_data = graph.get_edge_data(u, v)
    if not edge_data:
        return float('inf')

    mode = context.get("mode", RoutingMode.BALANCED)
    weights = get_weights(mode)
    vehicle = context.get("vehicle", VehicleType.CAR)

    time_cost = float('inf')
    for key in edge_data:
        data = edge_data[key]
        if 'travel_time' in data:
            t = float(data['travel_time']) / 60.0
        elif 'length' in data:
            t = (float(data['length']) / 1000.0) / 30.0 * 60.0
        else:
            t = 1.0
        time_cost = min(time_cost, t)

    congestion = 0.0
    for key in edge_data:
        data = edge_data[key]
        if 'congestion' in data:
            congestion = max(congestion, data['congestion'])

    weather_data = context.get("weather", {})
    incidents = context.get("incidents", [])

    risk = compute_edge_risk(graph, u, v, weather_data, incidents, vehicle)
    vehicle_penalty = get_vehicle_penalty(graph, u, v, vehicle)

    cost = (
        weights.time * time_cost
        + weights.congestion * congestion * 10
        + weights.risk * risk * 20
        + weights.vehicle * vehicle_penalty
    )

    return cost

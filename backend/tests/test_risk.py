import networkx as nx
from models.schemas import RoutingMode
from risk.risk_engine import (
    calculate_congestion_risk,
    calculate_incident_risk,
    calculate_road_class_risk,
    calculate_weather_risk,
    compute_edge_cost,
    compute_edge_risk,
)
from risk.weights import get_weights


def test_calculate_congestion_risk():
    assert calculate_congestion_risk(0.1) == 0.1
    assert calculate_congestion_risk(0.5) == 0.4
    assert calculate_congestion_risk(0.7) == 0.7
    assert calculate_congestion_risk(0.9) == 0.9


def test_calculate_weather_risk():
    assert calculate_weather_risk(0, 0) == 0.05
    assert calculate_weather_risk(1, 0) == 0.15
    assert calculate_weather_risk(61, 5) == 0.45
    assert calculate_weather_risk(95, 0) == 0.8


def test_calculate_incident_risk():
    incidents = [{'edge_id': '1_2', 'active': True, 'severity': 0.8}]
    assert calculate_incident_risk(incidents, '1_2') == 0.8
    assert calculate_incident_risk(incidents, '2_3') == 0.0


def test_calculate_road_class_risk():
    assert calculate_road_class_risk('motorway') == 0.1
    assert calculate_road_class_risk('residential') == 0.3
    assert calculate_road_class_risk('footway') == 0.9


def test_get_weights():
    weights = get_weights(RoutingMode.FASTEST)
    assert weights.time == 2.0
    assert weights.risk == 0.2

    weights = get_weights(RoutingMode.SAFEST)
    assert weights.risk == 2.0
    assert weights.time == 0.5


def test_compute_edge_risk():
    G = nx.MultiDiGraph()
    G.add_node(1, x=77.59, y=12.97)
    G.add_node(2, x=77.60, y=12.97)
    G.add_edge(1, 2, key=0, length=1000, travel_time=120, highway='primary', congestion=0.5)

    weather = {'weather_code': 0, 'precipitation_mm': 0}
    incidents = []
    risk = compute_edge_risk(G, 1, 2, weather, incidents, 'car')
    assert 0 <= risk <= 1


def test_compute_edge_cost():
    G = nx.MultiDiGraph()
    G.add_node(1, x=77.59, y=12.97)
    G.add_node(2, x=77.60, y=12.97)
    G.add_edge(1, 2, key=0, length=1000, travel_time=120, highway='primary', congestion=0.3)

    context = {
        'mode': RoutingMode.BALANCED,
        'vehicle': 'car',
        'weather': {'weather_code': 0, 'precipitation_mm': 0},
        'incidents': [],
    }
    cost = compute_edge_cost(G, 1, 2, context)
    assert cost > 0

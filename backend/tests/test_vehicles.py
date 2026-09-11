import networkx as nx
from models.schemas import VehicleType
from vehicles.models import (
    get_vehicle_constraints,
    get_vehicle_penalty,
)


def test_vehicle_constraints():
    car = get_vehicle_constraints(VehicleType.CAR)
    assert 'motorway' in car.allowed_road_classes
    assert 'footway' in car.forbidden_road_classes

    van = get_vehicle_constraints(VehicleType.DELIVERY_VAN)
    assert van.max_height_m == 3.5
    assert van.max_weight_kg == 3500

    ambulance = get_vehicle_constraints(VehicleType.AMBULANCE)
    assert ambulance.emergency_override

    truck = get_vehicle_constraints(VehicleType.TRUCK)
    assert truck.max_weight_kg == 40000
    assert 'tertiary' in truck.forbidden_road_classes


def test_vehicle_penalty():
    G = nx.MultiDiGraph()
    G.add_node(1, x=77.59, y=12.97)
    G.add_node(2, x=77.60, y=12.97)

    G.add_edge(1, 2, key=0, length=1000, travel_time=120, highway='motorway')
    assert get_vehicle_penalty(G, 1, 2, VehicleType.CAR) == 0
    assert get_vehicle_penalty(G, 1, 2, VehicleType.TRUCK) == 0

    G.add_edge(1, 2, key=1, length=1000, travel_time=120, highway='footway')
    assert get_vehicle_penalty(G, 1, 2, VehicleType.CAR) > 0
    assert get_vehicle_penalty(G, 1, 2, VehicleType.AMBULANCE) == 10.0

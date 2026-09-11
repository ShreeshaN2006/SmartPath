
import networkx as nx
from models.schemas import VehicleConstraints, VehicleType

VEHICLE_CONSTRAINTS: dict[VehicleType, VehicleConstraints] = {
    VehicleType.CAR: VehicleConstraints(
        max_height_m=2.0,
        max_weight_kg=2000,
        max_width_m=2.0,
        allowed_road_classes=["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "service", "living_street"],
        forbidden_road_classes=["cycleway", "footway", "path", "steps", "pedestrian", "track"],
        emergency_override=False,
    ),
    VehicleType.DELIVERY_VAN: VehicleConstraints(
        max_height_m=3.5,
        max_weight_kg=3500,
        max_width_m=2.2,
        allowed_road_classes=["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "service", "living_street"],
        forbidden_road_classes=["cycleway", "footway", "path", "steps", "pedestrian", "track"],
        emergency_override=False,
    ),
    VehicleType.AMBULANCE: VehicleConstraints(
        max_height_m=3.0,
        max_weight_kg=5000,
        max_width_m=2.5,
        allowed_road_classes=["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "service", "living_street"],
        forbidden_road_classes=["cycleway", "footway", "path", "steps"],
        emergency_override=True,
    ),
    VehicleType.TRUCK: VehicleConstraints(
        max_height_m=4.0,
        max_weight_kg=40000,
        max_width_m=2.55,
        allowed_road_classes=["motorway", "trunk", "primary", "secondary"],
        forbidden_road_classes=["tertiary", "residential", "service", "cycleway", "footway", "path", "steps", "pedestrian", "track", "living_street"],
        emergency_override=False,
    ),
}


def get_vehicle_constraints(vehicle: VehicleType) -> VehicleConstraints:
    return VEHICLE_CONSTRAINTS.get(vehicle, VEHICLE_CONSTRAINTS[VehicleType.CAR])


def get_vehicle_penalty(graph: nx.MultiDiGraph, u: int, v: int, vehicle: VehicleType) -> float:
    constraints = get_vehicle_constraints(vehicle)
    edge_data = graph.get_edge_data(u, v)
    if not edge_data:
        return 1.0

    for key in edge_data:
        data = edge_data[key]
        highway = data.get("highway", "")
        if highway in constraints.forbidden_road_classes:
            if constraints.emergency_override:
                return 10.0
            return 1000.0
        if highway not in constraints.allowed_road_classes:
            if constraints.emergency_override:
                return 5.0
            return 100.0

        if "maxheight" in data and constraints.max_height_m:
            try:
                max_h = float(data["maxheight"].replace("m", ""))
                if max_h < constraints.max_height_m:
                    return 50.0
            except:
                pass

    return 0.0

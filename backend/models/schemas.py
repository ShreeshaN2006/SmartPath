from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class VehicleType(str, Enum):
    CAR = "car"
    DELIVERY_VAN = "delivery_van"
    AMBULANCE = "ambulance"
    TRUCK = "truck"


class RoutingMode(str, Enum):
    FASTEST = "fastest"
    SAFEST = "safest"
    BALANCED = "balanced"
    EMERGENCY = "emergency"


class VehicleConstraints(BaseModel):
    max_height_m: float | None = None
    max_weight_kg: float | None = None
    max_width_m: float | None = None
    allowed_road_classes: list[str] = Field(default_factory=list)
    forbidden_road_classes: list[str] = Field(default_factory=list)
    emergency_override: bool = False


DEFAULT_VEHICLE_CONSTRAINTS: dict[VehicleType, VehicleConstraints] = {
    VehicleType.CAR: VehicleConstraints(
        allowed_road_classes=["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "service"],
        forbidden_road_classes=["cycleway", "footway", "path", "steps"],
    ),
    VehicleType.DELIVERY_VAN: VehicleConstraints(
        max_height_m=3.5,
        max_weight_kg=3500,
        allowed_road_classes=["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "service"],
        forbidden_road_classes=["cycleway", "footway", "path", "steps", "pedestrian"],
    ),
    VehicleType.AMBULANCE: VehicleConstraints(
        allowed_road_classes=["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "service"],
        forbidden_road_classes=["cycleway", "footway", "path", "steps"],
        emergency_override=True,
    ),
    VehicleType.TRUCK: VehicleConstraints(
        max_height_m=4.0,
        max_weight_kg=40000,
        allowed_road_classes=["motorway", "trunk", "primary", "secondary"],
        forbidden_road_classes=["tertiary", "residential", "service", "cycleway", "footway", "path", "steps", "pedestrian"],
    ),
}


class RouteRequest(BaseModel):
    origin: Coordinates
    destination: Coordinates
    vehicle: VehicleType = VehicleType.CAR
    mode: RoutingMode = RoutingMode.BALANCED
    depart_at: datetime | None = None
    waypoints: list[Coordinates] = Field(default_factory=list)


class RouteSegment(BaseModel):
    edge_id: str
    coords: list[Coordinates]
    distance_m: float
    travel_time_min: float
    congestion: float
    risk: float
    road_class: str


class DataQuality(BaseModel):
    traffic: Literal["live", "simulated", "historical", "predicted"] = "simulated"
    weather: Literal["live", "simulated", "historical"] = "simulated"
    incidents: Literal["live", "simulated", "historical"] = "simulated"


class RouteResponse(BaseModel):
    route_id: str
    algorithm: str
    distance_km: float
    eta_min: float
    risk_score: float
    reliability_score: float
    segments: list[RouteSegment]
    explanation: list[str]
    data_quality: DataQuality


class ReplanRequest(BaseModel):
    route_id: str
    changes: list[dict[str, Any]]


class WeatherData(BaseModel):
    temperature_c: float
    precipitation_mm: float
    wind_speed_kmh: float
    weather_code: int


class Incident(BaseModel):
    id: str
    edge_id: str
    type: Literal["road_blockage", "accident", "construction", "flooding", "other"]
    severity: float = Field(..., ge=0, le=1)
    active: bool
    started_at: datetime
    expires_at: datetime | None = None


class IncidentSimulateRequest(BaseModel):
    edge_id: str
    type: Literal["road_blockage", "accident", "construction", "flooding", "other"] = "road_blockage"
    severity: float = Field(..., ge=0, le=1)
    active: bool = True
    expires_at: datetime | None = None


class TrafficData(BaseModel):
    edge_id: str
    current_speed_kmh: float
    predicted_speed_kmh: float
    congestion: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)


class RiskFactors(BaseModel):
    congestion: float = Field(..., ge=0, le=1)
    weather: float = Field(..., ge=0, le=1)
    incident_severity: float = Field(..., ge=0, le=1)
    road_class: float = Field(..., ge=0, le=1)
    vehicle_compatibility: float = Field(..., ge=0, le=1)
    historical_reliability: float = Field(..., ge=0, le=1)


class AlgorithmMetrics(BaseModel):
    nodes_expanded: int
    execution_time_ms: float
    path_cost: float
    success: bool


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"

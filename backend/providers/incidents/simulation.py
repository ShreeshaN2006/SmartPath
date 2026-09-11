import random
import uuid
from datetime import datetime, timedelta

from models.schemas import Incident, IncidentSimulateRequest

from providers.base import IncidentProvider


class SimulationIncidentProvider(IncidentProvider):
    def __init__(self):
        self.incidents: dict[str, Incident] = {}
        self._generate_initial_incidents()

    def _generate_initial_incidents(self):
        for i in range(5):
            incident = Incident(
                id=f"inc_{i}",
                edge_id=f"edge_{random.randint(0, 99)}",
                type=random.choice(["road_blockage", "accident", "construction", "flooding"]),
                severity=round(random.uniform(0.3, 0.9), 2),
                active=True,
                started_at=datetime.now() - timedelta(minutes=random.randint(0, 120)),
                expires_at=datetime.now() + timedelta(minutes=random.randint(30, 240)),
            )
            self.incidents[incident.id] = incident

    def get_incidents(self, bounds: dict[str, float] | None = None) -> list[Incident]:
        return [inc for inc in self.incidents.values() if inc.active]

    def simulate_incident(self, request: IncidentSimulateRequest) -> Incident:
        incident = Incident(
            id=f"inc_{uuid.uuid4().hex[:8]}",
            edge_id=request.edge_id,
            type=request.type,
            severity=request.severity,
            active=request.active,
            started_at=datetime.now(),
            expires_at=request.expires_at,
        )
        self.incidents[incident.id] = incident
        return incident

    def get_provider_name(self) -> str:
        return "simulation"


class DatasetIncidentProvider(IncidentProvider):
    def get_incidents(self, bounds: dict[str, float] | None = None) -> list[Incident]:
        return []

    def simulate_incident(self, incident: Incident) -> Incident:
        return incident

    def get_provider_name(self) -> str:
        return "dataset"


def get_incident_provider() -> IncidentProvider:
    import os
    provider_name = os.getenv("INCIDENT_PROVIDER", "simulation")
    if provider_name == "simulation":
        return SimulationIncidentProvider()
    elif provider_name == "dataset":
        return DatasetIncidentProvider()
    raise ValueError(f"Unknown incident provider: {provider_name}")

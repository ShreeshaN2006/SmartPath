import random

from models.schemas import TrafficData

from providers.base import TrafficProvider


class SimulationTrafficProvider(TrafficProvider):
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def get_traffic(self, bounds: dict[str, float] | None = None) -> list[TrafficData]:
        num_edges = 100
        traffic = []
        for i in range(num_edges):
            congestion = random.uniform(0.1, 0.9)
            base_speed = random.uniform(20, 60)
            current_speed = base_speed * (1 - congestion * 0.7)
            predicted_speed = current_speed * random.uniform(0.8, 1.2)
            traffic.append(TrafficData(
                edge_id=f"edge_{i}",
                current_speed_kmh=round(current_speed, 1),
                predicted_speed_kmh=round(predicted_speed, 1),
                congestion=round(congestion, 2),
                confidence=random.uniform(0.6, 0.95),
            ))
        return traffic

    def get_forecast(self, horizon_minutes: int, bounds: dict[str, float] | None = None) -> list[TrafficData]:
        current = self.get_traffic(bounds)
        for t in current:
            factor = 1.0 + (horizon_minutes / 60.0) * random.uniform(-0.2, 0.3)
            t.predicted_speed_kmh = round(t.current_speed_kmh * factor, 1)
            t.congestion = min(1.0, t.congestion * factor)
        return current

    def get_provider_name(self) -> str:
        return "simulation"


class DatasetTrafficProvider(TrafficProvider):
    def __init__(self, data_path: str = "data/traffic"):
        self.data_path = data_path

    def get_traffic(self, bounds: dict[str, float] | None = None) -> list[TrafficData]:
        return []

    def get_forecast(self, horizon_minutes: int, bounds: dict[str, float] | None = None) -> list[TrafficData]:
        return []

    def get_provider_name(self) -> str:
        return "dataset"


def get_traffic_provider() -> TrafficProvider:
    import os
    provider_name = os.getenv("TRAFFIC_PROVIDER", "simulation")
    if provider_name == "simulation":
        return SimulationTrafficProvider()
    elif provider_name == "dataset":
        return DatasetTrafficProvider()
    raise ValueError(f"Unknown traffic provider: {provider_name}")

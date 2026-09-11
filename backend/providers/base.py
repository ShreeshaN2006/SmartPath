from abc import ABC, abstractmethod
from typing import Any, Protocol

from models.schemas import Incident, TrafficData, WeatherData


class TrafficProvider(ABC):
    @abstractmethod
    def get_traffic(self, bounds: dict[str, float] | None = None) -> list[TrafficData]:
        pass

    @abstractmethod
    def get_forecast(self, horizon_minutes: int, bounds: dict[str, float] | None = None) -> list[TrafficData]:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class WeatherProvider(ABC):
    @abstractmethod
    def get_weather(self, lat: float, lng: float) -> WeatherData:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class IncidentProvider(ABC):
    @abstractmethod
    def get_incidents(self, bounds: dict[str, float] | None = None) -> list[Incident]:
        pass

    @abstractmethod
    def simulate_incident(self, incident: Incident) -> Incident:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class RoutingAlgorithm(Protocol):
    def route(self, graph: Any, source: int, target: int, context: dict[str, Any]) -> dict[str, Any]:
        ...


class CacheProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Any | None:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

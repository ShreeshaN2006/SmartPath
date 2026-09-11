import os

import requests
from models.schemas import WeatherData
from utils.cache import get_cache

from providers.base import WeatherProvider


class OpenMeteoProvider(WeatherProvider):
    def __init__(self, timeout: int = 10, cache_ttl: int = 600):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.cache = get_cache()

    def get_weather(self, lat: float, lng: float) -> WeatherData:
        cache_key = f"weather:{lat:.4f}:{lng:.4f}"
        cached = self.cache.get(cache_key)
        if cached:
            return WeatherData(**cached)

        params = {
            "latitude": lat,
            "longitude": lng,
            "current": "temperature_2m,precipitation,wind_speed_10m,weather_code",
            "timezone": "auto",
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            weather = WeatherData(
                temperature_c=current.get("temperature_2m", 20.0),
                precipitation_mm=current.get("precipitation", 0.0),
                wind_speed_kmh=current.get("wind_speed_10m", 0.0),
                weather_code=current.get("weather_code", 0),
            )

            self.cache.set(cache_key, weather.model_dump(), self.cache_ttl)
            return weather

        except Exception as e:
            print(f"[Weather] Open-Meteo error: {e}")
            return WeatherData(
                temperature_c=25.0,
                precipitation_mm=0.0,
                wind_speed_kmh=10.0,
                weather_code=0,
            )

    def get_provider_name(self) -> str:
        return "open_meteo"


def get_weather_provider() -> WeatherProvider:
    provider_name = os.getenv("WEATHER_PROVIDER", "open_meteo")
    if provider_name == "open_meteo":
        return OpenMeteoProvider()
    raise ValueError(f"Unknown weather provider: {provider_name}")

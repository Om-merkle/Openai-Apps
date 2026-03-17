"""HTTP client helpers for geocoding and forecast calls."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.models import Coordinates, CurrentWeather, DailyForecast, LocationMatch, TemperatureUnit, WeatherToolResponse


WEATHER_CODE_DESCRIPTIONS: dict[int, str] = {
    0: "Clear sky",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


class WeatherClient:
    """Thin async client around Open-Meteo APIs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # One shared async client keeps connection reuse efficient.
        self._client = httpx.AsyncClient(timeout=20.0)

    async def close(self) -> None:
        """Close the underlying HTTP client during app shutdown."""
        await self._client.aclose()

    async def get_weather(self, location: str, days: int, unit: TemperatureUnit) -> WeatherToolResponse:
        """Resolve a place name, fetch forecast data, and shape it for the MCP tool."""
        place = await self._geocode_location(location)
        weather_payload = await self._fetch_forecast(place.coordinates, days, unit)

        current_units = weather_payload.get("current_units", {})
        current = weather_payload["current"]
        daily = weather_payload["daily"]

        # Convert the raw JSON into typed models to keep the rest of the app predictable.
        current_weather = CurrentWeather(
            temperature=current["temperature_2m"],
            wind_speed=current["wind_speed_10m"],
            wind_direction=current["wind_direction_10m"],
            weather_code=current["weather_code"],
            is_day=current["is_day"],
            time=current["time"],
            unit="fahrenheit" if str(current_units.get("temperature_2m", "")).endswith("F") else "celsius",
        )

        forecast_days = [
            DailyForecast(
                date=daily["time"][index],
                weather_code=daily["weather_code"][index],
                temperature_max=daily["temperature_2m_max"][index],
                temperature_min=daily["temperature_2m_min"][index],
                precipitation_probability_max=(
                    daily["precipitation_probability_max"][index]
                    if "precipitation_probability_max" in daily
                    else None
                ),
            )
            for index in range(len(daily["time"]))
        ]

        summary = self._build_summary(place, current_weather, forecast_days)
        return WeatherToolResponse(location=place, current=current_weather, forecast=forecast_days, summary=summary)

    async def _geocode_location(self, location: str) -> LocationMatch:
        """Find the best match for a user-entered place name."""
        response = await self._client.get(
            f"{self.settings.geocoding_api_base_url}/search",
            params={"name": location, "count": 1, "language": "en", "format": "json"},
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])
        if not results:
            raise ValueError(f'No location was found for "{location}".')

        best_match = results[0]
        return LocationMatch(
            name=best_match["name"],
            country=best_match.get("country"),
            admin1=best_match.get("admin1"),
            coordinates=Coordinates(latitude=best_match["latitude"], longitude=best_match["longitude"]),
        )

    async def _fetch_forecast(
        self,
        coordinates: Coordinates,
        days: int,
        unit: TemperatureUnit,
    ) -> dict[str, Any]:
        """Request current weather and a short daily forecast."""
        temperature_unit = "fahrenheit" if unit == "fahrenheit" else "celsius"
        response = await self._client.get(
            f"{self.settings.weather_api_base_url}/forecast",
            params={
                "latitude": coordinates.latitude,
                "longitude": coordinates.longitude,
                "current": "temperature_2m,weather_code,wind_speed_10m,wind_direction_10m,is_day",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": days,
                "timezone": "auto",
                "temperature_unit": temperature_unit,
                "wind_speed_unit": "kmh",
            },
        )
        response.raise_for_status()
        return response.json()

    def _build_summary(
        self,
        location: LocationMatch,
        current: CurrentWeather,
        forecast: list[DailyForecast],
    ) -> str:
        """Generate a short natural-language summary for ChatGPT to display."""
        today = forecast[0]
        place_bits = [location.name]
        if location.admin1:
            place_bits.append(location.admin1)
        if location.country:
            place_bits.append(location.country)

        unit_label = "F" if current.unit == "fahrenheit" else "C"
        current_text = WEATHER_CODE_DESCRIPTIONS.get(current.weather_code, "Current conditions unavailable")
        today_text = WEATHER_CODE_DESCRIPTIONS.get(today.weather_code, "Forecast unavailable")

        return (
            f"{', '.join(place_bits)} is {current.temperature} deg {unit_label} with {current_text.lower()}. "
            f"Today's range is {today.temperature_min} deg {unit_label} to {today.temperature_max} deg {unit_label} "
            f"with {today_text.lower()}."
        )

"""Pydantic models used by the Weather Info app."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


TemperatureUnit = Literal["celsius", "fahrenheit"]


class Coordinates(BaseModel):
    """Latitude and longitude returned from geocoding."""

    latitude: float = Field(..., description="Latitude for the resolved place.")
    longitude: float = Field(..., description="Longitude for the resolved place.")


class LocationMatch(BaseModel):
    """Best place match returned from the geocoding service."""

    name: str = Field(..., description="Resolved display name for the location.")
    country: str | None = Field(default=None, description="Country name when available.")
    admin1: str | None = Field(default=None, description="State / region when available.")
    coordinates: Coordinates


class CurrentWeather(BaseModel):
    """Current weather snapshot used by the tool response and widget."""

    temperature: float
    wind_speed: float
    wind_direction: float
    weather_code: int
    is_day: int
    time: str
    unit: TemperatureUnit


class DailyForecast(BaseModel):
    """Single forecast day."""

    date: str
    weather_code: int
    temperature_max: float
    temperature_min: float
    precipitation_probability_max: int | None = None


class WeatherToolResponse(BaseModel):
    """Structured payload returned by the MCP tool."""

    location: LocationMatch
    current: CurrentWeather
    forecast: list[DailyForecast]
    summary: str

"""Application configuration for the Weather Info ChatGPT app."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class Settings:
    """Central place for environment-driven settings."""

    app_name: str = os.getenv("APP_NAME", "Weather Info")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "https://chatgpt.com,https://chat.openai.com").split(",")
            if origin.strip()
        ]
    )
    forecast_days_limit: int = int(os.getenv("FORECAST_DAYS_LIMIT", "5"))
    connect_base_url: str = os.getenv("PUBLIC_BASE_URL", "")
    weather_api_base_url: str = os.getenv("WEATHER_API_BASE_URL", "https://api.open-meteo.com/v1")
    geocoding_api_base_url: str = os.getenv("GEOCODING_API_BASE_URL", "https://geocoding-api.open-meteo.com/v1")

    @property
    def mcp_url(self) -> str:
        """Full MCP endpoint that ChatGPT should connect to."""
        return f"{self.connect_base_url.rstrip('/')}/mcp"

    @property
    def widget_url(self) -> str:
        """Hosted HTML widget URL."""
        return f"{self.connect_base_url.rstrip('/')}/widget"

    @property
    def health_url(self) -> str:
        """Health-check URL for local verification."""
        return f"{self.connect_base_url.rstrip('/')}/healthz"

    @property
    def connections_url(self) -> str:
        """Helpful endpoint that lists every important connection."""
        return f"{self.connect_base_url.rstrip('/')}/connections"


settings = Settings()

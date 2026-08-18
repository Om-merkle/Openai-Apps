"""Application configuration for the Weather Info ChatGPT app."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit


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
    cloudflare_tunnel_name: str = os.getenv("CLOUDFLARE_TUNNEL_NAME", "weather-info")
    cloudflare_tunnel_hostname: str = os.getenv("CLOUDFLARE_TUNNEL_HOSTNAME", "")
    weather_api_base_url: str = os.getenv("WEATHER_API_BASE_URL", "https://api.open-meteo.com/v1")
    geocoding_api_base_url: str = os.getenv("GEOCODING_API_BASE_URL", "https://geocoding-api.open-meteo.com/v1")
    openai_apps_docs_url: str = os.getenv("OPENAI_APPS_DOCS_URL", "https://developers.openai.com/apps-sdk/")
    openai_apps_deploy_url: str = os.getenv("OPENAI_APPS_DEPLOY_URL", "https://developers.openai.com/apps-sdk/deploy")
    openai_platform_apps_url: str = os.getenv("OPENAI_PLATFORM_APPS_URL", "https://platform.openai.com")

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

    @property
    def mcp_allowed_hosts(self) -> list[str]:
        """Host headers accepted by the MCP DNS-rebinding protection."""
        allowed_hosts = [
            "127.0.0.1",
            "127.0.0.1:*",
            "localhost",
            "localhost:*",
            "[::1]",
            "[::1]:*",
        ]

        configured_url = self.connect_base_url.strip()
        if configured_url:
            parsed_url = urlsplit(configured_url)
            if parsed_url.hostname:
                hostname = parsed_url.hostname
                if ":" in hostname:
                    hostname = f"[{hostname}]"

                allowed_hosts.extend([hostname, f"{hostname}:*"])

        return list(dict.fromkeys(allowed_hosts))

    @property
    def mcp_allowed_origins(self) -> list[str]:
        """Browser origins accepted by the MCP DNS-rebinding protection."""
        allowed_origins = [
            "http://127.0.0.1:*",
            "http://localhost:*",
            "http://[::1]:*",
            *(origin.rstrip("/") for origin in self.allowed_origins),
        ]

        configured_url = self.connect_base_url.strip()
        if configured_url:
            parsed_url = urlsplit(configured_url)
            if parsed_url.scheme and parsed_url.netloc:
                allowed_origins.append(f"{parsed_url.scheme}://{parsed_url.netloc}")

        return list(dict.fromkeys(allowed_origins))

    @property
    def cloudflare_public_url(self) -> str:
        """Public Cloudflare hostname when the user configures one."""
        if not self.cloudflare_tunnel_hostname.strip():
            return ""

        return f"https://{self.cloudflare_tunnel_hostname.strip()}"


settings = Settings()

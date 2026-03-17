"""FastMCP server that exposes the Weather Info tool to ChatGPT."""

from __future__ import annotations

from typing import Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

from app.config import settings
from app.services.weather_client import WeatherClient


# This FastMCP instance is the MCP server ChatGPT connects to.
mcp = FastMCP(
    name=settings.app_name,
    stateless_http=True,
    json_response=True,
    instructions=(
        "Use the weather tool whenever a user asks for current weather or a short forecast "
        "for a city, state, or country."
    ),
)

# Mounting the server at /mcp becomes cleaner when the inner MCP path is set to root.
mcp.settings.streamable_http_path = "/"


# The shared weather client is attached by the FastAPI app during startup.
weather_client: WeatherClient | None = None


def attach_weather_client(client: WeatherClient) -> None:
    """Allow the FastAPI host to inject a ready-to-use API client."""
    global weather_client
    weather_client = client


@mcp.tool()
async def get_weather_info(
    location: str,
    days: int = 3,
    unit: Literal["celsius", "fahrenheit"] = "celsius",
) -> CallToolResult:
    """
    Look up current weather and a short forecast for a user-provided location.

    The location can be a city, state, or country name.
    """
    if weather_client is None:
        raise RuntimeError("Weather client is not ready yet. Start the FastAPI app first.")

    # Clamp the forecast window so the tool stays fast and predictable inside ChatGPT.
    safe_days = max(1, min(days, settings.forecast_days_limit))
    weather = await weather_client.get_weather(location=location, days=safe_days, unit=unit)

    # Return both text content and structured JSON so ChatGPT can summarize or render it.
    return CallToolResult(
        content=[TextContent(type="text", text=weather.summary)],
        structuredContent=weather.model_dump(),
    )

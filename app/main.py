"""FastAPI host application for the Weather Info ChatGPT app."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.mcp_server import attach_weather_client, mcp
from app.services.weather_client import WeatherClient

BASE_DIR = Path(__file__).resolve().parents[1]


def resolve_base_url(request: Request) -> str:
    """Prefer an explicit public URL, but fall back to the current request host when needed."""
    configured_base_url = settings.connect_base_url.strip()
    if configured_base_url:
        return configured_base_url.rstrip("/")

    return str(request.base_url).rstrip("/")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create shared connections when the API boots and clean them up on shutdown."""
    weather_client = WeatherClient(settings)
    attach_weather_client(weather_client)
    try:
        yield
    finally:
        await weather_client.close()


# FastAPI hosts the MCP server, the widget, and helper routes in one process.
app = FastAPI(
    title=settings.app_name,
    description="ChatGPT App + MCP server that returns weather information.",
    version="1.0.0",
    lifespan=lifespan,
)

# These CORS settings allow the ChatGPT web client to reach the app while developing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the static widget assets from a simple folder.
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Mount the streamable HTTP MCP app at /mcp so ChatGPT can connect to it.
app.mount("/mcp", mcp.streamable_http_app())


@app.get("/", tags=["meta"])
async def index(request: Request) -> dict[str, object]:
    """Short landing payload for local debugging."""
    base_url = resolve_base_url(request)
    return {
        "name": settings.app_name,
        "message": "Weather Info ChatGPT app is running.",
        "connections": {
            "mcp": f"{base_url}/mcp",
            "widget": f"{base_url}/widget",
            "health": f"{base_url}/healthz",
            "inventory": f"{base_url}/connections",
        },
    }


@app.get("/healthz", tags=["meta"])
async def healthcheck() -> dict[str, str]:
    """Simple health endpoint for local checks and deployment probes."""
    return {"status": "ok"}


@app.get("/connections", tags=["meta"])
async def connections(request: Request) -> dict[str, object]:
    """List every important connection so setup is easy to verify."""
    base_url = resolve_base_url(request)
    return {
        "app_name": settings.app_name,
        "base_url": base_url,
        "connections": [
            {
                "name": "FastAPI root",
                "url": base_url,
                "purpose": "Human-readable root response for quick checks.",
            },
            {
                "name": "MCP server",
                "url": f"{base_url}/mcp",
                "purpose": "Connector URL to add inside ChatGPT Apps.",
            },
            {
                "name": "Widget page",
                "url": f"{base_url}/widget",
                "purpose": "Hosted HTML page for a simple weather card UI.",
            },
            {
                "name": "Health check",
                "url": f"{base_url}/healthz",
                "purpose": "Operational check for local or deployed environments.",
            },
        ],
        "external_services": [
            {
                "name": "Open-Meteo Geocoding API",
                "url": f"{settings.geocoding_api_base_url}/search",
                "purpose": "Converts a place name into latitude and longitude.",
            },
            {
                "name": "Open-Meteo Forecast API",
                "url": f"{settings.weather_api_base_url}/forecast",
                "purpose": "Returns current weather plus a short forecast.",
            },
        ],
    }


@app.get("/widget", tags=["ui"])
async def widget() -> FileResponse:
    """Serve the example HTML widget used by this app."""
    return FileResponse(BASE_DIR / "static" / "widget.html")

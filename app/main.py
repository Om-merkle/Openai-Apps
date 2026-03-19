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
MCP_HTTP_APP = mcp.streamable_http_app()


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
    # Mounted sub-app lifespans are not started automatically here, so we enter the
    # MCP app lifespan explicitly to initialize the session manager before /mcp is used.
    async with MCP_HTTP_APP.router.lifespan_context(MCP_HTTP_APP):
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
app.mount("/mcp", MCP_HTTP_APP)


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
            {
                "name": "OpenAI Apps SDK docs",
                "url": settings.openai_apps_docs_url,
                "purpose": "Primary documentation for building ChatGPT apps and MCP integrations.",
            },
            {
                "name": "OpenAI Apps deployment docs",
                "url": settings.openai_apps_deploy_url,
                "purpose": "Deployment guidance for exposing an MCP server to ChatGPT.",
            },
            {
                "name": "OpenAI Platform",
                "url": settings.openai_platform_apps_url,
                "purpose": "Platform entry point for broader OpenAI project management and integrations.",
            },
            {
                "name": "Cloudflare public hostname",
                "url": settings.cloudflare_public_url or "Not configured yet",
                "purpose": "Optional public HTTPS endpoint for exposing this app without ngrok.",
            },
        ],
    }


@app.get("/integration-guide", tags=["meta"])
async def integration_guide(request: Request) -> dict[str, object]:
    """Return a machine-readable setup guide covering local, Cloudflare, and ChatGPT steps."""
    base_url = resolve_base_url(request)
    return {
        "app_name": settings.app_name,
        "summary": "Step-by-step integration guide for local development, Cloudflare exposure, and ChatGPT connection.",
        "steps": [
            {
                "step": 1,
                "title": "Run the FastAPI app locally",
                "details": "Start uvicorn from the weather_info_app folder.",
                "command": "uvicorn app.main:app --reload --host 127.0.0.1 --port 8000",
            },
            {
                "step": 2,
                "title": "Verify local routes",
                "details": "Open the root, health, connections, and widget routes in a browser.",
                "links": [
                    f"{base_url}/",
                    f"{base_url}/healthz",
                    f"{base_url}/connections",
                    f"{base_url}/widget",
                ],
            },
            {
                "step": 3,
                "title": "Expose the app with Cloudflare",
                "details": "Point a Cloudflare Tunnel hostname at http://127.0.0.1:8000 or your hosted app URL.",
                "cloudflare_hostname": settings.cloudflare_public_url or "Set CLOUDFLARE_TUNNEL_HOSTNAME in .env",
            },
            {
                "step": 4,
                "title": "Connect ChatGPT",
                "details": "Use the public HTTPS MCP endpoint in the ChatGPT connector flow.",
                "chatgpt_connector_url": (
                    f"{settings.cloudflare_public_url}/mcp"
                    if settings.cloudflare_public_url
                    else "https://your-public-url.example/mcp"
                ),
            },
            {
                "step": 5,
                "title": "Review OpenAI Apps references",
                "details": "Use the official OpenAI Apps SDK docs and deployment docs while integrating.",
                "links": [
                    settings.openai_apps_docs_url,
                    settings.openai_apps_deploy_url,
                    settings.openai_platform_apps_url,
                ],
            },
        ],
    }


@app.get("/widget", tags=["ui"])
async def widget() -> FileResponse:
    """Serve the example HTML widget used by this app."""
    return FileResponse(BASE_DIR / "static" / "widget.html")

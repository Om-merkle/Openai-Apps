# Weather Info

`Weather Info` is a starter ChatGPT App that uses:

- OpenAI ChatGPT Apps connector flow
- Python `FastMCP` from the official MCP Python SDK
- `FastAPI` as the host web app
- Open-Meteo APIs for geocoding and weather data

Every major step in the code has comments so new users can understand the app structure.

## Project structure

```text
weather_info_app/
|-- .env.example
|-- README.md
|-- requirements.txt
|-- app/
|   |-- __init__.py
|   |-- config.py
|   |-- main.py
|   |-- mcp_server.py
|   |-- models.py
|   `-- services/
|       |-- __init__.py
|       `-- weather_client.py
`-- static/
    `-- widget.html
```

## Connections to check

This app exposes and uses these connections:

1. `FastAPI root`
   `GET /`
   Quick local verification that the app is up.
2. `MCP server`
   `POST /mcp`
   This is the connector URL to add inside ChatGPT Apps.
3. `Widget page`
   `GET /widget`
   Local preview page for the weather card UI.
4. `Health check`
   `GET /healthz`
   Simple operational endpoint.
5. `Connection inventory`
   `GET /connections`
   Returns all internal and external URLs in one payload.
6. `Open-Meteo Geocoding API`
   `https://geocoding-api.open-meteo.com/v1/search`
   Used to resolve place names to coordinates.
7. `Open-Meteo Forecast API`
   `https://api.open-meteo.com/v1/forecast`
   Used to fetch current weather and daily forecasts.

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` values into your shell or into your preferred `.env` loader.
4. Start the app from the `weather_info_app` folder:

```powershell
cd weather_info_app
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## VS Code Remote - Tunnels setup

You can use VS Code Remote - Tunnels for development if you cannot use `ngrok` on your company laptop.

### What this is good for

- local development
- temporary ChatGPT connector testing
- sharing a running dev app through an HTTPS tunnel

### What this is not ideal for

- long-term production hosting
- highly stable public endpoints

### Steps

1. Start the app locally:

```powershell
cd weather_info_app
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

2. In VS Code, start a Remote Tunnel for this machine.
3. Forward port `8000` and make sure the forwarded URL is publicly reachable over `https`.
4. Set `PUBLIC_BASE_URL` to your VS Code tunnel URL.
5. Verify these pages in the browser:
   - `https://your-tunnel-url/`
   - `https://your-tunnel-url/healthz`
   - `https://your-tunnel-url/connections`
   - `https://your-tunnel-url/widget`
6. In ChatGPT, add the connector using:

```text
https://your-tunnel-url/mcp
```

### Important notes

- If the VS Code tunnel requires you to be signed in before opening the URL, ChatGPT will not be able to reach it.
- The tunnel URL must be directly reachable by ChatGPT over public `https`.
- For better results, set `PUBLIC_BASE_URL` in your `.env` file before starting the app.

## Connect it in ChatGPT

1. Deploy the app or start it locally for testing.
2. Set `PUBLIC_BASE_URL` to your final HTTPS URL, such as a tunnel URL or your deployed domain.
3. Open ChatGPT and add a new connector / app using your MCP endpoint:

```text
https://your-public-url.example/mcp
```

4. Ask for weather in a place such as:

```text
What's the weather in Hyderabad for the next 3 days?
```

## Notes

- The `get_weather_info` MCP tool returns both plain text and structured JSON.
- The widget at `/widget` is included so you can preview a simple UI and extend it later.
- The `/connections` route was added specifically so users can inspect all relevant connections quickly.

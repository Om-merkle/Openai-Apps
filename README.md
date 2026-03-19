# Weather Info

`Weather Info` is an OpenAI ChatGPT App starter that uses:

- ChatGPT Apps SDK concepts and connector flow
- Python `FastMCP` from the official MCP Python SDK
- `FastAPI` as the host web app
- Open-Meteo APIs for geocoding and weather data
- Cloudflare Tunnel for public HTTPS exposure

Every major code path includes comments so users can follow each process.

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
|-- cloudflare/
|   `-- cloudflared.example.yml
`-- static/
    `-- widget.html
```

## File connection map

This is how the files connect to each other at runtime:

1. `app/config.py`
   Reads environment variables and builds shared settings such as:
   - local host and port
   - public base URL
   - Cloudflare tunnel metadata
   - OpenAI Apps docs links
   - external weather API base URLs

2. `app/main.py`
   Starts the FastAPI app and connects:
   - `settings` from `app/config.py`
   - `mcp` from `app/mcp_server.py`
   - `WeatherClient` from `app/services/weather_client.py`
   - `widget.html` from `static/widget.html`

3. `app/mcp_server.py`
   Defines the FastMCP server and the `get_weather_info` tool.
   It depends on:
   - `settings` from `app/config.py`
   - `WeatherClient` from `app/services/weather_client.py`

4. `app/services/weather_client.py`
   Makes external HTTP calls to:
   - Open-Meteo Geocoding API
   - Open-Meteo Forecast API
   It shapes the responses into models from `app/models.py`.

5. `app/models.py`
   Defines the Pydantic models used in the MCP tool response:
   - `LocationMatch`
   - `CurrentWeather`
   - `DailyForecast`
   - `WeatherToolResponse`

6. `static/widget.html`
   Reads tool output injected by ChatGPT through `window.openai`.
   If ChatGPT has not injected tool output yet, it renders fallback demo data.

7. `.env` and `.env.example`
   Supply the settings used by `app/config.py`.

8. `cloudflare/cloudflared.example.yml`
   Shows how Cloudflare should route a public hostname to:
   - `http://127.0.0.1:8000`

9. `cloudflare-setup.md`
   Gives the Cloudflare command flow needed to expose this local app publicly.

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
6. `Integration guide`
   `GET /integration-guide`
   Returns local run, Cloudflare, and ChatGPT connection steps in JSON.
7. `Open-Meteo Geocoding API`
   `https://geocoding-api.open-meteo.com/v1/search`
   Resolves place names to coordinates.
8. `Open-Meteo Forecast API`
   `https://api.open-meteo.com/v1/forecast`
   Returns current weather and daily forecasts.
9. `OpenAI Apps SDK docs`
   `https://developers.openai.com/apps-sdk/`
   Official OpenAI Apps SDK reference.
10. `OpenAI Apps deploy docs`
    `https://developers.openai.com/apps-sdk/deploy`
    Official deployment guidance for exposing MCP servers to ChatGPT.
11. `OpenAI Platform`
    `https://platform.openai.com`
    Platform entry point for OpenAI projects and integrations.

## Endpoint connection map

These are the active endpoints and what each one connects to:

1. `GET /`
   Returns app metadata and links to the main local routes.
   Internal connection:
   - `app/main.py` -> `resolve_base_url()` -> `settings`

2. `GET /healthz`
   Returns a simple health payload.
   Internal connection:
   - `app/main.py`

3. `GET /connections`
   Returns the full connection inventory.
   Internal connections:
   - `app/main.py` -> `settings`
   External references listed:
   - Open-Meteo endpoints
   - OpenAI Apps docs
   - OpenAI Platform
   - Cloudflare hostname metadata

4. `GET /integration-guide`
   Returns a machine-readable setup guide.
   Internal connections:
   - `app/main.py` -> `settings`

5. `GET /widget`
   Serves the local HTML widget.
   Internal connection:
   - `app/main.py` -> `static/widget.html`

6. `POST /mcp`
   Main MCP endpoint used by ChatGPT or any MCP client.
   Internal flow:
   - `app/main.py` mounts the MCP app
   - `app/mcp_server.py` exposes `get_weather_info`
   - `get_weather_info` calls `WeatherClient.get_weather()`
   - `WeatherClient` calls Open-Meteo APIs

7. `GET /mcp`
   Part of the Streamable HTTP MCP transport.
   This route is used by MCP clients for transport behavior and is not a normal browser page.

## Step 1: Create a virtual environment

Open PowerShell in `weather_info_app` and run:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
```

## Step 2: Install dependencies

Install the project dependencies:

```powershell
pip install -r requirements.txt
```

## Step 3: Create your local environment file

Use `.env.example` as the template and create `.env`.

Example:

```env
APP_NAME=Weather Info
HOST=127.0.0.1
PORT=8000
PUBLIC_BASE_URL=
ALLOWED_ORIGINS=https://chatgpt.com,https://chat.openai.com
FORECAST_DAYS_LIMIT=5
CLOUDFLARE_TUNNEL_NAME=weather-info
CLOUDFLARE_TUNNEL_HOSTNAME=
OPENAI_APPS_DOCS_URL=https://developers.openai.com/apps-sdk/
OPENAI_APPS_DEPLOY_URL=https://developers.openai.com/apps-sdk/deploy
OPENAI_PLATFORM_APPS_URL=https://platform.openai.com
```

## Step 4: Run the app locally

Start the app from the `weather_info_app` folder:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Step 5: Verify local routes

Open these in your browser:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/healthz`
- `http://127.0.0.1:8000/connections`
- `http://127.0.0.1:8000/integration-guide`
- `http://127.0.0.1:8000/widget`

Optional FastAPI docs page:

- `http://127.0.0.1:8000/docs`

## Step 6: Expose the app with Cloudflare

This project uses Cloudflare as the recommended public HTTPS path.

### Option A: Quick test with a Cloudflare Tunnel command

If `cloudflared` is already installed, run:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Cloudflare will give you a temporary public HTTPS URL.

### Option B: Named tunnel with a fixed hostname

1. Create a Cloudflare Tunnel in your Cloudflare account.
2. Configure a public hostname such as `weather-info.your-domain.example`.
3. Copy [cloudflared.example.yml](./cloudflare/cloudflared.example.yml) and update:
   - `tunnel`
   - `credentials-file`
   - `hostname`
4. Start the tunnel with your updated config.
5. Set these values in `.env`:

```env
PUBLIC_BASE_URL=https://weather-info.your-domain.example
CLOUDFLARE_TUNNEL_HOSTNAME=weather-info.your-domain.example
```

6. Restart `uvicorn`.

## Step 7: Check the public HTTPS routes

After Cloudflare is working, verify:

- `https://your-public-url/`
- `https://your-public-url/healthz`
- `https://your-public-url/connections`
- `https://your-public-url/integration-guide`
- `https://your-public-url/widget`

## Step 8: Connect the app in ChatGPT

Once the app is publicly reachable over HTTPS, add this connector URL inside ChatGPT:

```text
https://your-public-url/mcp
```

This is the Apps SDK / MCP connection point for the Weather Info tool.

## Step 9: Use the OpenAI Apps references while integrating

Use these official references during integration:

- OpenAI Apps SDK docs:
  `https://developers.openai.com/apps-sdk/`
- OpenAI Apps deployment docs:
  `https://developers.openai.com/apps-sdk/deploy`
- OpenAI Platform:
  `https://platform.openai.com`

## Step 10: Test the app behavior

After the connector is added in ChatGPT, ask:

```text
What's the weather in Hyderabad for the next 3 days?
```

Expected behavior:

1. ChatGPT calls `get_weather_info`
2. The MCP server fetches geocoding data
3. The MCP server fetches forecast data
4. ChatGPT receives structured weather output
5. The widget can render real tool data instead of fallback demo content

## Step 10A: Test the endpoints in Postman

Postman is best for:

- `GET /`
- `GET /healthz`
- `GET /connections`
- `GET /integration-guide`
- `GET /widget`
- `POST /mcp`

Ready-made collection:

- [weather-info.postman_collection.json](C:\Users\owankh01\openai_apps\weather_info_app\postman\weather-info.postman_collection.json)
- [weather-info.postman_environment.json](C:\Users\owankh01\openai_apps\weather_info_app\postman\weather-info.postman_environment.json)

### Import the collection into Postman

1. Open Postman
2. Click `Import`
3. Select:
   - [weather-info.postman_collection.json](C:\Users\owankh01\openai_apps\weather_info_app\postman\weather-info.postman_collection.json)
   - [weather-info.postman_environment.json](C:\Users\owankh01\openai_apps\weather_info_app\postman\weather-info.postman_environment.json)
4. Update collection variables:
   - `base_url`
   - `public_url`

Recommended values:

```text
base_url=http://127.0.0.1:8000
public_url=https://your-public-url.example
```

After import, choose the `Weather Info Local` environment in Postman before sending requests.

### Postman test 1: Root endpoint

Method:

```text
GET
```

URL:

```text
http://127.0.0.1:8000/
```

Expected result:
- JSON with app name
- `mcp`
- `widget`
- `health`
- `inventory`

### Postman test 2: Health check

Method:

```text
GET
```

URL:

```text
http://127.0.0.1:8000/healthz
```

Expected result:

```json
{"status":"ok"}
```

### Postman test 3: Connection inventory

Method:

```text
GET
```

URL:

```text
http://127.0.0.1:8000/connections
```

Expected result:
- local routes
- external API URLs
- OpenAI Apps links
- Cloudflare hostname metadata

### Postman test 4: Integration guide

Method:

```text
GET
```

URL:

```text
http://127.0.0.1:8000/integration-guide
```

Expected result:
- numbered setup steps
- example run command
- public MCP connector guidance

### Postman test 5: Widget route

Method:

```text
GET
```

URL:

```text
http://127.0.0.1:8000/widget
```

Expected result:
- HTML response
- browser-style widget markup

### Postman test 6: MCP initialize request

This app uses Streamable HTTP MCP, so the `/mcp` route is a protocol endpoint, not a plain REST endpoint.
For Postman, start with an MCP initialize request.

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:8000/mcp
```

Headers:

```text
Content-Type: application/json
Accept: application/json, text/event-stream
```

Body:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": {
      "name": "Postman",
      "version": "1.0.0"
    }
  }
}
```

Expected result:
- JSON-RPC response
- server capabilities including tools support

### Postman test 7: MCP list tools

After initialize, send:

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:8000/mcp
```

Headers:

```text
Content-Type: application/json
Accept: application/json, text/event-stream
```

Body:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

Expected result:
- a tool list containing `get_weather_info`

### Postman test 8: MCP call tool

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:8000/mcp
```

Headers:

```text
Content-Type: application/json
Accept: application/json, text/event-stream
```

Body:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_weather_info",
    "arguments": {
      "location": "Hyderabad",
      "days": 3,
      "unit": "celsius"
    }
  }
}
```

Expected result:
- text content summary
- structured weather JSON

### Postman troubleshooting notes

- If `/mcp` does not behave like a normal REST endpoint, that is expected because it follows MCP JSON-RPC rules.
- If tool calls fail, check whether your machine can reach:
  - `https://geocoding-api.open-meteo.com`
  - `https://api.open-meteo.com`
- If public testing fails, confirm `PUBLIC_BASE_URL` and your Cloudflare hostname are correct.
- For browser-friendly checks, use `/`, `/healthz`, `/connections`, `/integration-guide`, and `/widget`.
- For protocol-level MCP debugging, ChatGPT or the MCP Inspector is often easier than Postman.

## Step 11: Review all connection points

The easiest way to inspect all major connections is:

- `GET /connections`
- `GET /integration-guide`

These routes list:

- local app URLs
- MCP connector URL
- widget URL
- Open-Meteo API connections
- OpenAI Apps docs links
- OpenAI Platform link
- Cloudflare hostname metadata

## Extra tools for smooth testing

If you want the smoothest validation flow, use:

1. Browser
   For `GET /`, `GET /healthz`, `GET /connections`, `GET /integration-guide`, and `GET /widget`

2. Postman
   For all HTTP routes, especially the JSON responses and simple MCP POST requests

3. ChatGPT
   For the full connector test using the public `/mcp` URL

4. MCP Inspector
   For the cleanest protocol-level debugging of MCP initialization, tools listing, and tool calls

## Notes

- The `get_weather_info` tool returns both text and structured JSON.
- The `/widget` page shows demo data if you open it directly in the browser.
- Real widget data appears when ChatGPT calls the MCP tool and passes tool output.
- ChatGPT needs a public `HTTPS` URL. Plain `localhost` is not enough for connector use.

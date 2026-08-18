# Weather Info: Complete Run Guide

This guide covers the complete workflow for the Weather Info FastAPI and MCP application:

1. Prepare the machine.
2. Create the Python environment.
3. Configure the application.
4. Run it locally.
5. Verify the HTTP and MCP endpoints.
6. Test the weather tool.
7. Deploy it to Render.
8. Connect the deployed MCP server to ChatGPT.
9. Stop, restart, update, and troubleshoot the application.

The application does not call the OpenAI API, so it does not require an OpenAI API key. It calls the public Open-Meteo geocoding and forecast APIs.

## MCP endpoint and transport security

The canonical Streamable HTTP endpoint is `/mcp`. The application internally maps that path to the mounted MCP application without returning an HTTP redirect.

DNS-rebinding protection remains enabled. Local hosts are allowed automatically, while the public hostname is derived from `PUBLIC_BASE_URL`. In production, set `PUBLIC_BASE_URL` to the exact HTTPS Render origin before testing the MCP endpoint.

## 1. Prerequisites

Install or confirm the following:

- Python 3.14
- Git, if the project will be deployed through GitHub
- Node.js and npm, only if MCP Inspector will be used
- A Render account, only for public deployment
- A ChatGPT account or workspace that permits Developer mode, only for the final connection
- Internet access to the Open-Meteo APIs

Check the local tools in PowerShell:

```powershell
python --version
git --version
node --version
npm --version
```

Expected Python version:

```text
Python 3.14.x
```

Node.js and npm are optional for normal server operation.

## 2. Open the project directory

Open PowerShell and change to the application directory:

```powershell
cd C:\Users\owankh01\openai_apps\weather_info_app
```

Confirm the current directory:

```powershell
Get-Location
Get-ChildItem
```

The directory must contain at least:

```text
app/
static/
requirements.txt
.env.example
render.yaml
```

Run all standard commands in this guide from `weather_info_app`, not from its parent directory.

## 3. Create and activate a virtual environment

Create a project-local virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, allow scripts only for the current terminal and try again:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Confirm that the virtual environment is active:

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

The executable path should end with:

```text
weather_info_app\.venv\Scripts\python.exe
```

## 4. Install dependencies

Upgrade pip and install the project dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Check the installed dependency set:

```powershell
python -m pip check
```

Expected result:

```text
No broken requirements found.
```

Run the automated regression tests:

```powershell
python -m unittest discover -s tests -v
```

The MCP transport tests should confirm that `/mcp` does not redirect, configured origins are accepted, and unknown hosts or origins are rejected.

## 5. Create the local configuration

Create `.env` from the tracked example:

```powershell
Copy-Item .env.example .env
```

Open `.env` in an editor and use these local values:

```dotenv
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

For local execution, leave `PUBLIC_BASE_URL` empty. The application will derive links from the current request host.

The `.env` file is ignored by Git. Do not commit environment-specific values or credentials.

## 6. Run the application locally

In the first PowerShell terminal, with the virtual environment active, run:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --env-file .env
```

Expected startup output includes a URL similar to:

```text
Uvicorn running on http://127.0.0.1:8000
```

Keep this terminal open while testing.

If port 8000 is already in use, either stop the existing process or use another port consistently:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001 --env-file .env
```

If starting from the parent `openai_apps` directory is unavoidable, use both explicit paths:

```powershell
uvicorn app.main:app --app-dir weather_info_app --reload --host 127.0.0.1 --port 8000 --env-file weather_info_app\.env
```

Do not run `python app/main.py`. This is an ASGI application and must be started with Uvicorn.

## 7. Verify the local HTTP routes

Open a second PowerShell terminal. Run:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/healthz
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/connections
Invoke-RestMethod http://127.0.0.1:8000/integration-guide
```

The health response must be:

```json
{"status":"ok"}
```

Open these pages in a browser:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/widget
```

The widget is currently a standalone preview. It is not registered as an MCP UI resource.

## 8. Verify the MCP protocol endpoint

### Recommended: MCP Inspector

Run MCP Inspector from a terminal with Node.js and npm available:

```powershell
npx @modelcontextprotocol/inspector@latest
```

In MCP Inspector:

1. Select `Streamable HTTP`.
2. Enter `http://127.0.0.1:8000/mcp`.
3. Connect to the server.
4. Confirm initialization succeeds.
5. Open the tools list.
6. Confirm `get_weather_info` is present.

The request should receive the MCP response directly with no HTTP redirect.

### Optional: initialize with PowerShell

The following request checks MCP initialization without MCP Inspector:

```powershell
$McpHeaders = @{
    Accept = "application/json, text/event-stream"
    "MCP-Protocol-Version" = "2025-06-18"
}

$InitializeBody = @{
    jsonrpc = "2.0"
    id = 1
    method = "initialize"
    params = @{
        protocolVersion = "2025-06-18"
        capabilities = @{}
        clientInfo = @{
            name = "weather-info-manual-check"
            version = "1.0"
        }
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/mcp `
    -Headers $McpHeaders `
    -ContentType "application/json" `
    -Body $InitializeBody
```

Expected result fields include:

```text
result.protocolVersion
result.serverInfo.name
result.capabilities.tools
```

## 9. Call the weather tool

In MCP Inspector, select `get_weather_info` and call it with:

```json
{
  "location": "Hyderabad, India",
  "days": 3,
  "unit": "celsius"
}
```

Confirm the response contains:

- A text summary
- The resolved location and coordinates
- Current weather data
- Three forecast entries
- Celsius as the unit

Repeat with Fahrenheit:

```json
{
  "location": "London, United Kingdom",
  "days": 2,
  "unit": "fahrenheit"
}
```

Test representative edge cases:

```json
{"location":"Hyderabad","days":1,"unit":"celsius"}
```

```json
{"location":"Hyderabad","days":20,"unit":"celsius"}
```

```json
{"location":"this-place-should-not-exist-12345","days":3,"unit":"celsius"}
```

The 20-day request should be clamped to `FORECAST_DAYS_LIMIT`. An unknown location should return a tool error rather than fabricated weather data.

## 10. Optional Postman verification

Import these files into Postman:

```text
postman/weather-info.postman_collection.json
postman/weather-info.postman_environment.json
```

Select the `Weather Info Local` environment and run the requests.

The MCP requests are JSON-RPC calls, not conventional REST requests.

## 11. Stop and restart the local application

To stop Uvicorn, return to its terminal and press:

```text
Ctrl+C
```

Deactivate the virtual environment when finished:

```powershell
deactivate
```

To start the application later:

```powershell
cd C:\Users\owankh01\openai_apps\weather_info_app
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --env-file .env
```

## 12. Prepare the project for Render

Do not begin this phase until:

- All local HTTP checks pass.
- MCP Inspector can initialize the local server.
- `get_weather_info` returns a representative result.
- `PUBLIC_BASE_URL` will be set to the exact Render HTTPS origin.

Check Git state:

```powershell
git status
git branch --show-current
```

Commit and push the deployable files:

```powershell
git add .
git commit -m "Prepare Weather Info deployment"
git push origin main
```

Before committing, verify that `.env` is not staged:

```powershell
git status --short
git check-ignore -v .env
```

## 13. Deploy to Render

### Option A: use the included Blueprint

1. Sign in to Render.
2. Create a new Blueprint.
3. Select the GitHub repository containing `weather_info_app` as its repository root.
4. Confirm that Render detects `render.yaml`.
5. Review the proposed `weather-info` web service.
6. Deploy it.

Do not create a Blueprint if it would unintentionally duplicate an existing manually configured service.

### Option B: configure a web service manually

Use these values:

| Setting | Value |
| --- | --- |
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health-check path | `/healthz` |
| Instance type | Free for testing, or paid for an always-on service |

Watch the deployment logs until the service starts and Render reports a healthy deployment.

## 14. Configure the production environment

Copy the exact Render origin, for example:

```text
https://YOUR_RENDER_SERVICE.onrender.com
```

In the Render service environment settings, configure:

```text
APP_NAME=Weather Info
PUBLIC_BASE_URL=https://YOUR_RENDER_SERVICE.onrender.com
ALLOWED_ORIGINS=https://chatgpt.com,https://chat.openai.com
FORECAST_DAYS_LIMIT=5
```

Do not add `/mcp` to `PUBLIC_BASE_URL`. Do not add a trailing route.

Save the environment changes and redeploy the service.

## 15. Verify the Render deployment

In PowerShell, set the exact service origin:

```powershell
$RenderUrl = "https://YOUR_RENDER_SERVICE.onrender.com"
```

Check the public HTTP routes:

```powershell
Invoke-RestMethod "$RenderUrl/healthz"
Invoke-RestMethod "$RenderUrl/"
Invoke-RestMethod "$RenderUrl/connections"
Invoke-RestMethod "$RenderUrl/integration-guide"
```

Open:

```text
https://YOUR_RENDER_SERVICE.onrender.com/docs
https://YOUR_RENDER_SERVICE.onrender.com/widget
```

Then test the public MCP endpoint with MCP Inspector:

```text
https://YOUR_RENDER_SERVICE.onrender.com/mcp
```

Confirm all three operations:

1. MCP initialization
2. Tool discovery
3. A real `get_weather_info` tool call

If MCP Inspector receives `421 Invalid Host header`, confirm that `PUBLIC_BASE_URL` exactly matches the public Render origin, then save the environment and redeploy. Do not proceed to ChatGPT until initialization succeeds.

## 16. Connect the MCP server to ChatGPT

The public MCP endpoint must be reachable over HTTPS and must pass MCP Inspector before completing this phase.

### Enable Developer mode

In ChatGPT:

1. Open `Settings`.
2. Select `Security and login`.
3. Turn on `Developer mode`.

Developer mode availability can depend on the account and workspace policy.

### Add the MCP connection

1. Open ChatGPT Plugins.
2. Select the plus button.
3. Enter a user-facing name such as `Weather Info`.
4. Enter a description such as `Get current weather and a short forecast for a location.`
5. Under `Connection`, choose a public endpoint.
6. Enter the verified public MCP URL, including the MCP path.
7. Create the connection.
8. Confirm ChatGPT discovers `get_weather_info` and its input schema.

Use the exact URL that succeeded in MCP Inspector:

```text
https://YOUR_RENDER_SERVICE.onrender.com/mcp
```

Official OpenAI documentation describes `/mcp` as the typical Streamable HTTP path.

### Run an end-to-end test

Start a new ChatGPT conversation, enable the Weather Info connection from the tools menu, and ask:

```text
What is the weather in Hyderabad, India for the next 3 days in Celsius?
```

Confirm that:

1. ChatGPT selects `get_weather_info`.
2. The tool receives the location, day count, and unit.
3. The service calls Open-Meteo.
4. The response contains current weather and forecast data.
5. ChatGPT presents the result to the user.

Also test:

- A one-day forecast
- Fahrenheit output
- An unknown location
- A request exceeding the configured day limit
- A non-weather question, which should not call the tool

## 17. Deploy future updates

For each application or tool change:

1. Activate the virtual environment.
2. Run the application locally.
3. Verify `/healthz` and the affected routes.
4. Test `get_weather_info` with MCP Inspector.
5. Commit the change.
6. Push it to `main`.
7. Wait for Render's automatic deployment.
8. Verify the public HTTP and MCP endpoints.
9. Refresh the connection metadata in ChatGPT.
10. Start a new conversation and repeat the affected prompts.

Typical Git commands:

```powershell
git status
git add .
git commit -m "Describe the Weather Info update"
git push origin main
```

## 18. Troubleshooting

### `python` is not recognized

Install Python 3.14, enable the option that adds Python to `PATH`, and open a new PowerShell terminal.

### Virtual-environment activation is blocked

Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### `No module named 'app'`

Run Uvicorn from `weather_info_app`:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --env-file .env
```

Do not use `python app/main.py`.

### `.env` values are ignored

Confirm the command contains:

```text
--env-file .env
```

Also confirm the terminal's current directory is `weather_info_app`.

### Port 8000 is already in use

Find the process:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

Stop the application that owns the port or run Weather Info on a different port.

### `/mcp` returns 307

Restart the application with the latest code. The canonical-path middleware should route `/mcp` internally without returning a redirect.

### Public `/mcp` returns 421

Confirm that `PUBLIC_BASE_URL` contains the exact public HTTPS origin, without `/mcp`, then save the Render environment and redeploy. The application derives its permitted public MCP Host header from this value.

### Weather calls fail

Confirm the machine or Render service can reach:

```text
https://geocoding-api.open-meteo.com/v1/search
https://api.open-meteo.com/v1/forecast
```

Check the Uvicorn or Render logs for the upstream HTTP status.

### A location is not found

Use a more specific location, for example:

```text
Hyderabad, India
Springfield, Illinois, United States
```

### Render cannot detect an open port

Confirm the start command is exactly:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Render reports `No module named 'app'`

Confirm that the Render repository root is the `weather_info_app` directory and that the start command uses Uvicorn.

### Generated public links use the wrong hostname

Set `PUBLIC_BASE_URL` to the exact HTTPS Render origin without `/mcp` or any other route, save it, and redeploy.

### ChatGPT cannot connect

Verify, in this order:

1. `GET /healthz` succeeds publicly.
2. MCP Inspector can initialize the public endpoint.
3. MCP Inspector can list tools.
4. MCP Inspector can call `get_weather_info`.
5. The endpoint does not return 307 or 421.
6. Developer mode is enabled and permitted by workspace policy.
7. The ChatGPT connection is refreshed after deployment changes.

### The first Render request is slow

Free Render services can sleep when inactive. Call `/healthz`, wait for the service to wake, and retry the MCP connection.

## 19. Final completion checklist

- [ ] Python 3.14 is installed.
- [ ] The virtual environment is active.
- [ ] Dependencies are installed and `pip check` passes.
- [ ] `.env` exists and is not tracked by Git.
- [ ] Uvicorn starts without errors.
- [ ] All local HTTP routes respond.
- [ ] Local MCP initialization succeeds at `/mcp` without a redirect.
- [ ] `get_weather_info` succeeds in Celsius and Fahrenheit.
- [ ] `PUBLIC_BASE_URL` contains the exact production origin.
- [ ] The Render health check passes.
- [ ] The public MCP endpoint initializes and lists tools.
- [ ] A public weather tool call succeeds.
- [ ] ChatGPT discovers `get_weather_info`.
- [ ] The end-to-end ChatGPT prompt succeeds.

## References

- [OpenAI: Connect and test your plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [OpenAI: Build an MCP server](https://developers.openai.com/plugins/build/mcp-server)
- [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector)
- [Open-Meteo API](https://open-meteo.com/en/docs)
- [Render FastAPI deployment](https://render.com/docs/deploy-fastapi)
- [Project README](./README.md)
- [Focused Render setup](./render-setup.md)

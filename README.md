# Weather Info MCP Application

Weather Info is a Python MCP application that lets ChatGPT retrieve current weather and a short forecast for a city, state, or country.

The application uses:

- FastAPI for the HTTP host
- FastMCP from the Python MCP SDK
- Open-Meteo for geocoding and weather data
- Pydantic for structured tool results
- Heroku for the public HTTPS deployment

No OpenAI API key is required. ChatGPT connects to the public MCP endpoint and invokes the tool; the server itself does not call the OpenAI API.

## Runtime flow

```text
User prompt in ChatGPT
        |
        v
ChatGPT MCP connection
        |
        v
POST https://YOUR_HEROKU_APP.herokuapp.com/mcp
        |
        v
FastMCP tool: get_weather_info
        |
        +--> Open-Meteo Geocoding API
        |
        +--> Open-Meteo Forecast API
        |
        v
WeatherToolResponse
        |
        v
Text summary + structuredContent returned to ChatGPT
```

## Available endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Application metadata and route links |
| `GET /healthz` | Health check |
| `GET /connections` | Internal and external connection inventory |
| `GET /integration-guide` | Machine-readable execution and deployment guide |
| `GET /widget` | Standalone weather widget preview |
| `/mcp` | Streamable HTTP MCP endpoint |
| `GET /docs` | FastAPI API documentation |

The MCP server exposes one tool:

```text
get_weather_info(location: string, days: integer = 3, unit: "celsius" | "fahrenheit")
```

`days` is clamped between `1` and `FORECAST_DAYS_LIMIT`.

> The current `/widget` route is a standalone preview. It is not registered as an MCP UI resource, so the primary ChatGPT workflow uses the tool's text and structured output.

## Project structure

```text
weather_info_app/
|-- .env.example
|-- .python-version
|-- Procfile
|-- README.md
|-- heroku-setup.md
|-- requirements.txt
|-- app/
|   |-- config.py
|   |-- main.py
|   |-- mcp_server.py
|   |-- models.py
|   `-- services/
|       `-- weather_client.py
|-- postman/
|   |-- weather-info.postman_collection.json
|   `-- weather-info.postman_environment.json
|-- static/
|   `-- widget.html
`-- cloudflare/
    `-- cloudflared.example.yml
```

Heroku is the primary deployment workflow. The Cloudflare files are retained only as an optional alternative.

## Complete execution workflow

### Phase 1: Prepare the local environment

#### Step 1: Open a terminal in the project directory

The working directory matters. Both `app/` and `.env` are inside `weather_info_app`, so change into that directory before using the standard startup command.

PowerShell:

```powershell
cd C:\Users\owankh01\openai_apps\weather_info_app
```

Command Prompt:

```bat
cd /d C:\Users\owankh01\openai_apps\weather_info_app
```

Confirm the prompt ends in `weather_info_app`:

```text
C:\Users\owankh01\openai_apps\weather_info_app>
```

#### Step 2: Confirm Python

The project selects Python 3.14 through `.python-version`.

```powershell
python --version
```

#### Step 3: Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
```

#### Step 4: Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5: Create the local environment file

```powershell
Copy-Item .env.example .env
```

For local execution, leave `PUBLIC_BASE_URL` empty. Review the remaining defaults in `.env`:

```env
APP_NAME=Weather Info
HOST=127.0.0.1
PORT=8000
PUBLIC_BASE_URL=
ALLOWED_ORIGINS=https://chatgpt.com,https://chat.openai.com
FORECAST_DAYS_LIMIT=5
```

The `.env` file is ignored by Git. Do not commit secrets or production credentials to it.

### Phase 2: Run and verify locally

#### Step 6: Start the application

Run this command from `weather_info_app` with the virtual environment active:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --env-file .env
```

If you intentionally remain in the parent `C:\Users\owankh01\openai_apps` directory, provide both paths explicitly instead:

```bat
uvicorn app.main:app --app-dir weather_info_app --reload --host 127.0.0.1 --port 8000 --env-file weather_info_app\.env
```

Do not mix the two forms. Running the standard command from the parent directory causes `.env` lookup and `app.main` import failures.

Keep this terminal running.

Expected startup behavior:

- FastAPI starts on `http://127.0.0.1:8000`.
- The MCP Streamable HTTP application is mounted at `/mcp`.
- A shared `WeatherClient` is created for outbound Open-Meteo calls.
- Static widget assets are served from `/static` and `/widget`.

#### Step 7: Verify the HTTP routes

Open a second PowerShell terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/healthz
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/connections
Invoke-RestMethod http://127.0.0.1:8000/integration-guide
```

Expected health response:

```json
{"status":"ok"}
```

Open these browser pages:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/widget`

#### Step 8: Test the MCP tool with MCP Inspector

Node.js and npm are required only for this optional inspector step.

```powershell
npx @modelcontextprotocol/inspector@latest
```

In MCP Inspector:

1. Select `Streamable HTTP` as the transport.
2. Enter `http://127.0.0.1:8000/mcp`.
3. Connect and confirm initialization succeeds.
4. List tools and select `get_weather_info`.
5. Call it with:

```json
{
  "location": "Hyderabad",
  "days": 3,
  "unit": "celsius"
}
```

Confirm that the result contains:

- A natural-language weather summary
- `location` with coordinates
- `current` weather data
- A three-day `forecast`

#### Step 9: Optionally test with Postman

Import:

- `postman/weather-info.postman_collection.json`
- `postman/weather-info.postman_environment.json`

Select the `Weather Info Local` environment, then run the HTTP requests. The `/mcp` requests are JSON-RPC protocol calls; `/mcp` is not a conventional REST endpoint or browser page.

### Phase 3: Deploy to Heroku

#### Step 10: Install and authenticate the Heroku CLI

Confirm the Heroku CLI and sign in:

```powershell
heroku --version
heroku login
```

#### Step 11: Commit the deployable project

Heroku Git deploys committed files:

```powershell
git add .
git commit -m "Prepare Weather Info for Heroku"
```

The repository includes:

- `Procfile`, which starts Uvicorn on Heroku's `$PORT`
- `.python-version`, which selects Python 3.14
- `requirements.txt`, which installs application dependencies

#### Step 12: Create the Heroku application

Choose a globally unique app name:

```powershell
heroku create YOUR_HEROKU_APP
heroku apps:info -a YOUR_HEROKU_APP
```

Record the exact HTTPS web URL shown by Heroku. The hostname can include an additional generated suffix.

#### Step 13: Configure production environment variables

Replace the placeholders with the actual app name and exact public URL:

```powershell
heroku config:set PUBLIC_BASE_URL=https://YOUR_ACTUAL_HEROKU_HOSTNAME -a YOUR_HEROKU_APP
heroku config:set APP_NAME="Weather Info" -a YOUR_HEROKU_APP
heroku config:set ALLOWED_ORIGINS=https://chatgpt.com,https://chat.openai.com -a YOUR_HEROKU_APP
heroku config:set FORECAST_DAYS_LIMIT=5 -a YOUR_HEROKU_APP
```

Review the configuration without placing credentials in the repository:

```powershell
heroku config -a YOUR_HEROKU_APP
```

#### Step 14: Deploy the main branch

```powershell
git push heroku main
```

If the current local branch has another name, push it to Heroku's `main` branch:

```powershell
git push heroku HEAD:main
```

#### Step 15: Check the web process and logs

```powershell
heroku ps -a YOUR_HEROKU_APP
heroku logs --tail -a YOUR_HEROKU_APP
```

The web process must be `up`. Press `Ctrl+C` to stop following the logs.

### Phase 4: Verify the public deployment

#### Step 16: Test every public route

Set the exact URL in the current PowerShell session:

```powershell
$HerokuUrl = "https://YOUR_ACTUAL_HEROKU_HOSTNAME"
Invoke-RestMethod "$HerokuUrl/healthz"
Invoke-RestMethod "$HerokuUrl/"
Invoke-RestMethod "$HerokuUrl/connections"
Invoke-RestMethod "$HerokuUrl/integration-guide"
```

Open:

- `https://YOUR_ACTUAL_HEROKU_HOSTNAME/docs`
- `https://YOUR_ACTUAL_HEROKU_HOSTNAME/widget`

#### Step 17: Test the production MCP endpoint

Restart MCP Inspector if necessary:

```powershell
npx @modelcontextprotocol/inspector@latest
```

Connect with Streamable HTTP using:

```text
https://YOUR_ACTUAL_HEROKU_HOSTNAME/mcp
```

Repeat the `get_weather_info` call from Step 8. Do not proceed to ChatGPT until initialization, tool discovery, and a representative tool call all succeed against Heroku.

### Phase 5: Connect the MCP server to ChatGPT

#### Step 18: Enable developer mode

In ChatGPT:

1. Open `Settings`.
2. Select `Security and login`.
3. Turn on `Developer mode`.

Developer mode availability can depend on the account and workspace policy.

#### Step 19: Add the public MCP connection

1. Open ChatGPT Plugins.
2. Select the plus button.
3. Enter a user-facing name such as `Weather Info`.
4. Enter a short description of the weather lookup capability.
5. Choose a public endpoint under `Connection`.
6. Enter the full URL, including `/mcp`:

```text
https://YOUR_ACTUAL_HEROKU_HOSTNAME/mcp
```

7. Create the connection.
8. Confirm that ChatGPT discovers `get_weather_info` and its input schema.

#### Step 20: Run an end-to-end ChatGPT test

Start a new conversation, enable the Weather Info MCP connection from the tools menu, and ask:

```text
What is the weather in Hyderabad for the next 3 days in Celsius?
```

Expected workflow:

1. ChatGPT selects `get_weather_info`.
2. The tool receives `location`, `days`, and `unit`.
3. The server resolves Hyderabad through Open-Meteo geocoding.
4. The server retrieves current conditions and a three-day forecast.
5. ChatGPT receives text content and structured JSON.
6. ChatGPT presents the weather result to the user.

Also test:

- A one-day forecast
- Fahrenheit output
- An unknown location
- A request exceeding the configured day limit
- A question unrelated to weather, which should not invoke the tool

### Phase 6: Deploy future updates

For each code or MCP metadata change:

1. Run and test the application locally.
2. Test `get_weather_info` with MCP Inspector.
3. Commit the changes.
4. Deploy them with `git push heroku main`.
5. Verify `/healthz` and the production `/mcp` endpoint.
6. Open the connection in ChatGPT Plugins and select `Refresh`.
7. Start a new conversation and repeat the affected test prompts.

## Troubleshooting

| Problem | Check |
| --- | --- |
| `python` is not recognized | Install Python 3.14 and reopen PowerShell. |
| PowerShell blocks virtual-environment activation | Run `Set-ExecutionPolicy -Scope Process Bypass`. |
| Local settings are ignored | Start Uvicorn with `--env-file .env`. |
| `/healthz` fails locally | Check the Uvicorn terminal for import or dependency errors. |
| Weather calls fail | Confirm the machine or Heroku app can reach both Open-Meteo APIs. |
| `/mcp` looks broken in a browser | Test it with MCP Inspector; it is an MCP protocol endpoint. |
| Heroku build fails | Review `heroku logs --tail` and confirm the root contains `requirements.txt`, `.python-version`, and `Procfile`. |
| Heroku web process is down | Run `heroku ps` and inspect startup logs. |
| Generated links show the wrong host | Set `PUBLIC_BASE_URL` to the exact Heroku HTTPS origin without `/mcp`. |
| ChatGPT cannot connect | Verify the Heroku `/mcp` URL with MCP Inspector first, then refresh the ChatGPT connection. |
| A location returns no result | Try a more specific value such as `Hyderabad, India`. |

## Important operational notes

- Keep the Heroku MCP endpoint publicly reachable over HTTPS.
- Do not put `/mcp` inside `PUBLIC_BASE_URL`; the application appends route paths itself.
- Store production values in Heroku config vars, not `.env` or Git.
- The service currently has no user authentication because it exposes public weather data only.
- Open-Meteo availability and outbound network access are required for tool calls.
- Use Heroku logs to diagnose initialization and tool failures.

## Reference documentation

- [Build an MCP server](https://developers.openai.com/plugins/build/mcp-server)
- [Connect and test an MCP server in ChatGPT](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [Heroku Procfile](https://devcenter.heroku.com/articles/procfile)
- [Heroku Python runtimes](https://devcenter.heroku.com/articles/python-runtimes)
- [Deploying to Heroku with Git](https://devcenter.heroku.com/articles/git)
- [Open-Meteo API](https://open-meteo.com/en/docs)

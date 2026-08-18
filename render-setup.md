# Render Deployment

This guide deploys the Weather Info FastAPI and MCP application as a Render web service with a public HTTPS endpoint.

## Required service settings

| Setting | Value |
| --- | --- |
| Runtime | `Python 3` |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health-check path | `/healthz` |
| Instance type | `Free` for testing, or a paid instance for always-on use |

Do not use `python app/main.py` as the start command. Direct execution breaks package imports such as `from app.config import settings` and does not start an ASGI server.

## Option A: Correct the existing Render service

1. Open the service in the Render Dashboard.
2. Open `Settings`.
3. Under `Build & Deploy`, keep the build command as:

   ```text
   pip install -r requirements.txt
   ```

4. Replace the start command with:

   ```text
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

5. Set the health-check path to `/healthz`.
6. Save the changes.
7. Select `Manual Deploy`, then `Deploy latest commit`.

The dependency build already succeeded, so clearing the build cache is normally unnecessary for a start-command correction.

## Option B: Create a service from render.yaml

The repository includes a root-level `render.yaml` Blueprint with the runtime, build, start, health-check, auto-deploy, and environment settings.

1. Push the latest repository commit to GitHub.
2. In Render, create a new Blueprint.
3. Select this GitHub repository.
4. Confirm Render detects `render.yaml`.
5. Review the proposed `weather-info` free web service.
6. Deploy the Blueprint.

Do not use this option to duplicate an existing service unless you intend to create a second deployment.

## Configure the public URL

After the first successful deployment, copy the exact service origin shown by Render:

```text
https://YOUR_RENDER_SERVICE.onrender.com
```

In the service's `Environment` settings, add:

```text
PUBLIC_BASE_URL=https://YOUR_RENDER_SERVICE.onrender.com
```

Do not include `/mcp` in `PUBLIC_BASE_URL`. Save the environment change and redeploy the service.

## Verify the deployment

Open these routes:

```text
https://YOUR_RENDER_SERVICE.onrender.com/
https://YOUR_RENDER_SERVICE.onrender.com/healthz
https://YOUR_RENDER_SERVICE.onrender.com/connections
https://YOUR_RENDER_SERVICE.onrender.com/integration-guide
https://YOUR_RENDER_SERVICE.onrender.com/widget
```

Expected health response:

```json
{"status":"ok"}
```

Test the production MCP endpoint with MCP Inspector using Streamable HTTP:

```text
https://YOUR_RENDER_SERVICE.onrender.com/mcp
```

Confirm initialization, tool discovery, and a `get_weather_info` call all succeed before connecting ChatGPT.

## Connect ChatGPT

Use this public MCP connection URL:

```text
https://YOUR_RENDER_SERVICE.onrender.com/mcp
```

After changing tool metadata or behavior, push the commit, wait for Render's automatic deployment, verify `/mcp`, refresh the connection in ChatGPT, and retest in a new conversation.

## Troubleshooting

- `ModuleNotFoundError: No module named 'app'`: replace `python app/main.py` with the required Uvicorn start command.
- Port binding failure: confirm the start command binds to `0.0.0.0` and uses `$PORT`.
- Build failure: confirm `requirements.txt` is in the repository root selected by Render.
- Health-check failure: verify `/healthz` locally and inspect the Render event logs.
- Wrong generated links: set `PUBLIC_BASE_URL` to the exact Render origin without a trailing route.
- MCP connection failure: verify the production `/mcp` URL with MCP Inspector before testing ChatGPT.
- Slow first request on the free instance: wait for the service to wake, verify `/healthz`, and retry.

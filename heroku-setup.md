# Heroku Deployment

This guide deploys the Weather Info FastAPI and MCP application to a permanent public HTTPS URL on Heroku.

## Prerequisites

- A Heroku account
- Git and the Heroku CLI installed
- This project committed to the `main` branch

Run every command below from the `weather_info_app` directory.

## 1. Verify the Heroku files

Heroku uses these root-level files:

- `requirements.txt` installs the Python dependencies.
- `.python-version` selects the Python runtime.
- `Procfile` starts Uvicorn on Heroku's dynamically assigned `$PORT`.

The web process is:

```text
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 2. Sign in

```powershell
heroku login
```

## 3. Create the Heroku app

Heroku app names are globally unique. Replace the placeholder with an available name:

```powershell
heroku create YOUR_HEROKU_APP
```

The command creates the app and adds a Git remote named `heroku`.

## 4. Configure environment variables

Copy the exact public HTTPS URL printed by `heroku create`, then set it as `PUBLIC_BASE_URL`:

```powershell
heroku config:set PUBLIC_BASE_URL=https://YOUR_HEROKU_APP.herokuapp.com -a YOUR_HEROKU_APP
heroku config:set ALLOWED_ORIGINS=https://chatgpt.com,https://chat.openai.com -a YOUR_HEROKU_APP
heroku config:set FORECAST_DAYS_LIMIT=5 -a YOUR_HEROKU_APP
```

Use the exact Heroku URL even if it contains an additional generated suffix. Heroku config vars replace the local `.env` file in production.

## 5. Deploy

```powershell
git push heroku main
```

For later changes, commit them and run the same push command again.

## 6. Check the deployment

```powershell
heroku ps -a YOUR_HEROKU_APP
heroku logs --tail -a YOUR_HEROKU_APP
```

Verify these HTTPS routes in a browser or Postman:

```text
https://YOUR_HEROKU_APP.herokuapp.com/
https://YOUR_HEROKU_APP.herokuapp.com/healthz
https://YOUR_HEROKU_APP.herokuapp.com/connections
https://YOUR_HEROKU_APP.herokuapp.com/integration-guide
https://YOUR_HEROKU_APP.herokuapp.com/widget
```

## 7. Connect ChatGPT

Use the public MCP URL in the ChatGPT connector configuration:

```text
https://YOUR_HEROKU_APP.herokuapp.com/mcp
```

The app must remain publicly reachable over HTTPS for ChatGPT to initialize the MCP connection and call `get_weather_info`.

## Troubleshooting

- Check `heroku logs --tail` when the app fails to start.
- Confirm `PUBLIC_BASE_URL` uses `https://` and has no trailing `/mcp` path.
- Confirm the `web` dyno is running with `heroku ps`.
- Confirm Heroku can reach the Open-Meteo geocoding and forecast APIs.
- Use `/healthz` to distinguish app startup problems from MCP protocol problems.

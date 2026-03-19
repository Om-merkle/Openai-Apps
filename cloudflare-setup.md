# Cloudflare Setup

This guide shows the exact `cloudflared` commands to expose the local `Weather Info` app from this machine:

- local project path:
  `C:\Users\owankh01\openai_apps\weather_info_app`
- local app URL:
  `http://127.0.0.1:8000`

Before you start, replace these placeholders with your real values:

- `YOUR_DOMAIN`
- `YOUR_CF_TUNNEL_NAME`
- `YOUR_HOSTNAME`

Example values:

- `YOUR_DOMAIN` -> `example.com`
- `YOUR_CF_TUNNEL_NAME` -> `weather-info`
- `YOUR_HOSTNAME` -> `weather-info.example.com`

## Step 1: Start the app locally

Open PowerShell in the project folder:

```powershell
cd C:\Users\owankh01\openai_apps\weather_info_app
.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Keep this terminal running.

## Step 2: Check whether `cloudflared` is installed

In a new PowerShell window:

```powershell
cloudflared --version
```

If that works, continue.

## Step 3: Log in to Cloudflare

```powershell
cloudflared tunnel login
```

This opens a browser so you can choose your Cloudflare account and zone.

## Step 4: Quick temporary public URL

If you only want a temporary HTTPS URL for testing, run:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Cloudflare will print a temporary public HTTPS URL.

Use that URL as:

```text
https://temporary-url.trycloudflare.com/mcp
```

This is good for quick testing, but not for a stable ChatGPT connector.

## Step 5: Create a named tunnel

Create a persistent tunnel:

```powershell
cloudflared tunnel create YOUR_CF_TUNNEL_NAME
```

Example:

```powershell
cloudflared tunnel create weather-info
```

Cloudflare will create credentials in your `.cloudflared` folder, usually:

```text
C:\Users\owankh01\.cloudflared\
```

## Step 6: Route your hostname to the tunnel

Create the DNS route:

```powershell
cloudflared tunnel route dns YOUR_CF_TUNNEL_NAME YOUR_HOSTNAME
```

Example:

```powershell
cloudflared tunnel route dns weather-info weather-info.example.com
```

## Step 7: Create the Cloudflare config file

Create or edit this file:

```text
C:\Users\owankh01\.cloudflared\config.yml
```

Use this template:

```yaml
tunnel: YOUR_CF_TUNNEL_NAME
credentials-file: C:\Users\owankh01\.cloudflared\YOUR_TUNNEL_ID.json

ingress:
  - hostname: YOUR_HOSTNAME
    service: http://127.0.0.1:8000
  - service: http_status:404
```

Important:
- replace `YOUR_TUNNEL_ID.json` with the real file created by `cloudflared tunnel create`
- replace `YOUR_HOSTNAME` with your real public hostname

You can also use the example file in the project:

- [cloudflared.example.yml](C:\Users\owankh01\openai_apps\weather_info_app\cloudflare\cloudflared.example.yml)

## Step 8: Run the named tunnel

```powershell
cloudflared tunnel run YOUR_CF_TUNNEL_NAME
```

Example:

```powershell
cloudflared tunnel run weather-info
```

Keep this terminal running while you test.

## Step 9: Update the app `.env`

Edit:

- [`.env`](C:\Users\owankh01\openai_apps\weather_info_app\.env)

Set:

```env
PUBLIC_BASE_URL=https://YOUR_HOSTNAME
CLOUDFLARE_TUNNEL_NAME=YOUR_CF_TUNNEL_NAME
CLOUDFLARE_TUNNEL_HOSTNAME=YOUR_HOSTNAME
```

Example:

```env
PUBLIC_BASE_URL=https://weather-info.example.com
CLOUDFLARE_TUNNEL_NAME=weather-info
CLOUDFLARE_TUNNEL_HOSTNAME=weather-info.example.com
```

Then restart the FastAPI app:

```powershell
cd C:\Users\owankh01\openai_apps\weather_info_app
.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Step 10: Verify the public routes

Open these URLs:

```text
https://YOUR_HOSTNAME/
https://YOUR_HOSTNAME/healthz
https://YOUR_HOSTNAME/connections
https://YOUR_HOSTNAME/integration-guide
https://YOUR_HOSTNAME/widget
```

## Step 11: Connect it in ChatGPT

Use this connector URL in ChatGPT:

```text
https://YOUR_HOSTNAME/mcp
```

Example:

```text
https://weather-info.example.com/mcp
```

## Optional useful commands

List tunnels:

```powershell
cloudflared tunnel list
```

Get tunnel info:

```powershell
cloudflared tunnel info YOUR_CF_TUNNEL_NAME
```

Delete a tunnel:

```powershell
cloudflared tunnel delete YOUR_CF_TUNNEL_NAME
```

## Notes

- Run the FastAPI app and `cloudflared` in separate terminals.
- The ChatGPT connector requires a public `HTTPS` URL.
- A named tunnel is better than a temporary URL if you want a stable connector.

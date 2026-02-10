# How to Run the Windows Agent (Milestone 1)

This guide is for running the Windows Agent on your Windows PC.

## 1) Install Python
1. Install **Python 3.11+** from python.org.
2. During install, check **Add Python to PATH**.

## 2) Open Terminal in the repo
1. Open PowerShell.
2. Navigate to the project folder.

## 3) Install the Windows Agent
```powershell
cd windows-agent
python -m pip install --upgrade pip
python -m pip install -e .
```

## 4) Run the agent
Default WebSocket server port is **8765**.
Default phone web UI port is **8766**.
```powershell
python -m windows_agent
```

A pairing code window should appear. Keep the app running.

## 5) Open the phone web UI
1. Make sure your phone is on the same local network as the PC.
2. Open your phone browser to:
   - `http://<pc-ip>:8766`
3. The page auto-connects to `ws://<pc-ip>:8765`.

## 6) Pair your device
1. Enter the 6-digit code shown in the Windows pairing window.
2. Tap **Pair** (this sends `pair.request` then `pair.confirm`).
3. If valid, the agent responds with `pair.result` success and trusts your `device_id`.

## 7) Optional configuration
You can override settings with CLI args or env vars:
- `--port` or `WINDOWS_AGENT_PORT`
- `--host` or `WINDOWS_AGENT_HOST`
- `--trusted-registry` or `WINDOWS_AGENT_TRUSTED_REGISTRY`
- `--audit-log` or `WINDOWS_AGENT_AUDIT_LOG`
- `--rate-limit-per-sec` or `WINDOWS_AGENT_RATE_LIMIT`
- `--no-pairing-window` to disable the tkinter window (headless/testing)
- `--no-web-ui` to disable static phone UI hosting
- `--web-ui-host` or `WINDOWS_AGENT_WEB_UI_HOST`
- `--web-ui-port` or `WINDOWS_AGENT_WEB_UI_PORT`

Example:
```powershell
python -m windows_agent --port 9000 --web-ui-port 9001 --trusted-registry .\trusted_devices.json
```

## 8) Files created by the agent
- `trusted_devices.json` — trusted paired devices.
- `audit.log` — timestamped actions (`device_id` + action).

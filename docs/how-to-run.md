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
Default server port is **8765**.
```powershell
python -m windows_agent
```

A pairing code window should appear. Keep the app running.

## 5) Pair your device
1. In your controller app, send `pair.request`.
2. Confirm with `pair.confirm` using the 6-digit code shown.
3. If valid, the agent responds with `pair.result` success and trusts your `device_id`.

## 6) Optional configuration
You can override settings with CLI args or env vars:
- `--port` or `WINDOWS_AGENT_PORT`
- `--host` or `WINDOWS_AGENT_HOST`
- `--trusted-registry` or `WINDOWS_AGENT_TRUSTED_REGISTRY`
- `--audit-log` or `WINDOWS_AGENT_AUDIT_LOG`
- `--rate-limit-per-sec` or `WINDOWS_AGENT_RATE_LIMIT`
- `--no-pairing-window` to disable the tkinter window (headless/testing)

Example:
```powershell
python -m windows_agent --port 9000 --trusted-registry .\trusted_devices.json
```

## 7) Files created by the agent
- `trusted_devices.json` — trusted paired devices.
- `audit.log` — timestamped actions (`device_id` + action).

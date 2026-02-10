# Windows Agent

Remote Brain Builder Windows Agent.

## Run
```bash
python -m windows_agent
```

This starts:
- WebSocket control server on `--host/--port` (default `0.0.0.0:8765`)
- Static mobile web UI on `--web-ui-host/--web-ui-port` (default `0.0.0.0:8080`)

Disable web UI with:
```bash
python -m windows_agent --no-web-ui
```

Protocol is enforced from `shared/protocol/messages.json` version `1.0`, including pairing and trusted-device checks.

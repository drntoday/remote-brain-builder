from __future__ import annotations

import asyncio
import secrets
from pathlib import Path

from .config import parse_args
from .pairing_ui import PairingCodeWindow
from .server import WindowsAgentServer
from .web_ui_server import StaticUIHTTPServer, run_services


def main() -> None:
    config = parse_args()
    code = f"{secrets.randbelow(1_000_000):06d}"
    print(f"Pairing code: {code}")

    if config.show_pairing_window:
        try:
            PairingCodeWindow(code).start()
        except Exception as exc:  # pragma: no cover
            print(f"Unable to open pairing window: {exc}")

    server = WindowsAgentServer(config=config, pairing_code=code)
    if config.web_ui_enabled:
        ui_server = StaticUIHTTPServer(
            host=config.web_ui_host,
            port=config.web_ui_port,
            static_dir=Path(__file__).parent / "static",
        )
        asyncio.run(run_services(server.run, ui_server.run))
    else:
        asyncio.run(server.run())


if __name__ == "__main__":
    main()

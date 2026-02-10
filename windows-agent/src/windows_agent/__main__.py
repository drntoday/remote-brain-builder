from __future__ import annotations

import asyncio
import secrets

from .config import parse_args
from .pairing_ui import PairingCodeWindow
from .server import WindowsAgentServer


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
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

import asyncio
import json
from pathlib import Path

from windows_agent.config import AgentConfig
from windows_agent.server import WindowsAgentServer


class DummyWebSocket:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send(self, message: str) -> None:
        self.messages.append(message)


def test_unpaired_device_rejected_for_input(tmp_path: Path) -> None:
    cfg = AgentConfig(
        host="127.0.0.1",
        port=8765,
        trusted_registry_path=tmp_path / "trusted.json",
        audit_log_path=tmp_path / "audit.log",
        show_pairing_window=False,
    )
    server = WindowsAgentServer(config=cfg, pairing_code="123456")
    ws = DummyWebSocket()

    msg = {
        "protocol_version": "1.0",
        "type": "input.mouse_move",
        "id": "id-3",
        "ts": 1735689600000,
        "nonce": "nonce-7",
        "device_id": "unknown-device",
        "payload": {"dx": 2, "dy": 3},
    }

    asyncio.run(server._handle_action(ws, msg))

    result = json.loads(ws.messages[-1])
    assert result["payload"]["success"] is False
    assert result["payload"]["reason"] == "device_not_trusted"

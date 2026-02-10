import asyncio
import json
import logging
from pathlib import Path

from windows_agent.config import AgentConfig
from windows_agent.server import WindowsAgentServer


class DummyWebSocket:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send(self, message: str) -> None:
        self.messages.append(message)


class RaisingInputController:
    def mouse_move(self, *, dx: float, dy: float) -> None:
        raise AssertionError("input handler must not execute for untrusted devices")


def _server(tmp_path: Path) -> WindowsAgentServer:
    cfg = AgentConfig(
        host="127.0.0.1",
        port=8765,
        trusted_registry_path=tmp_path / "trusted.json",
        audit_log_path=tmp_path / "audit.log",
        show_pairing_window=False,
    )
    return WindowsAgentServer(config=cfg, pairing_code="123456")


def test_unpaired_device_rejected_for_input(tmp_path: Path, caplog) -> None:
    server = _server(tmp_path)
    server.input_controller = RaisingInputController()
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

    with caplog.at_level(logging.INFO, logger="windows_agent"):
        asyncio.run(server._handle_action(ws, msg))

    result = json.loads(ws.messages[-1])
    assert result["payload"]["success"] is False
    assert result["payload"]["reason"] == "device_not_trusted"
    assert "reject_untrusted_input device_id=unknown-device type=input.mouse_move" in caplog.text
    assert "action=rejected_untrusted:input.mouse_move" in caplog.text

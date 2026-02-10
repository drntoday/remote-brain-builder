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


BASE_MSG = {
    "protocol_version": "1.0",
    "id": "id-1",
    "ts": 1735689600000,
    "nonce": "nonce-1",
    "device_id": "android-1",
}


def _server(tmp_path: Path) -> WindowsAgentServer:
    cfg = AgentConfig(
        host="127.0.0.1",
        port=8765,
        trusted_registry_path=tmp_path / "trusted.json",
        audit_log_path=tmp_path / "audit.log",
        show_pairing_window=False,
    )
    return WindowsAgentServer(config=cfg, pairing_code="123456")


def test_pairing_success(tmp_path: Path) -> None:
    server = _server(tmp_path)
    ws = DummyWebSocket()

    req = BASE_MSG | {
        "type": "pair.request",
        "nonce": "nonce-2",
        "payload": {"device_name": "Phone", "public_key": "abc"},
    }
    confirm = BASE_MSG | {
        "type": "pair.confirm",
        "nonce": "nonce-3",
        "payload": {"code": "123456", "accepted": True},
    }

    asyncio.run(server._handle_pair_request(ws, req))
    asyncio.run(server._handle_pair_confirm(ws, confirm))

    result = json.loads(ws.messages[-1])
    assert result["type"] == "pair.result"
    assert result["payload"]["success"] is True
    assert server.registry.is_trusted("android-1")


def test_pairing_failure_wrong_code(tmp_path: Path) -> None:
    server = _server(tmp_path)
    ws = DummyWebSocket()

    confirm = BASE_MSG | {
        "type": "pair.confirm",
        "nonce": "nonce-4",
        "payload": {"code": "999999", "accepted": True},
    }

    asyncio.run(server._handle_pair_confirm(ws, confirm))

    result = json.loads(ws.messages[-1])
    assert result["payload"]["success"] is False
    assert result["payload"]["reason"] == "invalid_code_or_rejected"


def test_pairing_failure_wrong_code_does_not_trust_device(tmp_path: Path) -> None:
    server = _server(tmp_path)
    ws = DummyWebSocket()

    req = BASE_MSG | {
        "type": "pair.request",
        "nonce": "nonce-5",
        "payload": {"device_name": "Phone", "public_key": "abc"},
    }
    confirm = BASE_MSG | {
        "type": "pair.confirm",
        "nonce": "nonce-6",
        "payload": {"code": "111111", "accepted": True},
    }

    asyncio.run(server._handle_pair_request(ws, req))
    asyncio.run(server._handle_pair_confirm(ws, confirm))

    assert server.registry.is_trusted("android-1") is False


def test_pair_confirm_without_request_fails_and_does_not_trust(tmp_path: Path) -> None:
    server = _server(tmp_path)
    ws = DummyWebSocket()

    confirm = BASE_MSG | {
        "type": "pair.confirm",
        "nonce": "nonce-7",
        "payload": {"code": "123456", "accepted": True},
    }

    asyncio.run(server._handle_pair_confirm(ws, confirm))

    result = json.loads(ws.messages[-1])
    assert result["payload"]["success"] is False
    assert result["payload"]["reason"] == "invalid_pair_request"
    assert server.registry.is_trusted("android-1") is False
